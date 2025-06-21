from unittest.mock import MagicMock, patch

import pytest
from beartype.door import is_bearable
from loguru import logger

from AzApi.AzApi import AzApi
from AzApi.utils.AzApi_boards import WorkItem, WorkItemsDef, WorkItemsStatesDef
from tests_AzApi.ut_AzApi.testdata import create_workitem_mock, id_details_response_mock, wiql_response_mock

logger.configure(handlers={})


@pytest.fixture
def api_mock():
    module_path = "AzApi.utils.http_client.requests"

    with (
        patch(f"{module_path}.get") as mock_get,
        patch(f"{module_path}.post") as mock_post,
        patch(f"{module_path}.put") as mock_put,
        patch(f"{module_path}.patch") as mock_patch,
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_response_put = MagicMock()
        mock_response_put.status_code = 200
        mock_response_put.json.return_value = {}

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        mock_put.return_value = mock_response_put
        mock_patch.return_value = mock_response

        yield {
            "get": mock_get,
            "post": mock_post,
            "put": mock_put,
            "patch": mock_patch,
            "response": mock_response,
            "response_put": mock_response_put,
        }


class Tests_AzApi_boards:
    @pytest.fixture(autouse=True)
    def setup(self, api_mock):
        self.api_mock = api_mock
        self.api = AzApi("Org", "Pro", "123")

    def test_create_new_item(self):
        self.api_mock["post"].return_value = create_workitem_mock
        assert self.api.Boards.create_new_item(work_item_type=WorkItemsDef.TestCase, item_name="Item") == 4

    def test_change_work_item_state(self):
        self.api.Boards.change_work_item_state(4, WorkItemsStatesDef.TestCase.Design)
        self.api_mock["patch"].assert_called_once()

    def test_get_work_items(self, api_mock):
        api_mock["post"].return_value = wiql_response_mock
        api_mock["get"].return_value = id_details_response_mock
        items = self.api.Boards.get_work_items(
            WorkItemsDef.Task, allowed_states=[WorkItemsStatesDef.Task.To_Do, WorkItemsStatesDef.Task.Doing]
        )
        assert is_bearable(items, dict[int, WorkItem])
