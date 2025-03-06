from typing import List, Type, Union, Dict
from pydantic import BaseModel
import json
import re
from pantheon_v2.core.prompt.base import BasePrompt
from pantheon_v2.core.prompt.models import PromptMessage
from pantheon_v2.core.prompt.constants import (
    OUTPUT_MODEL_CONSTANT,
    OUTPUT_START_TAG,
    OUTPUT_END_TAG,
    SCHEMA_INSTRUCTIONS,
)
from pantheon_v2.core.modelrouter.exceptions.exceptions import GenerationError
from pydantic import ValidationError


class ChainConfig(BaseModel):
    """Configuration for a prompt chain"""

    response_model: Type[BaseModel]


class PromptChain(BaseModel):
    """A chain of prompts that work together to produce structured output"""

    config: ChainConfig
    prompts: List[BasePrompt] = []

    def add_prompt(self, prompt: BasePrompt) -> "PromptChain":
        """Add a prompt to the chain"""
        self.prompts.append(prompt)
        return self

    def _format_model_schema(self) -> str:
        """Format the response model schema with output tags"""
        model_schema = json.dumps(
            self.config.response_model.model_json_schema(), indent=2
        )

        # Format schema with instructions
        schema_lines = [
            line if "{}" not in line else line.format(model_schema)
            for line in SCHEMA_INSTRUCTIONS
        ]

        return "\n".join([OUTPUT_START_TAG, *schema_lines, OUTPUT_END_TAG])

    def _validate_output_model_presence(self) -> None:
        """Validate that at least one prompt contains the OUTPUT_MODEL placeholder"""
        if not any(OUTPUT_MODEL_CONSTANT in prompt.template for prompt in self.prompts):
            raise ValueError(
                f"At least one prompt in the chain must contain the {OUTPUT_MODEL_CONSTANT} placeholder"
            )

    def _extract_json_from_brackets(self, content: str) -> Dict:
        """Extract JSON content between outermost brackets"""
        first_bracket = min(
            (content.find("["), "[")
            if content.find("[") != -1
            else (float("inf"), "["),
            (content.find("{"), "{")
            if content.find("{") != -1
            else (float("inf"), "{"),
            key=lambda x: x[0],
        )
        last_bracket = max(
            content.rfind("]") if first_bracket[1] == "[" else -1,
            content.rfind("}") if first_bracket[1] == "{" else -1,
        )

        if first_bracket[0] != float("inf") and last_bracket != -1:
            return json.loads(content[first_bracket[0] : last_bracket + 1])
        raise json.JSONDecodeError("No valid JSON found", content, 0)

    def _extract_json_with_regex(self, content: str) -> Dict:
        """Extract JSON using regex pattern"""
        json_pattern = r"\{[^{}]*\}"
        for match in re.finditer(json_pattern, content):
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
        raise json.JSONDecodeError("No valid JSON found", content, 0)

    def parse_response(self, content: str) -> Union[BaseModel, Dict, List[Dict]]:
        """Parse the LLM response into structured format"""
        try:
            # Extract content between output tags
            start_idx = content.find(OUTPUT_START_TAG) + len(OUTPUT_START_TAG)
            end_idx = content.find(OUTPUT_END_TAG)
            json_str = (
                content[start_idx:end_idx].strip()
                if start_idx != -1 and end_idx != -1
                else content
            )

            # Try different parsing strategies
            parsing_strategies = [
                lambda x: json.loads(x),  # Direct JSON parsing
                lambda x: json.loads(
                    x.replace("```json", "").replace("```", "").strip()
                ),  # Clean markdown
                self._extract_json_from_brackets,  # Extract from brackets
                self._extract_json_with_regex,  # Regex extraction
            ]

            for strategy in parsing_strategies:
                try:
                    data = strategy(json_str)
                    if isinstance(data, list):
                        return [
                            self.config.response_model.model_validate(item)
                            for item in data
                        ]
                    return self.config.response_model.model_validate(data)
                except (json.JSONDecodeError, ValidationError):
                    continue

            raise GenerationError(
                f"Failed to parse response into expected format. Content: {content}"
            )

        except Exception as e:
            if not isinstance(e, GenerationError):
                raise GenerationError(
                    f"Unexpected error during response parsing: {str(e)}"
                )
            raise

    def build_messages(self) -> List[PromptMessage]:
        """Build all messages in the chain, replacing output model schema where specified"""
        if not self.prompts:
            raise ValueError("No prompts added to the chain")

        self._validate_output_model_presence()

        messages = []
        schema = self._format_model_schema()

        for prompt in self.prompts:
            # Replace output model placeholder in template if present
            original_template = prompt.template
            if OUTPUT_MODEL_CONSTANT in original_template:
                # Use the property setter to update the template
                prompt.template = original_template.replace(
                    OUTPUT_MODEL_CONSTANT, schema
                )

            messages.extend(prompt.build_messages())

            # Restore original template
            # Restore original template
            prompt.template = original_template

        return messages
