import unittest

from pantheon.routers.health.router import health
from pantheon.routers.health.schemas.health import HealthResponse


class TestPageRouter(unittest.IsolatedAsyncioTestCase):
    async def test_health__ok(self):
        response: HealthResponse = await health()
        assert response.status == "ok"
