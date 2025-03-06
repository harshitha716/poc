class InvalidLLMClientType(Exception):
    code = "invalid_client_type"
    msg_template = "{msg}"


class NoLLMClientInitialised(Exception):
    code = "invalid_llm_client"
    msg_template = "{msg}"


class NoLLMResponse(Exception):
    code = "no_llm_response"
    msg_template = "{msg}"
