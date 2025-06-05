import pytest
from unittest.mock import patch, MagicMock

from loguru import logger

from AzApi.AzApi import AzApi

from testdata import branch_list_response_mock, create_pr_response_mock, get_active_prs_mock

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


class Tests_AzApi_repos:
    @pytest.fixture(autouse=True)
    def setup(self, api_mock):
        self.api_mock = api_mock
        self.api = AzApi("Org", "Pro", "123")
        self.api.repository_name = "Repo"

    def test_change_repo_name_positive(self):
        self.api.repository_name = "Repos2"
        assert self.api.repository_name == "Repos2"

    @pytest.mark.parametrize("repo_name", [None, "", 123])
    def test_change_repo_name_negative(self, repo_name):
        old = self.api.repository_name
        with pytest.raises(AttributeError):
            self.api.repository_name = repo_name
        assert self.api.repository_name == old

    def test_get_active_pull_requests_raw(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value = get_active_prs_mock
            active_prs = self.api.Repo.get_active_pull_requests(raw=True)
        assert active_prs[0]["pullRequestId"] == 1
        assert active_prs[0]["sourceRefName"] == "refs/heads/test2"
        assert active_prs[0]["targetRefName"] == "refs/heads/main"

    def test_get_active_pull_requests(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value = get_active_prs_mock
            active_prs = self.api.Repo.get_active_pull_requests(raw=False)
        assert 1 in active_prs.keys()
        assert active_prs[1]["sourceRefName"] == "refs/heads/test2"
        assert active_prs[1]["targetRefName"] == "refs/heads/main"

    def test_get_all_branches_raw(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value = branch_list_response_mock
            branches = self.api.Repo.get_all_branches(raw=True)
        assert len(branches) == 3
        assert branches[0]["name"] == "refs/heads/main"
        assert branches[1]["name"] == "refs/heads/test1"
        assert branches[2]["name"] == "refs/heads/test2"

    def test_get_all_branches(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value = branch_list_response_mock
            branches = self.api.Repo.get_all_branches(raw=False)
        assert len(branches) == 3
        assert branches["refs/heads/main"]["creator"] == "Maciej R"
        assert branches["refs/heads/test1"]["creator"] == "MRosi"
        assert branches["refs/heads/test2"]["creator"] == "MRosi"

    def test_create_pr(self):
        with patch("requests.post") as mock_get:
            mock_get.return_value = create_pr_response_mock
            pr_number = self.api.Repo.create_pr("Test PR", "test2", "main")
        assert pr_number == 1

    @pytest.mark.parametrize(
        "method, params",
        [
            ("get_active_pull_requests", None),
            ("create_pr", ["title", "source", "target"]),
            ("get_all_branches", None),
            ("get_pullrequest_url", 1234),
        ],
    )
    def test_repo_name_validation_decorator(self, method, params):
        new_api = AzApi("Org", "Pro", "123")
        with pytest.raises(AttributeError):
            fun = getattr(new_api.Repo, method)
            if params:
                if isinstance(params, list):
                    fun(*params)
                else:
                    fun(params)
            else:
                fun()
