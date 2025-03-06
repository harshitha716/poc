from pydantic import BaseModel


class HermFormulaAgentResponse(BaseModel):
    formula: str
    explanation: str
