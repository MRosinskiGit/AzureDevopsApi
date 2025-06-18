import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from loguru import logger

from AzApi.AzApi import AzApi
from AzApi.utils.AzApi_repos import PrStatusesDef

# logger.remove()
try:
    env_path = Path(__file__).resolve().parent / "systemtest.env"
except NameError:
    env_path = "st_AzApi/systemtest.env"
load_dotenv(env_path)
ORG = os.getenv("ORGANIZATION")
PRO = os.getenv("PROJECT")
PAT = os.getenv("PAT")
REPO = os.getenv("REPOSITORY")
POOL = os.getenv("AGENT_POOL")
AGENT_NAME = os.getenv("AGENT_NAME")
USER_EMAIL = os.getenv("USER_EMAIL")
MAIN_BRANCH_NAME = os.getenv("MAIN_BRANCH_NAME")
TEST_BRANCH_NAME = "tmp_systemtest_branch"


@pytest.fixture(scope="class")
def fixture_set_git_configuration_pat():
    logger.info("Setting GIT configuration with Token.")
    env = os.environ.copy()
    git_config_command = [
        "git",
        "config",
        "--global",
        "http.https://dev.azure.com/.extraheader",
        f"Authorization: Bearer {PAT}",
    ]

    subprocess.run(git_config_command, env=env)

    yield

    logger.info("Removing GIT configuration with Token.")
    remove_config_command = ["git", "config", "--global", "--unset-all", "http.https://dev.azure.com/.extraheader"]

    subprocess.run(remove_config_command)


@pytest.fixture(scope="class")
def fixture_clone_repository(fixture_set_git_configuration_pat, tmp_path_factory, request):
    output_dir = tmp_path_factory.mktemp("tmp_cloned_repo")

    git_clone_cmd = ["git", "clone", f"https://{ORG}@dev.azure.com/{ORG}/{PRO}/_git/{REPO}"]

    subprocess.run(git_clone_cmd, cwd=output_dir)

    yield output_dir


@pytest.fixture()
def fixture_create_and_push_test_branch(fixture_clone_repository, request):
    git_commands = [
        ["git", "checkout", "-b", TEST_BRANCH_NAME],
        ["git", "push", "-u", "origin", TEST_BRANCH_NAME],
    ]
    repo_path = os.path.join(fixture_clone_repository, REPO)

    subprocess.run(["git", "branch", "-D", TEST_BRANCH_NAME], cwd=repo_path, check=False)
    for cmd in git_commands:
        subprocess.run(cmd, cwd=repo_path, check=True)

    yield
    self = request.instance
    self.api.Repos.delete_branch(TEST_BRANCH_NAME)
    prs = self.api.Repos.get_active_pull_requests()
    for pr_id, pr_data in prs.items():
        if pr_data.get("sourceRefName") == f"refs/heads/{TEST_BRANCH_NAME}":
            self.api.Repos.change_pr_status(pr_id, PrStatusesDef.Abandoned)
            break


@pytest.mark.skipif(not REPO, reason="Repository name not defined.")
class Test_AzApi_Repos_functions_correct_pat:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = AzApi(organization=ORG, project=PRO, token=PAT)
        self.api.repository_name = REPO

    def test_get_all_branches(self):
        branches = self.api.Repos.get_all_branches()
        assert branches.get("refs/heads/master") or branches.get("refs/heads/main")

    @pytest.mark.parametrize(
        "submodules, depth, branch, kwargs",
        [
            (False, None, None, {}),
            (False, None, None, {"custom_url": "https://github.com/MRosinskiGit/AzureDevopsApi.git"}),
            (True, 1, MAIN_BRANCH_NAME, {}),
            (True, 1, "master", {"custom_url": "https://github.com/MRosinskiGit/AzureDevopsApi.git"}),
        ],
    )
    def test_clone_repository_std(
        self, tmp_path_factory, fixture_set_git_configuration_pat, submodules, depth, branch, kwargs
    ):
        output_path = tmp_path_factory.mktemp("temporary_clone")
        repo_path = self.api.Repos.clone_repository(output_path, submodules, depth, branch, **kwargs)
        assert os.path.exists(os.path.join(repo_path, ".git"))

    # def test_add_pr_reviewer(self):
    #     pass
    #
    # def test_get_active_pull_requests(self, fixture_create_and_push_test_branch):
    #     print("test")
    #
    # def test_get_active_pull_requests(self):
    #     pass
    #
    def test_create_pr_and_get_active_prs(self, fixture_create_and_push_test_branch):
        with patch("loguru.logger.warning") as mck:
            mck.return_value = logger.warning
            pr_id = self.api.Repos.create_pr("Test Branch", TEST_BRANCH_NAME, f"refs/heads/{MAIN_BRANCH_NAME}")
        prs = self.api.Repos.get_active_pull_requests()
        mck.assert_not_called()
        assert prs.get(pr_id)

    def test_get_pullrequest_url(self):
        assert (
            self.api.Repos.get_pullrequest_url(3)
            == f"https://dev.azure.com/{self.api.organization}/{self.api.project}/_git/{self.api.repository_name}/pullrequest/3"
        )

    def test_change_pr_status(self, fixture_create_and_push_test_branch):
        pr_id = self.api.Repos.create_pr("Test Branch", TEST_BRANCH_NAME, f"refs/heads/{MAIN_BRANCH_NAME}")
        prs_pre_change = self.api.Repos.get_active_pull_requests()
        self.api.Repos.change_pr_status(pr_id, PrStatusesDef.Abandoned)
        prs_post_change = self.api.Repos.get_active_pull_requests()
        assert prs_pre_change.get(pr_id)
        assert not prs_post_change.get(pr_id)
