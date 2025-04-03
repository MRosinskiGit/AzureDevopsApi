import pytest
from loguru import logger

from AzApi.AzApi import AzApi
from unittest.mock import patch, MagicMock


logger.configure(handlers={})


@pytest.fixture
def api_mock():
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response

        yield {"get": mock_get, "post": mock_post, "response": mock_response}


class Tests_AzApi:
    @pytest.fixture(autouse=True)
    def setup(self, api_mock):
        self.api_mock = api_mock
        self.api = AzApi("Org", "Pro", "123")

    def test_change_repo_name_positive(self):
        self.api.repository_name = "Repo"
        assert self.api.repository_name == "Repo"

    @pytest.mark.parametrize("repo_name", [None, "", 123])
    def test_change_repo_name_negative(self, repo_name):
        with pytest.raises(AttributeError):
            self.api.repository_name = repo_name
