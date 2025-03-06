OUTPUT_MODEL_CONSTANT = "{{OUTPUT_MODEL}}"
OUTPUT_START_TAG = "<output>"
OUTPUT_END_TAG = "</output>"

SCHEMA_INSTRUCTIONS = [
    "Your response MUST conform to the following JSON schema specification.",
    "Do not include any explanations or additional text outside the JSON response.",
    "Schema:",
    "```json",
    "{}",  # Placeholder for actual schema
    "```",
    "Ensure your response is valid JSON that matches this schema exactly.",
]

REQUIRED_TAGS = {OUTPUT_MODEL_CONSTANT: "OUTPUT_MODEL"}
