from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class GeneralData(BaseModel):
    vendor_or_developer_legal_name: Optional[str] = Field(
        ..., description="The legal name of the vendor or developer"
    )
    vendor_country: Optional[str] = Field(
        ..., description="The country of the vendor or developer"
    )
    vendor_state_or_province: Optional[str] = Field(
        ..., description="The state or province of the vendor or developer"
    )
    netflix_legal_entity: Optional[str] = Field(
        ..., description="The legal entity of Netflix"
    )
    games: list[str] = Field(..., description="The list of games")
    license_term_length_in_years: Optional[float] = Field(
        ..., description="The length of the license term in years"
    )
    license_renewal_option: Optional[str] = Field(
        ...,
        description=(
            "Extract all relevant license renewal terms. If the renewal option is not mentioned, leave it null. Do not create your own renewal option or assume it. Extract data only when some explicit renewal terms are mentioned. Current services terms are not classified as renewal terms. If some relevant terms are mentioned in different sections, extract them all and return them as a single string."
        ),
    )
    live_service_length_in_years: Optional[float] = Field(
        ..., description="The length of the live service in years"
    )
    live_service_renewal_option: Optional[str] = Field(
        ...,
        description=(
            "The renewal option of the live services. Extract all relevant renewal terms. If the renewal option is not mentioned, leave it null. Do not create your own renewal option or assume it. Extract data only when some explicit renewal terms are mentioned. Current services terms are not classified as renewal terms."
        ),
    )
    rev_share_clause: Optional[bool] = Field(
        ..., description="Whether the revenue share clause is present."
    )
    rev_share_terms: Optional[str] = Field(
        ...,
        description="The terms of the revenue share clause. Please provide the exact text of the clause and extract all the relevant information related to reve",
    )
    cloud_option: Optional[bool] = Field(
        ..., description="Whether the cloud option is present"
    )
    deal_currency: Optional[str] = Field(..., description="The currency of the deal")
    total_deal_value: Optional[float] = Field(
        ..., description="The total value of the deal"
    )


class GameMilestoneData(BaseModel):
    milestone_number: Optional[str] = Field(
        ...,
        description="The number of the milestone. Extract the same details from the table. Dont create your own numbers. For eg, M01, M02, R01, R02, Live Release 1, Live Release 2 etc.",
    )
    development_phase: Optional[str] = Field(
        ...,
        description="The development phase of the milestone. Extract the same phase as mentioned in the table. This can be blank if the phase is not mentioned in the table. It has values like Alpha, Beta, Release Ready etc.",
    )
    payment_type: Optional[str] = Field(
        ...,
        description="The type of payment for the milestone. If the fees is related to milestone, it needs to be MILESTONE. If its related to Live Services/Content Update, it needs to be LIVE_SERVICES. Try to fit the payment type into one of these categories. If nothing seems relevant, leave it as MILESTONE_FEE",
    )
    payment_terms: Optional[str] = Field(
        ..., description="The terms of the payment for the milestone"
    )
    milestone_description: Optional[str] = Field(
        ...,
        description="The description of the milestone. Extract all the relevant information related to the milestone. It might be on one more than one page.",
    )
    payment_amount: Optional[float] = Field(
        ..., description="The amount of the payment for the milestone"
    )
    delivery_date: Optional[str] = Field(
        ..., description="The date of the delivery for the milestone"
    )


class GameMilestones(BaseModel):
    game_name: Optional[str] = Field(..., description="The name of the game")
    milestones: list[GameMilestoneData] = Field(
        ...,
        description="List of milestone data for the game. Do not include any of the milestones with headings like Initial Live Services, Support and Maintenance, Balance of License Fee etc. These are typically development milestones with specific deliverables and payment terms. They have types like Alpha ready, beta ready, production, live ops etc and always well descriptive and under the milestone schedule table. A milestone needs to have either a milestone number, development phase, due date or amount. They are payment schedules and they are not to be extracted as milestones.",
    )


class NetflixContractExtractionWorkflowInputParams(BaseModel):
    file_id: int
    gcs_path: str


class PaymentFrequency(str, Enum):
    """
    Enum representing the frequency of payments in a payment schedule.
    """

    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"


