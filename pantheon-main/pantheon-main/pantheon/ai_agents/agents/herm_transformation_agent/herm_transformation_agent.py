import os
from typing import Dict, List, Tuple
import structlog
import yaml
import uuid

from pantheon.ai_agents.internal.llm_service.service import LLMService
from pantheon.ai_agents.internal.llm_service.enums.llmclient import (
    LLMModel,
    Role,
    ContentType,
)
from pantheon.ai_agents.agents.herm_transformation_agent.schemas.herm_transformation_agent import (
    HermTransformationsActionsResponse,
    Action,
    Param,
)

from pantheon.ai_agents.internal.llm_service.enums.llmclient import LLMClientType

from pantheon.ai_agents.tools.herm.tool import HermTool
from pantheon.utils.utils import extract_yaml_from_response
from pantheon.ai_agents.agents.herm_transformation_agent.constants.herm_transformation_agent_constants import (
    PLANNING_PROMPT_FILE_PATH,
    EXECUTION_PROMPT_FILE_PATH,
    VALIDATION_PROMPT_FILE_PATH,
    STATUS_FAILED,
    STATUS_SUCCESS,
)

logger = structlog.get_logger(__name__)


class HermTransformationAgent:
    def __init__(self):
        self.anthropic_llm_client = LLMService(client_type=LLMClientType.ANTHROPIC)
        self.openai_llm_client = LLMService(client_type=LLMClientType.OPENAI)
        self.herm_tool = HermTool()

    @staticmethod
    def _load_prompt(file_path: str) -> str:
        filepath = os.path.join(os.path.dirname(__file__), file_path)
        try:
            with open(filepath, "r") as file:
                return file.read()
        except FileNotFoundError as e:
            logger.exception(
                "HERM_FORMULA_AGENT_ERROR_LOADING_SYSTEM_PROMPT", exception=str(e)
            )
            raise

    def get_herm_transformations(
        self, query: str, page_id: uuid.UUID, sheet_id: int
    ) -> HermTransformationsActionsResponse:
        planning_steps = self._get_planning_steps(query)
        if not planning_steps:
            return HermTransformationsActionsResponse(actions=[], status=STATUS_FAILED)
        logger.info(
            "HERM_TRANSFORMATION_AGENT_PLANNING_STEPS", planning_steps=planning_steps
        )

        herm_sheet_context = self._get_herm_context(page_id, sheet_id)
        transformation_actions = self._get_transformation_actions(
            planning_steps, herm_sheet_context
        )
        if not transformation_actions:
            return HermTransformationsActionsResponse(actions=[], status=STATUS_FAILED)
        logger.info(
            "HERM_TRANSFORMATION_AGENT_TRANSFORMATION_ACTIONS",
            transformation_actions=transformation_actions,
        )
        respose: HermTransformationsActionsResponse = self._convert_actions_to_response(
            transformation_actions
        )
        return respose

    def _get_planning_steps(self, query: str) -> List[str]:
        planning_prompt_messages = self._get_planning_prompt_messages(query)
        response = self.anthropic_llm_client.send_message(
            messages=planning_prompt_messages, model=str(LLMModel.Claude3_5Sonnet)
        )

        yaml_response = extract_yaml_from_response(response.content)
        logger.info(
            "HERM_TRANSFORMATION_AGENT_PLANNING_STEPS_RESPONSE",
            response=response.content,
        )
        if (
            yaml_response
            and isinstance(yaml_response, dict)
            and "steps" in yaml_response
        ):
            return yaml_response["steps"]
        else:
            logger.error(
                "HERM_TRANSFORMATION_AGENT_ERROR_PARSING_PLANNING_STEPS",
                response=response.content,
            )
            return []

    def _get_planning_prompt_messages(self, query: str) -> List[Dict[str, str]]:
        planning_prompt_template = self._load_prompt(PLANNING_PROMPT_FILE_PATH)
        planning_prompt = planning_prompt_template.replace("{{USER_QUERY}}", query)
        planning_prompt_messages: List = [
            {Role.ROLE: Role.USER, ContentType.CONTENT: planning_prompt}
        ]
        return planning_prompt_messages

    def _get_transformation_actions(
        self, planning_steps: List[str], herm_sheet_context: Dict
    ) -> List[Dict]:
        execution_steps: List[Dict] = self._get_execution_steps(
            planning_steps, herm_sheet_context
        )

        reordered_execution_steps = self.reorder_sequence_no(execution_steps)

        if not reordered_execution_steps:
            return []
        logger.info(
            "HERM_TRANSFORMATION_AGENT_EXECUTION_STEPS",
            execution_steps=reordered_execution_steps,
        )

        if any(
            step.get("name") == "NO_TRANSFORMATIONS_FOUND"
            for step in reordered_execution_steps
        ):
            logger.info("HERM_TRANSFORMATION_AGENT_NO_TRANSFORMATIONS_FOUND")
            return []

        return reordered_execution_steps

    def _get_execution_steps(
        self,
        planning_steps: List[str],
        herm_sheet_context: Dict,
    ) -> List[Dict]:
        all_actions = []
        for step in planning_steps:
            execution_prompt_messages = self._get_execution_prompt_messages(
                step, herm_sheet_context
            )
            response = self.anthropic_llm_client.send_message(
                messages=execution_prompt_messages, model=str(LLMModel.Claude3_5Sonnet)
            )
            yaml_response = extract_yaml_from_response(response.content)
            if (
                yaml_response
                and isinstance(yaml_response, dict)
                and "actions" in yaml_response
            ):
                actions = yaml_response["actions"]
                for action in actions:
                    all_actions.append(action)
                    if action["name"] in [
                        "ADD_COLUMN",
                        "REMOVE_COLUMN",
                        "UPDATE_CELL",
                        "ADD_ROW",
                        "REMOVE_ROW",
                    ]:
                        updated_context = self.herm_tool.update_sheet_context(
                            action, herm_sheet_context["sheet_context"]
                        )
                        logger.info(
                            "HERM_TRANSFORMATION_AGENT_UPDATED_CONTEXT",
                            updated_context=updated_context,
                        )
                        logger.info("HERM_ACTION", action=action)
                        herm_sheet_context["sheet_context"] = updated_context
            else:
                logger.error(
                    "HERM_TRANSFORMATION_AGENT_ERROR_PARSING_EXECUTION_STEPS",
                    response=response.content,
                )
                return []

        return all_actions

    def _get_execution_prompt_messages(
        self, planning_step: str, herm_sheet_context: Dict
    ) -> List[Dict[str, str]]:
        execution_prompt_template = self._load_prompt(EXECUTION_PROMPT_FILE_PATH)
        replacements = {
            "{{ATOMIC_STEPS}}": yaml.dump(planning_step),
            "{{TRANSFORMATIONS}}": yaml.dump(
                herm_sheet_context.get("transformations", [])
            ),
            "{{FORMULAS}}": yaml.dump(herm_sheet_context.get("formulas", [])),
            "{{SPREADSHEET_CONTEXT}}": yaml.dump(
                herm_sheet_context.get("sheet_context", {})
            ),
        }
        execution_prompt = execution_prompt_template
        for placeholder, value in replacements.items():
            execution_prompt = execution_prompt.replace(placeholder, value)

        return [{Role.ROLE: Role.USER, ContentType.CONTENT: execution_prompt}]

    def _get_herm_context(self, page_id: uuid.UUID, sheet_id: int) -> Dict:
        herm_formulas_library = self.herm_tool.get_herm_formulas()
        herm_transformations_library = self.herm_tool.get_herm_transformations()
        herm_sheet_context = self.herm_tool.get_sheet_context(page_id, sheet_id)
        return {
            "formulas": herm_formulas_library,
            "transformations": herm_transformations_library,
            "sheet_context": herm_sheet_context,
        }

    def _validate_actions(
        self, user_query: str, actions: List[Dict], herm_sheet_context: Dict
    ) -> Tuple[bool, str]:
        validation_output = self._get_validation(
            user_query, actions, herm_sheet_context
        )
        if not validation_output:
            return True, ""
        logger.info(
            "HERM_TRANSFORMATION_AGENT_VALIDATION_OUTPUT",
            validation_output=validation_output,
        )
        if isinstance(validation_output, list) and len(validation_output) > 0:
            confidence_score = validation_output[0].get("confidence_score", 0)
            if int(confidence_score) >= 85:
                return True, ""
            else:
                return False, validation_output[0].get("improvement_explanation", "")
        else:
            # return expected actions since validation loop failed
            return True, ""

    def _get_validation(
        self, user_query: str, actions: List[Dict], herm_sheet_context: Dict
    ) -> List[Dict]:
        try:
            validation_prompt_messages = self._get_validation_prompt_messages(
                user_query, actions, herm_sheet_context
            )
            response = self.anthropic_llm_client.send_message(
                messages=validation_prompt_messages, model=str(LLMModel.Claude3_5Sonnet)
            )
            yaml_response = extract_yaml_from_response(response.content)
            if (
                yaml_response
                and isinstance(yaml_response, dict)
                and "output" in yaml_response
            ):
                return yaml_response["output"]
            else:
                logger.error(
                    "HERM_TRANSFORMATION_AGENT_ERROR_PARSING_VALIDATION_STEPS",
                    response=response.content,
                )
                return []

        except Exception as e:
            logger.exception(
                "HERM_TRANSFORMATION_AGENT_ERROR_GETTING_VALIDATION_STEPS",
                user_query=user_query,
                actions=actions,
                exception=str(e),
            )
            return []

    def _get_validation_prompt_messages(
        self, user_query: str, actions: List[Dict], herm_sheet_context: Dict
    ) -> List[Dict[str, str]]:
        validation_prompt_template = self._load_prompt(VALIDATION_PROMPT_FILE_PATH)
        replacements = {
            "{{SPREADSHEET_CONTEXT}}": yaml.dump(
                herm_sheet_context.get("sheet_context", {})
            ),
            "{{USER_QUERY}}": user_query,
            "{{TRANSFORMATIONS_LIBRARY}}": yaml.dump(
                herm_sheet_context.get("transformations", [])
            ),
            "{{FUNCTIONAL_LIBRARY}}": yaml.dump(herm_sheet_context.get("formulas", [])),
            "{{ACTIONS}}": yaml.dump(actions),
        }
        validation_prompt = validation_prompt_template
        for placeholder, value in replacements.items():
            validation_prompt = validation_prompt.replace(placeholder, value)

        return [{Role.ROLE: Role.USER, ContentType.CONTENT: validation_prompt}]

    def _convert_actions_to_response(
        self, actions: List[Dict]
    ) -> HermTransformationsActionsResponse:
        converted_actions = []
        for action in actions:
            params = [
                Param(name=p["name"], value=str(p["value"])) for p in action["params"]
            ]
            converted_actions.append(
                Action(
                    name=action["name"],
                    params=params,
                    sequence_no=action["sequence_no"],
                )
            )

        return HermTransformationsActionsResponse(
            actions=converted_actions, status=STATUS_SUCCESS
        )

    def reorder_sequence_no(self, actions_list):
        for index, action in enumerate(actions_list):
            action["sequence_no"] = (
                index + 1
            )  # Ensuring sequence_no matches the index (1-based)
        return actions_list
