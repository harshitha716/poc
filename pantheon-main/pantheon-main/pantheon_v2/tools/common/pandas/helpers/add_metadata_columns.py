import pandas as pd
from typing import Dict, Any, List, Union


def process_metadata_value(value: Any) -> Union[List[str], str]:
    """Process a metadata value to handle both array and non-array values."""
    if isinstance(value, list):
        return value
    return value


def create_metadata_columns(metadata: Dict[str, Any], df_length: int) -> pd.DataFrame:
    """Create a DataFrame with metadata columns."""
    processed_data = {}

    for key, value in metadata.items():
        if isinstance(value, list):
            # For array values, create as many columns as there are elements
            for i, val in enumerate(value, 1):
                processed_data[f"{key}_{i}"] = [val] * df_length
        else:
            # For non-array values, create single column
            processed_data[key] = [value] * df_length

    # Create DataFrame
    metadata_df = pd.DataFrame(processed_data)

    # Add a header row with column names
    header_row = pd.DataFrame(
        [metadata_df.columns.tolist()], columns=metadata_df.columns
    )
    metadata_df = pd.concat([header_row, metadata_df], ignore_index=True)

    # Convert column names to numeric sequence
    metadata_df.columns = range(len(metadata_df.columns))

    return metadata_df


def add_metadata_to_df(df: pd.DataFrame, metadata: Dict[str, Any]) -> pd.DataFrame:
    """Add metadata as new columns to existing DataFrame."""
    # Create metadata DataFrame
    metadata_df = create_metadata_columns(metadata, len(df))

    # Normalize source DataFrame if it has numeric headers
    if all(
        isinstance(h, (int, float)) or (isinstance(h, str) and h.isdigit())
        for h in df.columns
    ):
        source_headers = df.iloc[0].tolist()
        df.columns = source_headers
        df = df.iloc[1:].reset_index(drop=True)

    # Get the actual column names from metadata_df's first row
    metadata_headers = metadata_df.iloc[0].tolist()
    metadata_df.columns = metadata_headers
    metadata_df = metadata_df.iloc[1:].reset_index(drop=True)

    # Concatenate DataFrames
    result_df = pd.concat([df, metadata_df], axis=1)

    return result_df
