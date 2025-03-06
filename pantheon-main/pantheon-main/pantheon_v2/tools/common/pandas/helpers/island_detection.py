import pandas as pd
import re


def _merge_wrapped_rows(df):
    """
    Attempt to merge pairs of rows that appear to be one logical row split across
    two lines (e.g. 'Balance' on one line, numeric cells on the next).
    We only merge rows if they complement each other (no conflicts) and merging
    significantly increases the fill of the row.

    :param df: Original DataFrame (all strings).
    :param max_merge_distance: How many rows ahead to look for a merge (usually 1).
    :return: A new DataFrame with merged rows where needed.
    """
    num_rows, num_cols = df.shape
    merged_data = []
    skip_next = False

    for i in range(num_rows):
        if skip_next:
            skip_next = False
            continue

        current_row = df.iloc[i].tolist()
        # Look ahead up to max_merge_distance (usually just the next row)
        if i < num_rows - 1:
            next_row = df.iloc[i + 1].tolist()

            fill_before = sum(bool(v.strip()) for v in current_row)
            fill_after = sum(bool(v.strip()) for v in next_row)

            merged_candidate = current_row[:]
            conflict = False

            for col_idx in range(num_cols):
                v1 = current_row[col_idx].strip()
                v2 = next_row[col_idx].strip()
                if v1 and v2 and v1 != v2:
                    # Conflict: both have content, but differ
                    conflict = True
                    break
                if not v1 and v2:
                    merged_candidate[col_idx] = next_row[col_idx]

            if not conflict:
                combined_fill = sum(bool(v.strip()) for v in merged_candidate)
                # Heuristic: if combined_fill is significantly larger than either row alone,
                # and close to fill_before+fill_after, we consider them "wrapped" parts of 1 row.
                if (
                    combined_fill >= 0.8 * (fill_before + fill_after)
                    and combined_fill > fill_before
                    and combined_fill > fill_after
                ):
                    merged_data.append(merged_candidate)
                    skip_next = True
                    continue

        merged_data.append(current_row)

    return pd.DataFrame(merged_data, columns=df.columns)


