from fastapi.testclient import TestClient
from pantheon.app import app

import unittest


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
