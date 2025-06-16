import base64
from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from AzApi.AzApi import AzApi
from tests_AzApi.ut_AzApi.testdata import (
    get_guid_by_descriptor_mock,
    get_list_of_all_org_users_mock_continuous,
    get_list_of_all_org_users_mock_single_use,
)

logger.configure(handlers={})


@pytest.fixture
def api_mock():
    module_path = "AzApi.utils.http_client.requests"

    with (
        patch(f"{module_path}.get") as mock_get,
        patch(f"{module_path}.post") as mock_post,
        patch(f"{module_path}.put") as mock_put,
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_response_put = MagicMock()
        mock_response_put.status_code = 201
        mock_response_put.json.return_value = {}

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        mock_put.return_value = mock_response_put

        yield {
            "get": mock_get,
            "post": mock_post,
            "put": mock_put,
            "response": mock_response,
            "response_put": mock_response_put,
        }


class Tests_AzApi:
    @pytest.fixture(autouse=True)
    def setup(self, api_mock):
        self.api_mock = api_mock
        self.api = AzApi("Org", "Pro", "123456789")

    def test_token_setter(self):
        self.api.token = "987654321"
        assert self.api.token == "987***321"

    def test_token_getter(self):
        assert self.api.token == "123***789"

    def test_repo_setter(self):
        with patch("AzApi.AzApi._AzRepos") as mock_azrepos:
            mock_azrepos_instance = MagicMock()
            mock_azrepos.return_value = mock_azrepos_instance
            self.api.repository_name = "TestRepo"
            assert self.api.repository_name == "TestRepo"

    @pytest.mark.parametrize("repo_name", ["", 123, None])
    def test_repo_setter_exception(self, repo_name):
        with patch("AzApi.AzApi._AzRepos") as mock_azrepos:
            mock_azrepos_instance = MagicMock()
            mock_azrepos.return_value = mock_azrepos_instance
            with pytest.raises(AttributeError):
                self.api.repository_name = repo_name

    def test_repo_getter(self):
        assert self.api.repository_name is Ellipsis

    def test_pool_setter(self):
        with patch("AzApi.AzApi._AzAgents") as mock_azagents:
            mock_azagents_instance = MagicMock()
            mock_azagents.return_value = mock_azagents_instance
            self.api.agent_pool_name = "TestPool"
            assert self.api.agent_pool_name == "TestPool"

    @pytest.mark.parametrize("pool_name", ["", 123, None])
    def test_pool_setter_exception(self, pool_name):
        with patch("AzApi.AzApi._AzAgents") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            with pytest.raises(AttributeError):
                self.api.agent_pool_name = pool_name

    def test_pool_getter(self):
        assert self.api.agent_pool_name is Ellipsis

    def test_header(self):
        pat = "123456789"
        b64_token = base64.b64encode(f":{pat}".encode()).decode()
        expected = {"Content-Type": "application/json-patch+json", "Authorization": f"Basic {b64_token}"}
        assert self.api._headers() == expected

    def test_header_custom(self):
        pat = "123456789"
        b64_token = base64.b64encode(f":{pat}".encode()).decode()
        expected = {"Content-Type": "test_content/123", "Authorization": f"Basic {b64_token}"}
        assert self.api._headers("test_content/123") == expected

    @pytest.mark.parametrize(
        "response_mock",
        [
            [get_list_of_all_org_users_mock_single_use],
            [get_list_of_all_org_users_mock_continuous, get_list_of_all_org_users_mock_single_use],
        ],
    )
    def test_get_list_of_all_org_users(self, response_mock):
        self.api_mock["get"].side_effect = response_mock
        self.api._AzApi__get_list_of_all_org_users()

    def test_search_user_aad_descriptor_by_email_negative(self):
        self.api_mock["get"].return_value = get_list_of_all_org_users_mock_single_use
        assert self.api.search_user_aad_descriptor_by_email("test@gmail.com") is None

    def test_search_user_aad_descriptor_by_email_positive(self):
        self.api_mock["get"].return_value = get_list_of_all_org_users_mock_single_use
        assert (
            self.api.search_user_aad_descriptor_by_email("m.rosi97@gil.com")
            == "msa.NmRhOTcyZDUtZTVkNy03N2JiLWE2YWQtMTE3NWFhMmQ5YTk2"
        )

    def test_get_guid_by_descriptor_positive(self):
        self.api_mock["get"].return_value = get_guid_by_descriptor_mock
        assert (
            self.api.get_guid_by_descriptor("msa.NmRhOTcyZDUtZTVkNy03N2JiLWE2YWQtMTE3NWFhMmQ5YTk2")
            == "6da972d5-e5d7-67bb-a6ad-1175aa2d9a96"
        )
