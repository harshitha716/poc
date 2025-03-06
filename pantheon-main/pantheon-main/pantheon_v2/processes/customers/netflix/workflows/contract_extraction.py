from pantheon_v2.processes.core.registry import WorkflowRegistry
from typing import Type, TypeVar
from temporalio import workflow
from pydantic import BaseModel
import asyncio
from pantheon_v2.processes.customers.netflix.models.contract_extraction_models import (
    ContractExtractedData,
    GameMilestones,
    GamePaymentSchedule,
    PaymentInstallmentsCreationOutput,
    GameExtractedData,
    PaymentInstallments,
    PaymentFrequency,
    PaymentScheduleType,
    PaymentSchedule,
    GamePaymentInstallments,
    NetflixContractExtractionWorkflowInputParams,
    GeneralData,
    Vendor,
    PaymentInstallmentsCreationInput,
)

with workflow.unsafe.imports_passed_through():
    import json
    import structlog

    logger = structlog.get_logger(__name__)
    from dateutil.relativedelta import relativedelta

    from datetime import timedelta

    from pantheon_v2.tools.core.internal_data_repository.models import (
        RelationalQueryParams,
        RelationalUpdateParams,
        BlobStorageQueryParams,
    )
    from pantheon_v2.tools.core.internal_data_repository.activities import (
        query_internal_relational_data,
        update_internal_relational_data,
        query_internal_blob_storage,
    )

    from pantheon_v2.tools.common.pdf_parser.config import PDFParserConfig
    from pantheon_v2.tools.common.pdf_parser.models import ParsePDFParams
    from pantheon_v2.tools.common.pdf_parser.activities import parse_pdf

    from pantheon_v2.tools.common.contract_data_extracter.models import (
        ContractDataExtracterInput,
        ContractDataExtracterOutput,
    )
    from pantheon_v2.tools.common.contract_data_extracter.activities import (
        extract_contract_data,
    )

T = TypeVar("T", bound=BaseModel)


