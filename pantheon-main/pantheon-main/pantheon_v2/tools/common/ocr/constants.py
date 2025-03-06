from pathlib import Path

INVOICE_EXTRACT_PROMPT_PATH = (
    Path(__file__).parent
    / "ocr_prompt_registry"
    / "invoice_extraction"
    / "prompts"
    / "invoice_extraction_prompt.txt"
)
