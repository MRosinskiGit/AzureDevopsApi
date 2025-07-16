import time

import pytest
import requests

from azapidevops.utils.http_client import _create_requests_session_with_retries_strategy


@pytest.mark.parametrize("status_code", [408, 429, 500, 502, 503, 504])
@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_incorrect_response_retires(status_code):
    session = _create_requests_session_with_retries_strategy()

    time_start_session = time.time()
    response = session.get(f"https://httpbingo.org/status/{status_code}")
    assert response.status_code == status_code
    time_exception_session = time.time() - time_start_session

    time_start_requests = time.time()
    response = requests.get(f"https://httpbingo.org/status/{status_code}")
    time_exception_requests = time.time() - time_start_requests
    time.sleep(2)
    assert response.status_code == status_code
    assert time_exception_session > time_exception_requests, (
        "Session with retries strategy should be slower than requests without retries strategy"
    )



@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_incorrect_response_noretries():
    session = _create_requests_session_with_retries_strategy()

    time_start_session = time.time()
    response = session.get("https://httpbingo.org/status/404")
    time_exception_session = time.time() - time_start_session
    time.sleep(2)
    assert response.status_code == 404

    time_start_requests = time.time()
    response = requests.get("https://httpbingo.org/status/404")
    time_exception_requests = time.time() - time_start_requests
    time.sleep(2)
    assert response.status_code == 404
    assert abs(time_exception_session - time_exception_requests) < 4, (
        "Session with retries strategy should be similar than requests without retries strategy"
    )
