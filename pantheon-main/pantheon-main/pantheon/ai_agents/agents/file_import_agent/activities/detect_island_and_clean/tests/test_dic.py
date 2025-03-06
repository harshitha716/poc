import pytest
import pandas as pd
from pantheon.ai_agents.agents.file_import_agent.activities.detect_island_and_clean.dic import (
    detect_island_and_clean,
)
from pantheon.ai_agents.agents.file_import_agent.activities.detect_island_and_clean.schema.dic_schema import (
    DetectIslandAndCleanInput,
    DetectIslandAndCleanOutput,
)


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {
            0: [
                "Date",
                "14 Nov '23",
                "14 Nov '23",
                "13 Nov '23",
                "13 Nov '23",
                "13 Nov '23",
                "12 Nov '23",
                "12 Nov '23",
            ],
            1: [
                "Transaction Details",
                "NEERU ENTERPRISES GURGAON IN",
                "PAYTM Noida IN",
                "SMARTSHIFT LOGISTIC Bengaluru IN",
                "UBER INDIA SYSTE PVT LTD NOIDA IN",
                "12356ND07 000000017900 WsVG9VuCrv1",
                "UBER INDIA SYSTE PVT LTD NOIDA IN",
                "SWIGGY INSTAMART BANGALORE IN",
            ],
            2: [
                "Debit/Credit",
                "Debit",
                "Credit",
                "Debit",
                "Debit",
                "Debit",
                "Debit",
                "Debit",
            ],
            4: [
                "Amount (INR)",
                "₹ 898.00",
                "₹ 1020.00",
                "₹ 100.00",
                "₹ 106.23",
                "₹ 179.00",
                "₹ 41.93",
                "₹ 795.00",
            ],
        }
    )


def test_detect_island_and_clean(sample_dataframe):
    input_data = DetectIslandAndCleanInput(df=sample_dataframe, start_row=0)
    result = detect_island_and_clean(input_data)

    assert isinstance(result, DetectIslandAndCleanOutput)
    assert result.region == "A1:E8"
    assert result.island_df.shape == (8, 4)


def test_detect_island_and_clean_with_start_row(sample_dataframe):
    input_data = DetectIslandAndCleanInput(df=sample_dataframe, start_row=2)
    result = detect_island_and_clean(input_data)

    assert isinstance(result, DetectIslandAndCleanOutput)
    assert result.region == "A2:E8"
    assert result.island_df.shape == (7, 4)
