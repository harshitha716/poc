from pydantic import BaseModel


class RegexPatternsInput(BaseModel):
    grouped_values_str: str


class RegexPatternsOutput(BaseModel):
    regex_credit: str
    regex_debit: str
