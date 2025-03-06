import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO, StringIO
import csv
from .models import FileBytes, DataFrameModel
import polars as pl


def html_table_to_dataframe(file_bytes: FileBytes) -> DataFrameModel:
    # Parse the HTML content
    html_content = file_bytes.file_bytes.getvalue().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html_content, "html.parser")

    # Find the table
    table = soup.find("table")

    if not table:
        raise ValueError("No table found in the HTML file.")

    # Prepare CSV data
    csv_data = []

    # Process rows
    for row in table.find_all("tr"):
        csv_row = []
        # Process cells (both th and td)
        for cell in row.find_all(["th", "td"]):
            # Get the text content of the cell, strip whitespace
            cell_content = cell.get_text(strip=True)
            csv_row.append(cell_content)
        csv_data.append(csv_row)

    df = pd.DataFrame(csv_data)

    return DataFrameModel(df=df)


def flexible_csv_parser(file_bytes: FileBytes) -> DataFrameModel:
    # Function to process each row
    def process_row(row):
        # Remove empty strings from the end of the row
        while row and row[-1] == "":
            row.pop()
        return row

    try:
        # Read the content from BytesIO
        content = file_bytes.file_bytes.getvalue().decode("utf-8")
        reader = csv.reader(StringIO(content))

        # Process rows and find the maximum number of columns
        rows = [process_row(row) for row in reader if row]
        max_cols = max(len(row) for row in rows)

        # Pad shorter rows with empty strings
        padded_rows = [row + [None] * (max_cols - len(row)) for row in rows]

        # Create DataFrame with header=None
        df = pd.DataFrame(padded_rows)

        return DataFrameModel(df=df)

    except Exception:
        raise


def attempt_fix_malformed_csv(file_bytes: BytesIO) -> pd.DataFrame:
    """
    Attempts to fix and parse malformed CSV-like data by converting tab-separated values to CSV.

    Args:
        file_bytes (io.BytesIO): The file content as bytes

    Returns:
        pd.DataFrame: The processed DataFrame

    Raises:
        ValueError: If unable to process the file
    """
    try:
        file_bytes.seek(0)  # Reset file pointer to the beginning
        content = file_bytes.getvalue().decode("utf-8", errors="ignore")

        # Split into lines and replace tabs with commas
        processed_lines = []
        for line in content.split("\n"):
            # Remove carriage returns but keep the line even if empty
            line = line.replace("\r", "")

            # Convert tabs to commas, preserving empty fields
            fields = line.split("\t")
            processed_line = ",".join(field.strip() for field in fields)
            processed_lines.append(processed_line)

        # Create new BytesIO with processed content
        processed_content = "\n".join(processed_lines)
        processed_bytes = BytesIO(processed_content.encode("utf-8"))
        df_model = flexible_csv_parser(FileBytes(file_bytes=processed_bytes))
        return df_model.df
    except Exception as e:
        raise ValueError(f"Failed to process malformed CSV: {str(e)}")


def process_excel_file(file_bytes: BytesIO, file_extension: str) -> pd.DataFrame:
    """
    Process Excel files (XLS or XLSX) and return a DataFrame.
    If multiple sheets are present, they are vertically stacked.

    Args:
        file_bytes (io.BytesIO): The file content as bytes.
        file_extension (str): The file extension ('.xls' or '.xlsx').

    Returns:
        pd.DataFrame: The processed DataFrame.
    """
    try:
        if file_extension.endswith("xlsx"):
            excel_file = pd.ExcelFile(file_bytes, engine="openpyxl")
        elif file_extension.endswith("xls"):
            excel_file = pd.ExcelFile(file_bytes, engine="xlrd")
        else:
            raise ValueError(f"Unsupported Excel file extension: {file_extension}")

        # Read all sheets and concatenate them vertically
        dfs = []
        for sheet_name in excel_file.sheet_names:
            sheet_df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            dfs.append(sheet_df)

        df = pd.concat(dfs, axis=0, ignore_index=True)
        return df

    except Exception as excel_error:
        # If Excel reading fails, check for HTML
        file_bytes.seek(0)  # Reset file pointer to the beginning
        first_line = (
            file_bytes.getvalue()
            .decode("utf-8", errors="ignore")
            .split("\n")[0]
            .strip()
        )

        if first_line.startswith("<html"):
            df_model = html_table_to_dataframe(FileBytes(file_bytes=file_bytes))
            return df_model.df

        # If not HTML, check for CSV
        file_bytes.seek(0)  # Reset file pointer to the beginning
        file_start = file_bytes.getvalue().decode("utf-8", errors="ignore")[:1000]
        first_lines = file_start.split("\n")[:5]

        if any(line.count(",") > 3 for line in first_lines):
            file_bytes.seek(0)  # Reset file pointer to the beginning
            df_model = flexible_csv_parser(FileBytes(file_bytes=file_bytes))
            return df_model.df

        # If all checks fail, try to fix malformed CSV
        try:
            return attempt_fix_malformed_csv(file_bytes)
        except Exception:
            # If all checks fail, raise the original Excel error
            raise ValueError(f"Unable to process file. Excel error: {excel_error}")


def process_parquet_file(file_bytes: BytesIO) -> pd.DataFrame:
    """
    Process a Parquet file and return a DataFrame.
    First scans the parquet file using Polars LazyFrame to avoid memory consumption,
    fetches the first 10 rows, then converts to a Pandas DataFrame.

    Args:
        file_bytes (io.BytesIO): The file content as bytes.

    Returns:
        pd.DataFrame: The processed DataFrame (first 10 rows).

    Raises:
        ValueError: If unable to process the parquet file.
    """
    try:
        # Use scan_parquet which returns a LazyFrame for better memory efficiency
        lazy_df = pl.scan_parquet(file_bytes)

        # Limit to first 10 rows and collect results
        pl_df = lazy_df.limit(10).collect()

        # Convert Polars DataFrame to Pandas DataFrame
        df = pl_df.to_pandas()

        return df
    except Exception as e:
        raise ValueError(f"Unable to process parquet file: {str(e)}")
