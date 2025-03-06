import pytest
from aiohttp import ClientError
from pydantic import BaseModel
from typing import Optional
from aioresponses import aioresponses

from pantheon_v2.utils.api_client import ApiClient, ApiError, HttpMethod


# Test Models
class MockResponseModel(BaseModel):
    id: int
    name: str
    status: Optional[str] = None


class MockRequestModel(BaseModel):
    data: str


@pytest.fixture
def api_client():
    return ApiClient(
        base_url="https://api.example.com",
        default_headers={"Authorization": "Bearer test-token"},
    )


@pytest.fixture
def aiohttp_mock():
    with aioresponses() as m:
        yield m


@pytest.mark.asyncio
async def test_successful_get_request(aiohttp_mock, api_client):
    # Prepare test data
    mock_response = {"id": 1, "name": "test"}

    # Mock the API response
    aiohttp_mock.get("https://api.example.com/test", status=200, payload=mock_response)

    # Make request
    response = await api_client.request(
        method=HttpMethod.GET, endpoint="/test", response_model=MockResponseModel
    )

    # Assert response
    assert isinstance(response, MockResponseModel)
    assert response.id == 1
    assert response.name == "test"


@pytest.mark.asyncio
async def test_successful_post_request_with_model(aiohttp_mock, api_client):
    # Prepare test data
    request_data = MockRequestModel(data="test-data")
    mock_response = {"id": 1, "name": "test"}

    # Mock the API response
    aiohttp_mock.post("https://api.example.com/test", status=200, payload=mock_response)

    # Make request
    response = await api_client.request(
        method=HttpMethod.POST,
        endpoint="/test",
        response_model=MockResponseModel,
        data=request_data,
    )

    # Assert response
    assert isinstance(response, MockResponseModel)
    assert response.id == 1
    assert response.name == "test"


@pytest.mark.asyncio
async def test_failed_request(aiohttp_mock, api_client):
    # Mock failed API response
    aiohttp_mock.get("https://api.example.com/test", status=404, body="Not Found")

    # Assert error is raised
    with pytest.raises(ApiError) as exc_info:
        await api_client.request(
            method=HttpMethod.GET, endpoint="/test", response_model=MockResponseModel
        )

    assert exc_info.value.status_code == 404
    assert "Not Found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_invalid_json_response(aiohttp_mock, api_client):
    # Mock invalid JSON response
    aiohttp_mock.get("https://api.example.com/test", status=200, body="invalid json")

    # Assert error is raised
    with pytest.raises(ApiError) as exc_info:
        await api_client.request(
            method=HttpMethod.GET, endpoint="/test", response_model=MockResponseModel
        )

    assert "Invalid JSON response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validation_error(aiohttp_mock, api_client):
    # Mock response with missing required field
    mock_response = {"id": 1}  # missing 'name' field

    aiohttp_mock.get("https://api.example.com/test", status=200, payload=mock_response)

    # Assert error is raised
    with pytest.raises(ApiError) as exc_info:
        await api_client.request(
            method=HttpMethod.GET, endpoint="/test", response_model=MockResponseModel
        )

    assert "Response validation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout(aiohttp_mock, api_client):
    # Mock timeout
    aiohttp_mock.get("https://api.example.com/test", exception=ClientError("Timeout"))

    # Assert error is raised
    with pytest.raises(ApiError) as exc_info:
        await api_client.request(
            method=HttpMethod.GET, endpoint="/test", response_model=MockResponseModel
        )

    assert "Request failed" in str(exc_info.value)
