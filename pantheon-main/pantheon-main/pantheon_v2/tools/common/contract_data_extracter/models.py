from typing import Optional, Type
from pydantic import BaseModel
from pantheon_v2.core.common.generic_base_model import GenericBaseModel


class ContractDataExtracterInput(BaseModel):
    """Input model for contract data extraction."""

    document_content: str
    output_model: Type[BaseModel]
    additional_prompt: Optional[str] = None


class ContractDataExtracterOutput[T: BaseModel](GenericBaseModel):
    """Output model for contract data extraction."""

    extracted_data: T
