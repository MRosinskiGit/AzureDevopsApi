import os
from pathlib import Path

import beartype
import pytest
from dotenv import load_dotenv

from azapidevops.AzApi import AzApi
from azapidevops.utils.AzApi_agents import _AzAgents
from azapidevops.utils.AzApi_repos import _AzRepos

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


def test_import_AzApi():
    try:
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")


def test_AzApi_init():
    api = AzApi(organization=ORG, project=PRO, token=PAT)
    assert isinstance(api, AzApi)


class Test_AzApi_correct_pat:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = AzApi(organization=ORG, project=PRO, token=PAT)

    def test_repo_not_initiated(self):
        with pytest.raises(AzApi.ComponentException):
            self.api.Repos.get_active_pull_requests()

    @pytest.mark.skipif(not REPO, reason="Repo name not defined.")
    def test_init_repo_positive(self):
        self.api.repository_name = REPO
        assert isinstance(self.api.Repos, _AzRepos)

    @pytest.mark.parametrize("repo_name", [None, 123])
    def test_init_repo_negative(self, repo_name):
        with pytest.raises(beartype.roar.BeartypeCallHintParamViolation):
            self.api.repository_name = repo_name

    def test_agents_not_initiated(self):
        with pytest.raises(AzApi.ComponentException):
            _ = self.api.Agents.all_agents

    @pytest.mark.skipif(not POOL, reason="Pool name not defined.")
    def test_agents_repo_positive(self):
        self.api.agent_pool_name = POOL
        assert isinstance(self.api.Agents, _AzAgents)

    @pytest.mark.parametrize("pool_name", [None, 123])
    def test_agents_repo_negative(self, pool_name):
        with pytest.raises(beartype.roar.BeartypeCallHintParamViolation):
            self.api.agent_pool_name = pool_name

    @pytest.mark.skipif(not USER_EMAIL, reason="User email not defined.")
    def test_search_user_aad_descriptor_by_email(self):
        descriptor = self.api.search_user_aad_descriptor_by_email(USER_EMAIL)
        assert len(descriptor) > 30

    @pytest.mark.skipif(not USER_EMAIL, reason="User email not defined.")
    def test_get_guid_by_descriptor(self):
        descriptor = self.api.search_user_aad_descriptor_by_email(USER_EMAIL)
        guid = self.api.get_guid_by_descriptor(descriptor)
        assert len(guid) > 20
