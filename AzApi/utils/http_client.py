import logging
from http import HTTPStatus

import requests as _requests
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__name__)


def _create_requests_session_with_retries_strategy() -> _requests.Session:
    """
    Creates a request session with 5 attempts if status code is related to incorrect server respond.
    [408, 429, 500, 502, 503, 504]
    Returns:
        requests.Session
    """
    logger.info("Creating requests session")
    session = _requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=0.2,
        status_forcelist=[
            HTTPStatus.REQUEST_TIMEOUT,
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ],
        raise_on_status=False,
    )

    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    logger.info("SUCCESS: Session created.")
    return session


# Global object for requests session with retries strategy
requests = _create_requests_session_with_retries_strategy()
