from http import HTTPStatus
from typing import Any
import requests
import structlog

logger = structlog.get_logger(__name__)


def _check_response_success(
    response: requests.models.Response,
) -> None:
    is_success = HTTPStatus(response.status_code).is_success
    if not is_success:
        raise Exception(
            f"Request failed to: {response.url} with status code {response.status_code}"
        )


def get(url: str, query_params=None, **kwargs) -> Any:
    try:
        response = requests.get(url, params=query_params, **kwargs)
        time_taken = response.elapsed.total_seconds()
        _check_response_success(response)
        response_json = response.json()
        logger.info(
            "GET_REQUEST_SUCCESS",
            url=url,
            query_params=query_params,
            response=response_json,
            time_taken=time_taken,
        )
        return response_json
    except Exception as e:
        logger.info(
            "GET_REQUEST_FAILED",
            url=url,
            query_params=query_params,
            error=e,
        )
        raise e
