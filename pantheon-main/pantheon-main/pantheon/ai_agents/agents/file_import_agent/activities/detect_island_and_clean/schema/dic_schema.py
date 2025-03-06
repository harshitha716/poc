from pydantic import BaseModel
import pandas as pd


class DetectIslandAndCleanInput(BaseModel):
    df: pd.DataFrame
    start_row: int

    class Config:
        arbitrary_types_allowed = True


class DetectIslandAndCleanOutput(BaseModel):
    region: str
    island_df: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True
