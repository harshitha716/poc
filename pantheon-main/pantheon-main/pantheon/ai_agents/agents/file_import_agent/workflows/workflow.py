import pandas as pd
from typing import Dict, Any, List, Tuple
import logging

# Importing necessary agents and tools
from pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.cm import (
    column_mapping_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.clean_credit_debit.ccd import (
    clean_credit_debit_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.clean_credit_debit.schema.ccd_schema import (
    CleanCreditDebitInput,
    CleanCreditDebitResult,
    RegexConfig,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.fma import (
    find_missing_attributes_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.schema.fma_schema import (
    FindMissingAttributesInput,
)
from pantheon.ai_agents.agents.file_import_agent.activities.detect_island_and_clean.dic import (
    detect_island_and_clean,
)
from pantheon.ai_agents.agents.file_import_agent.activities.detect_island_and_clean.schema.dic_schema import (
    DetectIslandAndCleanInput,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_header_and_columns.fhc import (
    find_header_and_columns,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_header_and_columns.schema.fhc_schema import (
    FindHeaderAndColumnsInput,
)
from pantheon.ai_agents.tools.generate_transform_config.tool import (
    generate_transformation_config,
)
from .helpers.llm_cache import (
    destruct,
    combine_column_info_and_mappings,
    split_excel_ref,
    update_region,
)

# Importing constants
from .constants.constants import (
    ATTRIBUTES_TO_REMOVE,
)

logger = logging.getLogger(__name__)


# Usage in the FileImportAgent class:
class FileImportAgent:
    def __init__(self):
        # Initialize instance variables
        self.original_df = None
        self.island_df = None
        self.region = ""
        self.start_row = 0
        self.column_info = []
        self.mapped_columns = []
        self.unmapped_attributes = []
        self.errors = []
        self.mapped_attributes = []
        self.opening_balance = None

    async def create_transformation_config(
        self, df: pd.DataFrame, start_row: int, template_config: Any
    ) -> Tuple[Dict[str, Any], List[str], List[str], Dict[str, Any]]:
        # Destruct the template_config and save the variables
        (
            credit_debit_template,
            column_mappings_template,
            unmapped_columns_template,
            config_errors_template,
        ) = destruct(template_config)

        # Set the original dataframe and start row
        self.original_df = df
        self.start_row = start_row

        # Detect region and clean the dataframe
        input_data = DetectIslandAndCleanInput(
            df=self.original_df, start_row=self.start_row
        )
        result = detect_island_and_clean(input_data)
        self.region, self.island_df = result.region, result.island_df

        # Find header and columns in the cleaned dataframe
        fhc_input = FindHeaderAndColumnsInput(
            island_df=self.island_df, region=self.region, start_row=self.start_row
        )
        fhc_output = find_header_and_columns(fhc_input)

        # Remove or comment out these lines if they're not used later in the code
        # idx = fhc_output.header_row_index
        # header_columns = fhc_output.header_columns

        self.region = fhc_output.new_region
        self.start_row = fhc_output.new_start_row
        self.column_info = fhc_output.column_info
        self.island_df = fhc_output.updated_df

        # Get column mappings
        if column_mappings_template:
            self.mapped_columns = combine_column_info_and_mappings(
                self.column_info, column_mappings_template
            )
            self.unmapped_attributes = unmapped_columns_template
            self.errors = config_errors_template
        else:
            result = await column_mapping_activity(
                self.island_df, self.column_info, self.original_df
            )
            self.mapped_columns = result.mapped_columns
            self.unmapped_attributes = result.unmapped_attributes
            self.errors = result.errors

        # Handle credit and debit columns
        if credit_debit_template:
            start, end = self.region.split(":")
            _, start_row = split_excel_ref(start)
            _, end_row = split_excel_ref(end)
            # Update amount_column_region
            if credit_debit_template.amount_column_region:
                credit_debit_template.amount_column_region = update_region(
                    credit_debit_template.amount_column_region, start_row, end_row
                )

            # Update type_region if it exists
            if credit_debit_template.type_region:
                credit_debit_template.type_region = update_region(
                    credit_debit_template.type_region, start_row, end_row
                )

            clean_credit_debit_result = CleanCreditDebitResult(
                cb=RegexConfig(
                    amount_column_region=credit_debit_template.amount_column_region,
                    type_region=credit_debit_template.type_region,
                    regex_credit=credit_debit_template.regex_credit,
                    regex_debit=credit_debit_template.regex_debit,
                ),
                unmapped_attributes=self.unmapped_attributes,
            )
        else:
            clean_credit_debit_result = await clean_credit_debit_activity(
                CleanCreditDebitInput(
                    df=self.original_df,
                    column_mapping=self.mapped_columns,
                    unmapped_attributes=self.unmapped_attributes,
                )
            )

        cb = clean_credit_debit_result.cb
        self.unmapped_attributes = clean_credit_debit_result.unmapped_attributes

        self.mapped_attributes = []

        still_unmapped = []
        if len(self.unmapped_attributes) > 0:
            # Remove specific attributes from unmapped attributes
            still_unmapped = [
                attr
                for attr in self.unmapped_attributes
                if attr in ATTRIBUTES_TO_REMOVE
            ]

            self.unmapped_attributes = [
                attr
                for attr in self.unmapped_attributes
                if attr not in ATTRIBUTES_TO_REMOVE
            ]

            if self.unmapped_attributes:
                # Detect missing attributes
                fma_input = FindMissingAttributesInput(
                    original_df=self.original_df,
                    region=self.region,
                    unmapped_attributes=self.unmapped_attributes,
                )
                fma_output = await find_missing_attributes_activity(fma_input)

                self.mapped_attributes = fma_output.mapped_attributes
                search_still_unmapped = fma_output.search_still_unmapped
                self.opening_balance = fma_output.opening_balance

                still_unmapped.extend(search_still_unmapped)

        # Generate transformation configuration
        transformation_config = generate_transformation_config(
            self.mapped_attributes, self.mapped_columns, cb
        )

        # Return the transformation configuration, still unmapped attributes, errors, and opening balance
        return transformation_config, still_unmapped, self.errors, self.opening_balance
