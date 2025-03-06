from pydantic import BaseModel
from typing import Callable, Dict, Any, List
from pantheon_v2.core.modelrouter.models.models import Message


class ExtractionRegistry(BaseModel):
    prompt_output_dto: BaseModel
    page_limit: int
    prompt_function: Callable[[Dict[str, Any]], list[Message]]
    custom_vars: Dict[str, Any]


def fetch_ocr_prompt(
    message_creator_func: Callable[[Dict[str, Any]], list[Message]],
    custom_vars: Dict[str, Any],
    file_contents_with_types: List[Dict[str, Any]],
) -> None:
    """
    A utility function to handle custom prompt creation and output formatting.

    Args:
        message_creator_func: A function that takes Dict[str, Any] context and returns list[Message]

    The function handles:
    - Input: Parses JSON from command line into Dict[str, Any]
    - Processing: Calls the message creator function
    - Output: Formats Messages as JSON within custom_prompt delimiters
    """
    try:
        context = {
            "provider": {},
            "vars": {
                "file_contents_with_types": file_contents_with_types,
                **custom_vars,
            },
        }

        # Call the provided function with context
        messages: list[Message] = message_creator_func(context)

        return messages

    except Exception as e:
        print(f"Error processing custom prompt: {str(e)}")
        raise e
