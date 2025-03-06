import pytest
import pandas as pd
from io import BytesIO
from ..helper import (
    html_table_to_dataframe,
    flexible_csv_parser,
    attempt_fix_malformed_csv,
    process_excel_file,
    process_parquet_file,
    FileBytes,
)


@pytest.fixture
def sample_html_table():
    html = """
    <html>
    <body>
    <table>
        <tr><th>Name</th><th>Age</th></tr>
        <tr><td>John</td><td>30</td></tr>
        <tr><td>Jane</td><td>25</td></tr>
    </table>
    </body>
    </html>
    """
    return BytesIO(html.encode("utf-8"))


@pytest.fixture
def sample_csv():
    csv_data = "Name,Age\nJohn,30\nJane,25"
    return BytesIO(csv_data.encode("utf-8"))


@pytest.fixture
def malformed_csv():
    data = "Name\tAge\nJohn\t30\nJane\t25"
    return BytesIO(data.encode("utf-8"))


class TestHTMLTableToDataframe:
    def test_valid_html_table(self, sample_html_table):
        result = html_table_to_dataframe(FileBytes(file_bytes=sample_html_table))
        assert isinstance(result.df, pd.DataFrame)
        assert result.df.shape == (3, 2)
        assert result.df.iloc[1, 0] == "John"
        assert result.df.iloc[1, 1] == "30"

    def test_invalid_html(self):
        invalid_html = BytesIO(b"<html><body>No table here</body></html>")
        with pytest.raises(ValueError, match="No table found in the HTML file"):
            html_table_to_dataframe(FileBytes(file_bytes=invalid_html))


class TestFlexibleCSVParser:
    def test_valid_csv(self, sample_csv):
        result = flexible_csv_parser(FileBytes(file_bytes=sample_csv))
        assert isinstance(result.df, pd.DataFrame)
        assert result.df.shape == (3, 2)
        assert result.df.iloc[1, 0] == "John"
        assert result.df.iloc[1, 1] == "30"

    def test_uneven_columns(self):
        uneven_csv = BytesIO(b"a,b,c\n1,2\n3,4,5,6")
        result = flexible_csv_parser(FileBytes(file_bytes=uneven_csv))
        assert result.df.shape == (3, 4)  # Padded with None values
        assert pd.isna(result.df.iloc[1, 2])  # Third column should be None

    def test_empty_csv(self):
        empty_csv = BytesIO(b"")
        with pytest.raises(Exception):
            flexible_csv_parser(FileBytes(file_bytes=empty_csv))

    def test_trailing_empty_strings(self):
        csv_with_trailing = BytesIO(b"a,b,c,,\n1,2,3,,\n4,5,6,,")
        result = flexible_csv_parser(FileBytes(file_bytes=csv_with_trailing))
        assert result.df.shape == (3, 3)  # Should remove trailing empty strings
        assert list(result.df.iloc[0]) == ["a", "b", "c"]


class TestAttemptFixMalformedCSV:
    def test_tab_separated_values(self, malformed_csv):
        result = attempt_fix_malformed_csv(malformed_csv)
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (3, 2)
        assert result.iloc[1, 0] == "John"
        assert result.iloc[1, 1] == "30"


class TestProcessExcelFile:
    def test_xlsx_file(self):
        # Create a simple Excel-like BytesIO object
        excel_data = BytesIO()
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        with pd.ExcelWriter(excel_data, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        excel_data.seek(0)

        result = process_excel_file(excel_data, "test.xlsx")
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_xls_file(self, monkeypatch):
        # Mock the pd.ExcelFile to simulate .xls file handling
        class MockExcelFile:
            def __init__(self, *args, **kwargs):
                pass

            @property
            def sheet_names(self):
                return ["Sheet1"]

        def mock_read_excel(*args, **kwargs):
            return pd.DataFrame({"A": [1, 2], "B": [3, 4]})

        # Apply the mocks
        monkeypatch.setattr(pd, "ExcelFile", MockExcelFile)
        monkeypatch.setattr(pd, "read_excel", mock_read_excel)

        # Test with a dummy BytesIO
        excel_data = BytesIO(b"dummy xls content")
        result = process_excel_file(excel_data, "test.xls")

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_fallback_to_html(self):
        html_data = BytesIO(b"<html><table><tr><td>1</td></tr></table></html>")
        result = process_excel_file(html_data, "test.xlsx")
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_fallback_to_csv(self):
        csv_data = BytesIO(b"col1,col2,col3,col4\n1,2,3,4\n5,6,7,8")
        result = process_excel_file(csv_data, "test.xlsx")
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (3, 4)

    def test_fallback_to_csv_with_many_commas(self):
        # Create a CSV with more than 3 commas per line to trigger the CSV detection
        csv_data = BytesIO(b"a,b,c,d,e\n1,2,3,4,5\n6,7,8,9,10")
        result = process_excel_file(csv_data, "test.xlsx")
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (3, 5)  # Should have 3 rows and 5 columns
        assert list(result.iloc[0]) == ["a", "b", "c", "d", "e"]

    def test_unsupported_extension(self):
        with pytest.raises(ValueError, match="Unsupported Excel file extension"):
            process_excel_file(BytesIO(), "test.doc")


class TestProcessParquetFile:
    def test_valid_parquet(self):
        # Create a sample parquet file
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        parquet_data = BytesIO()
        df.to_parquet(parquet_data)
        parquet_data.seek(0)

        result = process_parquet_file(parquet_data)
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)
        assert list(result.columns) == ["A", "B"]

    def test_invalid_parquet(self):
        invalid_data = BytesIO(b"not a parquet file")
        with pytest.raises(ValueError):
            process_parquet_file(invalid_data)
