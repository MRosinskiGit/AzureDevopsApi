from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from AzApi.AzApi import AzApi
from AzApi.utils.AzApi_repos import PrStatusesDef, _AzRepos
from tests_AzApi.ut_AzApi.testdata import branch_list_response_mock, create_pr_response_mock, get_active_prs_mock

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
        mock_response_put.status_code = 201
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


def test_AzApi_repo_init_positivie(api_mock):
    api = AzApi("Org", "Pro", "123")
    assert api.repository_name is Ellipsis
    with pytest.raises(AzApi.ComponentException):
        _ = api.Repos
    api.repository_name = "Repos2"
    assert api.repository_name == "Repos2"
    assert api.Repos is not Ellipsis


@pytest.mark.parametrize("repo_name", [None, "", 123])
def test_AzApi_repo_init_negative(api_mock, repo_name):
    api = AzApi("Org", "Pro", "123")
    with pytest.raises(AttributeError):
        api.repository_name = repo_name
    assert api.repository_name is Ellipsis
    with pytest.raises(AzApi.ComponentException):
        _ = api.Repos


class Tests_AzApi_repos:
    @pytest.fixture(autouse=True)
    def setup_method(self, api_mock):
        self.api_mock = api_mock
        self.api = AzApi("Org", "Pro", "123")
        self.api.repository_name = "Repo"

    def test_change_repo_name_positive(self):
        self.api.repository_name = "Repos2"
        assert self.api.repository_name == "Repos2"
        assert self.api.Repos is not Ellipsis

    @pytest.mark.parametrize("repo_name", [None, "", 123])
    def test_change_repo_name_negative(self, repo_name):
        old_repo_instance = self.api.Repos
        old = self.api.repository_name
        with pytest.raises(AttributeError):
            self.api.repository_name = repo_name
        assert self.api.repository_name == old
        assert self.api.Repos is old_repo_instance

    def test_get_active_pull_requests_raw(self):
        self.api_mock["get"].return_value = get_active_prs_mock
        active_prs = self.api.Repos.get_active_pull_requests(raw=True)
        assert active_prs[0]["pullRequestId"] == 1
        assert active_prs[0]["sourceRefName"] == "refs/heads/test2"
        assert active_prs[0]["targetRefName"] == "refs/heads/main"

    def test_get_active_pull_requests(self):
        self.api_mock["get"].return_value = get_active_prs_mock
        active_prs = self.api.Repos.get_active_pull_requests(raw=False)
        assert 1 in active_prs.keys()
        assert active_prs[1]["sourceRefName"] == "refs/heads/test2"
        assert active_prs[1]["targetRefName"] == "refs/heads/main"

    def test_get_all_branches_raw(self):
        self.api_mock["get"].return_value = branch_list_response_mock
        branches = self.api.Repos.get_all_branches(raw=True)
        assert len(branches) == 3
        assert branches[0]["name"] == "refs/heads/main"
        assert branches[1]["name"] == "refs/heads/test1"
        assert branches[2]["name"] == "refs/heads/test2"

    def test_get_all_branches(self):
        self.api_mock["get"].return_value = branch_list_response_mock
        branches = self.api.Repos.get_all_branches(raw=False)
        assert len(branches) == 3
        assert branches["refs/heads/main"]["creator"] == "ciej R"
        assert branches["refs/heads/test1"]["creator"] == "MRosi"
        assert branches["refs/heads/test2"]["creator"] == "MRosi"

    def test_create_pr(self):
        self.api_mock["post"].return_value = create_pr_response_mock
        with patch.object(_AzRepos, "get_active_pull_requests") as mck:
            mck.return_value = {}
            pr_number = self.api.Repos.create_pr("Test PR", "test2", "main")
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
        new_api._AzApi__Repos = _AzRepos(new_api, "")
        with pytest.raises(AttributeError):
            fun = getattr(new_api.Repos, method)
            if params:
                if isinstance(params, list):
                    fun(*params)
                else:
                    fun(params)
            else:
                fun()

    @pytest.mark.parametrize(
        "submodules, depth, branch, cwd",
        [
            (True, 2, "test/dev", ".output"),
            (True, None, None, "/"),
            (False, 1, None, "test"),
        ],
    )
    def test_clone_repo_default(self, submodules, depth, branch, cwd):
        with (
            patch("subprocess.Popen") as mck_subprocess,
            patch("AzApi.utils.AzApi_repos.ThreadPoolExecutor") as mck_executor,
        ):
            mck_submit = MagicMock()
            mck_submit.return_value = True
            mck_executor.submit = mck_submit
            mck_subprocess.return_value = MagicMock(
                wait=MagicMock(return_value=0), terminate=MagicMock(return_value=True)
            )

            self.api.Repos.clone_repository(cwd, branch=branch, depth=depth, submodules=submodules)

            mck_subprocess.assert_called_once()
            args, kwargs = mck_subprocess.call_args
            cmd_submodules = "--recurse-submodules --shallow-submodules "
            assert " ".join(args[0]) + " " == (
                f"git clone https://Org@dev.azure.com/Org/Pro/_git/Repo {cmd_submodules if submodules else ''}"
                f"{'--branch ' + branch + ' ' if branch else ''}{'--depth ' + str(depth) + ' ' if depth else ''}"
            )

    @pytest.mark.parametrize(
        "submodules, depth, branch, cwd",
        [
            (True, 2, "test/dev", ".output"),
            (True, None, None, "/"),
            (False, 1, None, "test"),
        ],
    )
    def test_clone_repo_custom_url(self, submodules, depth, branch, cwd):
        with (
            patch("subprocess.Popen") as mck_subprocess,
            patch("AzApi.utils.AzApi_repos.ThreadPoolExecutor") as mck_executor,
        ):
            mck_submit = MagicMock()
            mck_submit.return_value = True
            mck_executor.submit = mck_submit
            mck_subprocess.return_value = MagicMock(
                wait=MagicMock(return_value=0), terminate=MagicMock(return_value=True)
            )

            self.api.Repos.clone_repository(
                cwd, branch=branch, depth=depth, submodules=submodules, custom_url="https://gitrepolink.git"
            )

            mck_subprocess.assert_called_once()
            args, kwargs = mck_subprocess.call_args
            cmd_submodules = "--recurse-submodules --shallow-submodules "
            assert " ".join(args[0]) + " " == (
                f"git clone https://gitrepolink.git {cmd_submodules if submodules else ''}"
                f"{'--branch ' + branch + ' ' if branch else ''}{'--depth ' + str(depth) + ' ' if depth else ''}"
            )

    def test_add_pr_reviewer(self):
        with (
            patch.object(self.api, "search_user_aad_descriptor_by_email") as mock_search,
            patch.object(self.api, "get_guid_by_descriptor") as mock_get_guid,
        ):
            mock_search.return_value = "ABCDEFGH"
            mock_get_guid.return_value = "1234-GUID"

            self.api.Repos.add_pr_reviewer(123, "user@gmail.com")

            mock_search.assert_called_once_with("user@gmail.com")
            mock_get_guid.assert_called_once_with("ABCDEFGH")
            self.api_mock["put"].assert_called_once()
            args, kwargs = self.api_mock["put"].call_args
            assert kwargs.get("json") == {
                "id": "1234-GUID",
                "vote": 0,
            }

    @pytest.mark.parametrize("branch_name", ["test1", "refs/heads/test1"])
    def test_delete_branch(self, branch_name):
        with patch.object(self.api.Repos, "get_all_branches") as mck:
            mck.return_value = {"refs/heads/test1": {"objectId": "11111111111111111111111111111111111111"}}
            self.api.Repos.delete_branch(branch_name)

    @pytest.mark.parametrize("status", [PrStatusesDef.Abandoned, PrStatusesDef.Completed, PrStatusesDef.Active])
    def test_change_pr_status(self, status):
        self.api.Repos.change_pr_status(1, status)
        self.api_mock["patch"].assert_called_once()
        args, kwargs = self.api_mock["patch"].call_args
        assert kwargs.get("json") == {"status": status}
