from pantheon.ai_agents.llm_calls.fileimport_agent.fileimport_agent import (
    FindMandatoryField,
)
from pantheon.ai_agents.agents.file_import_agent.workflows.workflow import (
    FileImportAgent,
)
from typing import Optional, Dict, Any
import structlog
import pandas as pd
from pantheon.routers.fileimport.schemas.fileimport import CSVData

logger = structlog.get_logger(__name__)


class FileImportController:
    def __init__(self):
        self.find_mandatory_field = FindMandatoryField()
        self.file_import_agent = FileImportAgent()

    async def find_mandatory_field_controller(self, row_values: str) -> Optional[Dict]:
        try:
            result = await self.find_mandatory_field.analyze_csv_row(row_values)
            logger.info("FIND_MANDATORY_FIELD_RESPONSE", result=result)
            return result
        except Exception as e:
            logger.exception(
                "FILE_IMPORT_CONTROLLER_ERROR",
                row_values=row_values,
                exception=str(e),
            )
            return None

    async def generate_config(
        self, csv_data: CSVData, start_row: int, template_config: Optional[Any] = None
    ) -> Optional[Dict]:
        try:
            df = pd.DataFrame(
                csv_data.data, columns=csv_data.columns, index=csv_data.index
            )

            (
                transformation_config,
                unmapped_columns,
                errors,
                opening_balance,
            ) = await self.file_import_agent.create_transformation_config(
                df, start_row, template_config
            )

            logger.info(
                "FILE_IMPORT_AGENT_RESPONSE",
                transformation_config=transformation_config,
                unmapped_columns=unmapped_columns,
                errors=errors,
                opening_balance=opening_balance,
            )

            return {
                "transformation_config": transformation_config,
                "unmapped_columns": unmapped_columns,
                "errors": errors,
                "opening_balance": opening_balance,
            }
        except Exception as e:
            logger.exception(
                "FILE_IMPORT_CONTROLLER_ERROR",
                exception=str(e),
            )
            return None
