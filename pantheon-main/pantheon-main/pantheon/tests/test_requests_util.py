import unittest
from unittest import mock
from http import HTTPStatus
from pantheon.utils import requests


class TestGet(unittest.TestCase):
    @mock.patch("pantheon.utils.requests.requests.get")
    def test_get_success(self, mock_get):
        mock_response = mock.Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response

        response = requests.get("https://example.com")

        self.assertEqual(response, {"status": "ok"})
        mock_get.assert_called_once_with("https://example.com", params=None)

    @mock.patch("pantheon.utils.requests.requests.get")
    def test_get_failure(self, mock_get):
        mock_response = mock.Mock()
        mock_response.status_code = HTTPStatus.NOT_FOUND
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            requests.get("https://example.com")

        mock_get.assert_called_once_with("https://example.com", params=None)
