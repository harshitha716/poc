import pytest
from pantheon_v2.processes.customers.netflix.workflows.contract_extraction import (
    NetflixContractExtractionWorkflow,
)
from pantheon_v2.processes.customers.netflix.models.contract_extraction_models import (
    NetflixContractExtractionWorkflowInputParams,
    GeneralData,
    Vendor,
)

from pantheon_v2.tools.core.internal_data_repository.activities import (
    update_internal_relational_data,
    query_internal_relational_data,
    query_internal_blob_storage,
)

from pantheon_v2.tools.core.internal_data_repository.models import (
    RelationalQueryResult,
    BlobStorageQueryResult,
)

from pantheon_v2.tools.common.contract_data_extracter.models import (
    ContractDataExtracterOutput,
)

from unittest.mock import patch


class TestContractExtractionWorkflow:
    @pytest.mark.asyncio
    async def test_contract_extraction_worklow_e2e(self):
        workflow = NetflixContractExtractionWorkflow()

        def mock_activity_response(*args, **kwargs):
            if args and args[0] == update_internal_relational_data:
                return None

            if args and args[0] == query_internal_blob_storage:
                return BlobStorageQueryResult(content=b"mock pdf content", metadata={})

            if args and args[0] == query_internal_relational_data:
                return RelationalQueryResult(
                    data=[Vendor(id="1", name="test")], row_count=1
                )

            return ContractDataExtracterOutput(extracted_data={})

        def mock_extract_game_details(*args, **kwargs):
            return GeneralData(
                vendor_or_developer_legal_name="test",
                vendor_country="test",
                vendor_state_or_province="test",
                netflix_legal_entity="test",
                games=[],
                license_renewal_option="test",
                live_service_length_in_years=1,
                live_service_renewal_option="test",
                rev_share_clause=True,
                rev_share_terms="test",
                cloud_option=True,
                deal_currency="test",
                total_deal_value=1000,
                license_term_length_in_years=1,
            )

        # Mock both execute_activity and wait_for_all
        with patch(
            "pantheon_v2.processes.customers.netflix.workflows.contract_extraction.workflow.execute_activity",
            side_effect=mock_activity_response,
        ):
            with patch(
                "pantheon_v2.processes.customers.netflix.workflows.contract_extraction.NetflixContractExtractionWorkflow._extract_game_details",
                side_effect=mock_extract_game_details,
            ):
                result = await workflow.execute(
                    NetflixContractExtractionWorkflowInputParams(
                        file_id="123",
                        gcs_path="gs://pantheon-contracts/netflix/contract.pdf",
                    )
                )

            assert result is not None
