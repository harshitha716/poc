from pantheon_v2.processes.customers.netflix.workflows.contract_extraction import (
    NetflixContractExtractionWorkflow,
)
from pantheon_v2.processes.common.table_detection_workflow.table_detection_workflow import (
    TableDetectionWorkflow,
)

from pantheon_v2.processes.common.accounts_payable.workflows.invoice_approval import (
    InvoiceApprovalWorkflow,
)
from pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent import (
    ZampAPAgentWorkflow,
)

from pantheon_v2.processes.common.sample.workflows.sample_workflow import (
    SampleWorkflow,
)

exposed_workflows = [
    # Netflix
    NetflixContractExtractionWorkflow,
    # A/P
    InvoiceApprovalWorkflow,
    ZampAPAgentWorkflow,
    # Table Detection
    TableDetectionWorkflow,
    # Sample
    SampleWorkflow,
]
