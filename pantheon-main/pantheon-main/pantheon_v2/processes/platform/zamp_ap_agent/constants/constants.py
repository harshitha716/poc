EMAIL_SEARCH_CONFIG = {
    "LIST_ADDRESS": "ap@zamp.finance",
    "MAX_RESULTS": 100,
    "INCLUDE_BODY": True,
}

VENDOR_BY_EMAIL_QUERY = """
    SELECT id FROM zampapagentvendors WHERE email = :email;
"""

ZAMPAPAGENTEMAILS = "zampapagentemails"

QUERY_SELECT_MESSAGE_IDS = """
    SELECT message_id FROM zampapagentemails WHERE message_id = ANY(:message_ids);
"""

QUERY_SELECT_EMAILS_BY_IDS_AND_STATUS = """
    SELECT id, message_id FROM zampapagentemails WHERE id = ANY(:ids) AND status = :status
"""

STATUS_PROCESSED = "processed"
STATUS_UNPROCESSED = "unprocessed"
