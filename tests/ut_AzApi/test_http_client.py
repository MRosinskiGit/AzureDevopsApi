import requests
from loguru import logger

from azapidevops.utils.http_client import _create_requests_session_with_retries_strategy

logger.remove()


def test_create_session():
    x = _create_requests_session_with_retries_strategy()
    assert isinstance(x, requests.Session)
    assert x.adapters.get("https://")
    assert x.adapters.get("http://")
