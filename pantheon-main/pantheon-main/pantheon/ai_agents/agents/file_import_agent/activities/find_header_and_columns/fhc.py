from pantheon.ai_agents.tools.find_headers_and_columns.tool import (
    find_header_row_and_columns,
)
from .schema.fhc_schema import (
    FindHeaderAndColumnsInput,
    FindHeaderAndColumnsOutput,
    ColumnInfo,
)


def find_header_and_columns(
    input_data: FindHeaderAndColumnsInput,
) -> FindHeaderAndColumnsOutput:
    # Call the underlying function
    result = find_header_row_and_columns(
        input_data.island_df, 10, input_data.region, input_data.start_row
    )

    # Unpack the result
    (
        header_row_index,
        header_columns,
        new_region,
        new_start_row,
        column_info,
        updated_df,
    ) = result

    # Create the output object
    output = FindHeaderAndColumnsOutput(
        header_row_index=header_row_index,
        header_columns=header_columns,
        new_region=new_region,
        new_start_row=new_start_row,
        column_info=[ColumnInfo(**col) for col in column_info],
        updated_df=updated_df,
    )

    return output