def detect_tables_and_metadata(
    df_original: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """
    1) Read CSV (no header, all as strings), fill empty cells with ''.
    2) Merge 'wrapped' rows if they look like one logical line.
    3) Detect table 'islands' by scanning for header rows and collecting
       contiguous rows below.
    4) For each detected table, also capture the 'metadata' rows immediately
       above it (optional).
    5) Return a tuple of (df, metadata_df) where metadata_df can be None if no metadata found.

    Raises:
        ValueError: If no valid table structure is found in the input DataFrame.
    """
    # Reset index and drop it to ensure it's not treated as data
    df_original = df_original.reset_index(drop=True)
    df_original = df_original.fillna("")

    # Step 2: merge possible row splits
    df_merged = _merge_wrapped_rows(df_original)
    df = df_merged.reset_index(drop=True)
    num_rows, num_cols = df.shape

    def longest_consecutive_non_empty(row_values):
        max_consecutive = 0
        current_count = 0
        for val in row_values:
            if val.strip():
                current_count += 1
                max_consecutive = max(max_consecutive, current_count)
            else:
                current_count = 0
        return max_consecutive

    # Identify row(s) with the longest consecutive block -> potential headers
    max_span = 0
    header_row_candidates = []
    for row_idx in range(num_rows):
        row_values = df.iloc[row_idx].tolist()
        span = longest_consecutive_non_empty(row_values)
        if span > max_span:
            max_span = span
            header_row_candidates = [row_idx]
        elif span == max_span and span > 0:
            header_row_candidates.append(row_idx)

    if max_span == 0:
        # No real header found, treat entire df as one table, with empty metadata
        return df, None

    # Collect tables
    used_rows = set()
    table_ranges = []  # will store tuples of (header_row, all_rows_set, sub_df)

    for header_row in header_row_candidates:
        if header_row in used_rows:
            continue

        # Find longest consecutive non-empty region in the header row
        row_values = df.iloc[header_row].tolist()
        longest_seq_start, longest_seq_end = None, None
        best_run_length = 0
        current_start = None

        for col_idx, val in enumerate(row_values):
            if val.strip():
                if current_start is None:
                    current_start = col_idx
            else:
                if current_start is not None:
                    run_length = col_idx - current_start
                    if run_length > best_run_length:
                        best_run_length = run_length
                        longest_seq_start = current_start
                        longest_seq_end = col_idx
                    current_start = None

        if current_start is not None:
            run_length = num_cols - current_start
            if run_length > best_run_length:
                best_run_length = run_length
                longest_seq_start = current_start
                longest_seq_end = num_cols

        if longest_seq_start is None:
            continue

        table_rows = [header_row]
        used_rows.add(header_row)

        # 3) gather contiguous table rows
        consecutive_empty = 0
        for r in range(header_row + 1, num_rows):
            if r in used_rows:
                continue
            row_slice = df.iloc[r, longest_seq_start:longest_seq_end]
            filled = sum(1 for x in row_slice if x.strip())
            slice_width = longest_seq_end - longest_seq_start
            ratio = filled / slice_width if slice_width else 0

            if ratio < 0.2:
                consecutive_empty += 1
            else:
                consecutive_empty = 0
                table_rows.append(r)
                used_rows.add(r)

            if consecutive_empty >= 3:
                break

        min_row = min(table_rows)
        max_row = max(table_rows)
        sub_df = (
            df.iloc[table_rows, longest_seq_start:longest_seq_end]
            .copy()
            .reset_index(drop=True)
        )
        table_ranges.append((min_row, max_row, sub_df))

    # Sort tables by their starting row
    table_ranges.sort(key=lambda x: x[0])

    # 4) For each table, find the metadata above it
    results = []
    prev_end = -1  # last row used by the previous table
    for i, (min_row, max_row, table_df) in enumerate(table_ranges):
        # metadata is from (prev_end+1) to (min_row-1), inclusive, if that range is valid
        meta_start = prev_end + 1
        meta_end = min_row - 1
        if meta_end > meta_start:  # Changed from >= to > to exclude single-row case
            metadata_df = (
                df.iloc[meta_start : meta_end + 1, :].copy().reset_index(drop=True)
            )
        else:
            metadata_df = None
        prev_end = max_row

        # find the true header
        header_row, cleaned_df = find_true_header(table_df)

        results.append({"metadata_df": metadata_df, "table_df": cleaned_df})

    # merge all the tables and metadata
    merged_df = merge_tables([item["table_df"] for item in results])

    # Only merge metadata if there is any
    metadata_dfs = [
        item["metadata_df"] for item in results if item["metadata_df"] is not None
    ]
    merged_metadata = merge_metadata(metadata_dfs) if metadata_dfs else None

    if merged_df.empty:
        raise ValueError("No valid table structure found in the input DataFrame")

    return merged_df, merged_metadata


def transform_float(text):
    try:
        text = str(text)
        # Check for multiple numbers separated by spaces
        if (
            len(
                [
                    x
                    for x in text.split()
                    if x.strip().replace(".", "").replace("-", "").isdigit()
                ]
            )
            > 1
        ):
            return ""

        # Remove all characters except digits, decimal points, and minus signs
        cleaned_text = "".join(char for char in text if char.isdigit() or char in ".-")

        # Pattern to match float number (handles negative numbers too)
        pattern = r"-?\d+(?:\.\d+)?"

        matches = list(re.finditer(pattern, cleaned_text))

        if not matches or len(matches) > 1:
            return ""

        return abs(float(matches[0].group()))
    except Exception as e:
        print(f"Error transforming float from '{text}': {str(e)}")
        return ""


def find_true_header(df: pd.DataFrame) -> tuple[int | None, pd.DataFrame]:
    """
    Find the true header row and remove any rows above it. Returns the header index
    and cleaned DataFrame with rows above header removed.

    The function identifies a header by:
    1. Scanning each row sequentially
    2. Looking for the first row that's followed by a row containing numeric values
    3. The header is the last non-numeric row before numeric data begins

    Args:
        df: DataFrame where all values are strings

    Returns:
        tuple[int | None, pd.DataFrame]:
            - Index of the header row if found, None otherwise
            - Cleaned DataFrame with rows above header removed, or original DataFrame if no header

    Raises:
        ValueError: If the input DataFrame is empty
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")

    def has_numeric(row) -> bool:
        """Check if row contains any numeric values."""
        return any(transform_float(val) != "" for val in row if val.strip())

    num_rows = len(df)
    for idx in range(num_rows - 1):  # Stop one row before the end
        current_row = df.iloc[idx]
        next_row = df.iloc[idx + 1]

        # Skip completely empty rows
        if not current_row.str.strip().str.len().sum():
            continue

        # If current row has no numbers and next row has numbers,
        # current row is likely the header
        if not has_numeric(current_row) and has_numeric(next_row):
            cleaned_df = df.iloc[idx:].reset_index(drop=True)
            return idx, cleaned_df

    return None, df


def merge_tables(tables: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple DataFrames based on matching headers.

    Args:
        tables: List of pandas DataFrames to merge

    Returns:
        pd.DataFrame: Merged DataFrame containing all matching tables.
        If no tables match, returns the first table.
        If only one table is provided, returns that table.
    """
    if not tables:
        return pd.DataFrame()

    if len(tables) == 1:
        return tables[0]

    # Group DataFrames by their column names (converted to tuple for hashability)
    header_groups = {}
    for df in tables:
        cols = tuple(df.columns)
        if cols in header_groups:
            header_groups[cols].append(df)
        else:
            header_groups[cols] = [df]

    # Find the group with the most matching tables
    largest_group = max(header_groups.values(), key=len)

    # If we found matching tables, merge them
    if len(largest_group) > 1:
        # Keep the first DataFrame as is
        merged_df = largest_group[0]
        # For subsequent DataFrames, skip their first row (header)
        for df in largest_group[1:]:
            merged_df = pd.concat([merged_df, df.iloc[1:]], ignore_index=True)
        return merged_df

    # If no matches found, return the first table
    return tables[0]


def merge_metadata(metadata: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple metadata DataFrames into one, removing exact duplicates.
    Maintains the original structure and only removes rows that are completely identical.

    Args:
        metadata: List of metadata DataFrames to merge

    Returns:
        pd.DataFrame: Single merged DataFrame with duplicates removed
    """
    if not metadata:
        return pd.DataFrame()

    if len(metadata) == 1:
        return metadata[0]

    # Merge all DataFrames vertically
    merged_df = pd.concat(metadata, ignore_index=True)

    # Convert empty strings and NaN to a special placeholder
    # This ensures we don't treat empty cells as different when they're effectively the same
    merged_df = merged_df.fillna("")

    # Remove exact duplicates while preserving order
    # keep='first' retains the first occurrence of any duplicate row
    deduped_df = merged_df.drop_duplicates(keep="first")

    # Reset the index to ensure continuous numbering
    return deduped_df.reset_index(drop=True)
