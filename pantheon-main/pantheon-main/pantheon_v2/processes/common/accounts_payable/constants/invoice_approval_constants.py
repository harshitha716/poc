import datetime

FETCH_HIERARCHY_TIMEOUT = datetime.timedelta(minutes=2)
SLACK_MESSAGE_TIMEOUT = datetime.timedelta(minutes=2)
DEFAULT_TIMEOUT = datetime.timedelta(minutes=2)

STATUS_OK = "ok"
STATUS_ERROR = "error"
INVOICE_STATUS_UNPROCESSED = "unprocessed"
INVOICE_STATUS_PROCESSING = "processing"
INVOICE_STATUS_PENDING_APPROVAL = "pending_approval"
INVOICE_STATUS_APPROVED = "approved"
INVOICE_STATUS_DISAPPROVED = "disputed"

INVOICE_QUERY = """
select zv.approvers, zi.*
from zampapagentinvoices zi
left join zampapagentvendors zv on zi.vendorid = zv.id
where zi.id = :invoice_id;
"""

INVOICE_TABLE = "zampapagentinvoices"

FETCH_HIERARCHY_QUERY = """
select zi.id,
        zi.vendorid,
        round(zi.amount, 2)::varchar(255) as amount,
        to_char(zi.invoicedate, 'DD/MM/YYYY') as invoicedate,
        to_char(zi.duedate, 'DD/MM/YYYY') as duedate,
        zi.status,
        zv.approvers,
        zi.metadata,
        zi.description,
        zi.invoicebucketpath as invoice_gcs_path
from zampapagentinvoices zi
  inner join zampapagentvendors zv on zv.id = zi.vendorid
where zi.id = :invoice_id;
"""

METADATA_QUERY = (
    "select metadata from zampapagentinvoices zi where zi.id = :invoice_id;"
)
APPROVAL_HIERARCHY_KEY = "approval_hierarchy"

INVOICE_APPROVED_MESSAGE = "Invoice has been approved"
INVOICE_DISAPPROVED_MESSAGE = "Invoice has been disapproved"

APPROVAL_RESPONSE_DISAPPROVE = "disapprove"
APPROVAL_RESPONSE_APPROVE = "approve"
