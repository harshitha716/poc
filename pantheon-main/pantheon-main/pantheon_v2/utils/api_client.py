from typing import TypeVar, Type, Optional, Dict, Any, Union
import aiohttp
from pydantic import BaseModel, ValidationError
import json
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ApiError(Exception):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class ApiClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.timeout = timeout

    async def request(
        self,
        method: HttpMethod,
        endpoint: str,
        response_model: Type[T],
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> T:
        """
        Make an HTTP request and return the response parsed into the specified Pydantic model.

        Args:
            method: HTTP method to use
            endpoint: API endpoint to call
            response_model: Pydantic model class to parse the response into
            data: Request body data (dict or Pydantic model)
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            Instance of response_model

        Raises:
            ApiError: If the request fails or response cannot be parsed
        """
        try:
            # Combine headers
            request_headers = {**self.default_headers}
            if headers:
                request_headers.update(headers)

            # Prepare URL
            url = f"{self.base_url}{endpoint}" if self.base_url else endpoint

            # Prepare request body
            if isinstance(data, BaseModel):
                request_data = data.model_dump_json()
                request_headers.setdefault("Content-Type", "application/json")
            elif isinstance(data, dict):
                request_data = json.dumps(data)
                request_headers.setdefault("Content-Type", "application/json")
            else:
                request_data = data

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method.value,
                    url=url,
                    headers=request_headers,
                    params=params,
                    data=request_data,
                    timeout=timeout or self.timeout,
                    ssl=True,  # Ensure SSL is enabled
                ) as response:
                    response_text = await response.text()

                    if not response.ok:
                        raise ApiError(
                            f"Request failed with status {response.status}: {response_text}",
                            status_code=response.status,
                            response_body=response_text,
                        )

                    try:
                        # Try to parse as JSON first
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        raise ApiError(
                            f"Invalid JSON response: {str(e)}",
                            response_body=response_text,
                        )

                    try:
                        # Parse into the specified Pydantic model
                        return response_model.model_validate(response_data)
                    except ValidationError as e:
                        raise ApiError(
                            f"Response validation failed: {str(e)}",
                            response_body=response_text,
                        )

        except aiohttp.ClientError as e:
            raise ApiError(f"Request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, ApiError):
                raise
            raise ApiError(f"Unexpected error: {str(e)}")
