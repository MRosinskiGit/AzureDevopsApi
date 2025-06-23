import time

import pytest
import requests

from AzApi.utils.http_client import _create_requests_session_with_retries_strategy


@pytest.mark.parametrize("status_code", [408, 429, 500, 502, 503, 504])
def test_incorrect_response_retires(status_code):
    session = _create_requests_session_with_retries_strategy()

    time_start_session = time.time()
    response = session.get(f"https://httpbin.org/status/{status_code}")
    assert response.status_code == status_code
    time_exception_session = time.time() - time_start_session

    time_start_requests = time.time()
    response = requests.get(f"https://httpbin.org/status/{status_code}")
    assert response.status_code == status_code
    time_exception_requests = time.time() - time_start_requests
    assert time_exception_session > time_exception_requests, (
        "Session with retries strategy should be slower than requests without retries strategy"
    )


def test_incorrect_response_noretries():
    session = _create_requests_session_with_retries_strategy()

    time_start_session = time.time()
    response = session.get("https://httpbin.org/status/404")
    assert response.status_code == 404
    time_exception_session = time.time() - time_start_session

    time_start_requests = time.time()
    response = requests.get("https://httpbin.org/status/404")
    assert response.status_code == 404
    time_exception_requests = time.time() - time_start_requests
    assert abs(time_exception_session - time_exception_requests) < 4, (
        "Session with retries strategy should be similar than requests without retries strategy"
    )