@WorkflowRegistry.register_workflow_defn(
    "Workflow that extracts contract data of games from a PDF",
    labels=["netflix"],
)
class NetflixContractExtractionWorkflow:
    @WorkflowRegistry.register_workflow_run
    async def execute(
        self, input_data: NetflixContractExtractionWorkflowInputParams
    ) -> ContractExtractedData:
        logger.info(
            "Executing Netflix Contract Extraction Workflow", input_data=input_data
        )

        # Step 1: Update the extraction step to EXTRACTING_GENERALISED_DATA
        await self._update_extracted_data(
            input_data, {"currentextractionstep": "EXTRACTING_GENERALISED_DATA"}
        )

        # Step 2: Extract the general data
        general_data = await self._extract_game_details(input_data, GeneralData)

        # Step 3: Update the extraction step to EXTRACTING_PAYMENT_DATA
        vendor_id = await self._get_vendor_id(
            general_data.vendor_or_developer_legal_name
        )

        # Step 4: If vendor found, update the vendor_id in extractedfiledata
        await self._update_extracted_data(
            input_data,
            {
                "currentextractionstep": "EXTRACTING_PAYMENT_DATA",
                "extracteddata": json.dumps(
                    {"general_data": general_data.model_dump()}
                ),
                "vendorname": general_data.vendor_or_developer_legal_name,
                "vendorid": vendor_id,
            },
        )

        extracted_data = ContractExtractedData(
            general_data=general_data,
            payment_installments=[],
            payment_schedules=[],
            game_milestones=[],
        )
        if len(general_data.games) == 0:
            return extracted_data

        # Step 5: Extract the game milestones.
        extracted_data.game_milestones = await self._extract_game_milestones(
            input_data, general_data
        )

        # Step 6: Extract the payment schedules
        game_payment_schedules: list[
            GamePaymentSchedule
        ] = await self._get_payment_schedules(input_data, general_data)

        extracted_data.payment_schedules = [
            game_payment_schedule.payment_schedule
            for game_payment_schedule in game_payment_schedules
        ]

        # Step 7: Create the payment installments
        payment_installments_response = await self._create_payment_installments(
            PaymentInstallmentsCreationInput(
                general_data=general_data,
                game_milestones=extracted_data.game_milestones,
                payment_schedules=game_payment_schedules,
            )
        )
        extracted_data.payment_installments = (
            payment_installments_response.game_extracted_data.payment_installments
        )

        # Step 8: Update the extracted data
        await self._update_extracted_data(
            input_data, {"extracteddata": json.dumps(extracted_data.model_dump())}
        )

        # TODO (Giri): Upload the data to Snowflake
        return extracted_data

    async def _get_payment_schedules(
        self,
        input_data: NetflixContractExtractionWorkflowInputParams,
        general_data: GeneralData,
    ) -> list[GamePaymentSchedule]:
        payment_schedule_tasks = [
            self._extract_game_details(
                input_data,
                GamePaymentSchedule,
                f"Now generate the payment schedule for the game: {game}",
            )
            for game in general_data.games
        ]

        # Execute all tasks in parallel and wait for results
        game_payment_schedules = await asyncio.gather(*payment_schedule_tasks)

        return game_payment_schedules

    async def _extract_game_milestones(
        self,
        input_data: NetflixContractExtractionWorkflowInputParams,
        general_data: GeneralData,
    ):
        game_milestones: list[GameMilestones] = []
        extraction_tasks = []

        for game in general_data.games:
            extraction_tasks.append(
                self._extract_game_details(
                    input_data,
                    GameMilestones,
                    f"Now generate the data for the game: {game}",
                )
            )

        # Execute all tasks in parallel and wait for results
        game_data_responses = await asyncio.gather(*extraction_tasks)

        for game, response in zip(general_data.games, game_data_responses):
            game_milestones.append(response)
            logger.info("Extracted game milestone data", game=game)

        return game_milestones

    async def _update_extracted_data(
        self, input_data: NetflixContractExtractionWorkflowInputParams, values: dict
    ):
        # call update postgres data activity
        await workflow.execute_activity(
            update_internal_relational_data,
            args=[
                RelationalUpdateParams(
                    table="extractedfiledata",
                    data=values,
                    where={"id": input_data.file_id},
                )
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

    async def _get_vendor_id(self, vendor_name: str):
        cleaned_vendor_name = "".join(e.lower() for e in vendor_name if e.isalnum())
        vendor_search_result = await workflow.execute_activity(
            query_internal_relational_data,
            args=[
                RelationalQueryParams(
                    query="SELECT id, name FROM zampapagentvendors WHERE REGEXP_REPLACE(LOWER(name), '[^a-z0-9]', '', 'g') = :cleaned_name",
                    parameters={"cleaned_name": cleaned_vendor_name},
                    output_model=Vendor,
                )
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

        return vendor_search_result.data[0].id if vendor_search_result.data else ""

    async def _extract_game_details(
        self,
        input_data: NetflixContractExtractionWorkflowInputParams,
        output_model: Type[BaseModel],
        additional_prompt="",
    ) -> BaseModel:
        gcs_path = input_data.gcs_path.replace("gs://", "")
        bucket_name, file_name = gcs_path.split("/", 1)

        gcs_response = await workflow.execute_activity(
            query_internal_blob_storage,
            BlobStorageQueryParams(
                bucket_name=bucket_name,
                file_name=file_name,
            ),
            start_to_close_timeout=timedelta(minutes=10),
        )

        pdf_content = gcs_response.content

        parsed_pdf_response = await workflow.execute_activity(
            parse_pdf,
            args=[
                PDFParserConfig(),
                ParsePDFParams(
                    pdf_content=pdf_content,
                    extract_tables=False,
                ),
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

        extracted_pdf_text_output = parsed_pdf_response.to_text()

        extraction_response: ContractDataExtracterOutput[
            output_model
        ] = await workflow.execute_activity(
            extract_contract_data,
            args=[
                ContractDataExtracterInput(
                    document_content=extracted_pdf_text_output,
                    output_model=output_model,
                    additional_prompt=additional_prompt,
                )
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

        # Convert extraction_response.extracted_data which is a base model to output_model
        return extraction_response.extracted_data

    async def _create_payment_installments(
        self, input_params: PaymentInstallmentsCreationInput
    ) -> PaymentInstallmentsCreationOutput:
        try:
            term_length = input_params.general_data.license_term_length_in_years
            deal_currency = input_params.general_data.deal_currency
            games_map = {game.game_name: game for game in input_params.game_milestones}
            schedules_map = {
                schedule.game_name: schedule
                for schedule in input_params.payment_schedules
            }

            # Get unique set of all game names
            all_games = set(games_map.keys()) | set(schedules_map.keys())

            # Process each game
            game_installments = [
                self._process_payment_installments_for_game(
                    game_name=game_name,
                    game_milestone=games_map.get(game_name),
                    game_schedule=schedules_map.get(game_name),
                    term_length=term_length,
                    deal_currency=deal_currency,
                )
                for game_name in all_games
            ]

            return PaymentInstallmentsCreationOutput(
                game_extracted_data=GameExtractedData(
                    general_data=input_params.general_data,
                    payment_installments=game_installments,
                )
            )

        except Exception as e:
            logger.error("Error in payment installments creation", error=str(e))
            raise

    """
    PAYMENT INSTALLMENTS SECTION
    """

    def _process_payment_installments_for_game(
        self,
        *,
        game_name: str,
        game_milestone: GameMilestones | None,
        game_schedule: GamePaymentSchedule | None,
        term_length: float,
        deal_currency: str,
    ) -> GamePaymentInstallments:
        """Process a single game's milestones and schedules."""
        milestone_installments = []
        other_service_installments = []

        if game_milestone:
            milestone_installments = self._process_milestones(
                game_milestone, deal_currency
            )

        if game_schedule:
            for schedule in game_schedule.payment_schedule:
                other_service_installments.extend(
                    self._process_schedule(schedule, term_length, deal_currency)
                )

        return GamePaymentInstallments(
            game_name=game_name,
            milestones=milestone_installments,
            other_services=other_service_installments,
        )

    def _get_frequency_delta(self, frequency: PaymentFrequency) -> relativedelta:
        """Get the time delta based on payment frequency."""
        frequency_mapping = {
            PaymentFrequency.WEEKLY: relativedelta(weeks=1),
            PaymentFrequency.MONTHLY: relativedelta(months=1),
            PaymentFrequency.QUARTERLY: relativedelta(months=3),
            PaymentFrequency.SEMI_ANNUAL: relativedelta(months=6),
            PaymentFrequency.ANNUAL: relativedelta(years=1),
        }
        return frequency_mapping[frequency]

    def _calculate_num_installments(
        self, term_length: float, frequency: PaymentFrequency
    ) -> int:
        """Calculate number of installments based on term length and frequency."""
        frequency_per_year = {
            PaymentFrequency.WEEKLY: 52,
            PaymentFrequency.MONTHLY: 12,
            PaymentFrequency.QUARTERLY: 4,
            PaymentFrequency.SEMI_ANNUAL: 2,
            PaymentFrequency.ANNUAL: 1,
        }
        return int(term_length * frequency_per_year[frequency])

    def _payment_type_display_name(self, payment_type: str) -> str:
        """Convert payment type enum values to display names."""
        try:
            return PaymentScheduleType(payment_type).display_name
        except ValueError:
            return payment_type

    def _format_display_amount(self, amount: float, currency_code: str) -> str:
        if amount is None or currency_code is None:
            return None

        try:
            return f"{currency_code} {float(amount):,.2f}"
        except (ValueError, TypeError):
            logger.warning(
                "Failed to format amount", amount=amount, currency_code=currency_code
            )
            return None

    def _create_single_installment(
        self,
        *,
        milestone_number: str | None = None,
        development_phase: str | None = None,
        payment_type: str | None = None,
        payment_terms: str | None = None,
        milestone_description: str | None = None,
        payment_amount: float,
        delivery_date: str | None = None,
        installment_number: int,
        deal_currency: str,
    ) -> PaymentInstallments:
        """Create a single payment installment with the given parameters."""
        payment_type_display_name = (
            self._payment_type_display_name(payment_type) if payment_type else None
        )

        # Format the display amount
        display_amount = self._format_display_amount(payment_amount, deal_currency)

        return PaymentInstallments(
            milestone_number=milestone_number,
            development_phase=development_phase,
            payment_type=payment_type_display_name,
            payment_terms=payment_terms,
            milestone_description=milestone_description,
            payment_amount=payment_amount,
            payment_amount_display=display_amount,
            delivery_date=delivery_date,
            installment_number=installment_number,
        )

    def _process_schedule(
        self, schedule: PaymentSchedule, term_length: float, deal_currency: str
    ) -> list[PaymentInstallments]:
        """Process a single payment schedule and return its installments."""
        installments = []

        for phase in schedule.phases:
            num_installments = (
                phase.number_of_installments
                or self._calculate_num_installments(term_length, phase.frequency)
            )

            installment_amount = phase.installment_amount or (
                round(schedule.payment_schedule_amount / num_installments, 2)
            )

            for i in range(num_installments):
                installment = self._create_single_installment(
                    payment_type=schedule.payment_schedule_type.value,
                    payment_terms=schedule.payment_schedule_terms,
                    payment_amount=installment_amount,
                    installment_number=i + 1,
                    deal_currency=deal_currency,
                )
                installments.append(installment)

        return installments

    def _process_milestones(
        self, game_milestone: GameMilestones, deal_currency: str
    ) -> list[PaymentInstallments]:
        """Process game milestones and return milestone installments."""
        return [
            self._create_single_installment(
                milestone_number=milestone.milestone_number,
                development_phase=milestone.development_phase,
                payment_type=milestone.payment_type,
                payment_terms=milestone.payment_terms,
                milestone_description=milestone.milestone_description,
                payment_amount=milestone.payment_amount,
                delivery_date=milestone.delivery_date,
                installment_number=1,
                deal_currency=deal_currency,
            )
            for milestone in game_milestone.milestones
        ]
