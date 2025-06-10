import pytest
from unittest.mock import patch, MagicMock

from loguru import logger

from AzApi.AzApi import AzApi
from AzApi.utils.AzApi_boards import WorkItemsDef, WorkItemsStatesDef


from ut_AzApi.testdata import create_workitem_mock


logger.configure(handlers={})


@pytest.fixture
def api_mock():
    with (
        patch("requests.get") as mock_get,
        patch("requests.post") as mock_post,
        patch("requests.put") as mock_put,
        patch("requests.patch") as mock_patch,
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        mock_put.return_value = mock_response
        mock_patch.return_value = mock_response

        yield {"get": mock_get, "post": mock_post, "response": mock_response, "put": mock_put, "patch": mock_patch}


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