class PaymentScheduleType(str, Enum):
    BALANCE_OF_LICENSE_FEE = "BALANCE_OF_LICENSE_FEE"
    SUPPORT_AND_MAINTENANCE = "SUPPORT_AND_MAINTENANCE"
    INITIAL_LIVE_SERVICES = "INITIAL_LIVE_SERVICES"
    DEVELOPER_FEE = "DEVELOPER_FEE"

    @property
    def display_name(self) -> str:
        """Get the human-readable display name for the payment type."""
        mapping = {
            self.BALANCE_OF_LICENSE_FEE: "License Fee",
            self.SUPPORT_AND_MAINTENANCE: "Support and Maintenance",
            self.INITIAL_LIVE_SERVICES: "Live Services",
            self.DEVELOPER_FEE: "Developer Fee",
        }
        return mapping[self]


class PaymentPhase(BaseModel):
    """
    Model representing a specific phase in a payment schedule, including type,
    installment details, and amounts.
    """

    number_of_installments: Optional[int] = Field(
        ...,
        description="Number of installments in this phase. Dont create your own number of installments. Only extract this field if the number of installments is explicitly mentioned in the contract. If not applicable leave it null",
    )
    installment_amount: Optional[float] = Field(
        ...,
        description="Amount per installment. Dont create your own installment amount. Only extract this field if the installment amount is explicitly mentioned in the contract. Dont confuse this with the total amount of the payment schedule. If not applicable leave it null",
    )
    frequency: PaymentFrequency = Field(
        ...,
        description="Payment frequency (WEEKLY, MONTHLY, QUARTERLY, SEMI_ANNUAL, or ANNUAL)",
    )
    is_payment_term_applicable: bool = Field(
        ...,
        description="Whether the installment needs to be paid through the applicable payment term.",
    )


class PaymentSchedule(BaseModel):
    payment_schedule_amount: float = Field(
        ...,
        description="The amount of the payment schedule. Look for amounts that appear immediately after or below table headers like 'Amount', 'Balance', or similar financial indicators. When multiple similar amounts appear in the document, prioritize extracting values that are presented in table cells rather than in paragraphs or prose text. If its BALANCE_OF_LICENSE_FEE, do not use the total amount mentioned in the contract. Use the amount mentioned in the table.",
    )
    currency: str = Field(..., description="Currency of the payments")
    payment_schedule_type: PaymentScheduleType = Field(
        ...,
        description="Type of the payment schedule. Can be one of: BALANCE_OF_LICENSE_FEE, SUPPORT_AND_MAINTENANCE, LIVE_SERVICES, DEVELOPER_FEE. Try to fit the payment schedule type into one of these categories.",
    )
    payment_schedule_terms: Optional[str] = Field(
        ...,
        description="The terms of the payment schedule for the milestone. Extract the same text from the contract. If not applicable leave it null",
    )
    phases: list[PaymentPhase] = Field(
        ...,
        description="List of payment phases. You dont have to break down into installments. If multiple types of phases are mentioned you can return all of them.",
    )


class GamePaymentSchedule(BaseModel):
    game_name: Optional[str] = Field(..., description="The name of the game")
    payment_schedule: list[PaymentSchedule] = Field(
        ..., description="List of payment schedules for the game"
    )


class PaymentInstallments(BaseModel):
    milestone_number: str | None = None
    development_phase: str | None = None
    payment_type: str | None = None
    payment_terms: str | None = None
    milestone_description: str | None = None
    payment_amount: float | None = None
    payment_amount_display: str | None = None
    delivery_date: str | None = None
    installment_number: int


class GamePaymentInstallments(BaseModel):
    game_name: Optional[str] = Field(..., description="The name of the game")
    milestones: list[PaymentInstallments] = Field(
        ..., description="List of payment installments for the game"
    )
    other_services: list[PaymentInstallments] = Field(
        ..., description="List of payment installments for the game"
    )


class GameExtractedData(BaseModel):
    general_data: GeneralData
    payment_installments: list[GamePaymentInstallments]


class ContractExtractedData(BaseModel):
    general_data: GeneralData
    payment_schedules: list[PaymentSchedule]
    payment_installments: list[GamePaymentInstallments]


class PaymentInstallmentsCreationInput(BaseModel):
    general_data: GeneralData
    game_milestones: list[GameMilestones]
    payment_schedules: list[GamePaymentSchedule]


class PaymentInstallmentsCreationOutput(BaseModel):
    game_extracted_data: GameExtractedData


class Vendor(BaseModel):
    id: str
    name: str
