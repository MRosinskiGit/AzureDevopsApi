import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from AzApi.AzApi import AzApi
from AzApi.utils.AzApi_agents import AgentsBy

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
TEST_CAPABILITY_NAME = "tmp_systemtest_capability"


@pytest.fixture()
def fixture_remove_created_capability(request):
    self = request.instance
    yield
    self.api.Agents.remove_user_capabilities(AGENT_NAME, AgentsBy.Agent_Name, TEST_CAPABILITY_NAME)


@pytest.fixture()
def fixture_create_capability(request):
    self = request.instance
    self.api.Agents.add_user_capabilities(AGENT_NAME, AgentsBy.Agent_Name, {TEST_CAPABILITY_NAME: "valueofvar"})
    yield


@pytest.mark.skipif(not POOL, reason="Agents Pool name not defined.")
class Test_AzApi_Agents_functions_correct_pat:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = AzApi(organization=ORG, project=PRO, token=PAT)
        self.api.agent_pool_name = POOL

    def test_all_agents_getter(self):
        if AGENT_NAME:
            assert self.api.Agents.all_agents.get(AGENT_NAME)
        else:
            assert len(self.api.Agents.all_agents) == 0

    @pytest.mark.skipif(not AGENT_NAME, reason="Agents name not defined.")
    @pytest.mark.parametrize("by", [AgentsBy.Agent_Name, AgentsBy.PC_Name, AgentsBy.ID])
    def test_get_agent_capabilities(self, by):
        match by:
            case AgentsBy.Agent_Name:
                key = AGENT_NAME
            case AgentsBy.PC_Name:
                key = self.api.Agents.all_agents.get(AGENT_NAME).get("pc_name")
            case AgentsBy.ID:
                key = self.api.Agents.all_agents.get(AGENT_NAME).get("id")

        capabilities = self.api.Agents.get_agent_capabilities(key, by)
        assert capabilities.get("userCapabilities")
        assert capabilities.get("systemCapabilities")

    @pytest.mark.skipif(not AGENT_NAME, reason="Agents name not defined.")
    @pytest.mark.parametrize("by", [AgentsBy.Agent_Name, AgentsBy.PC_Name, AgentsBy.ID])
    def test_add_user_capabilities(self, by, fixture_remove_created_capability):
        match by:
            case AgentsBy.Agent_Name:
                key = AGENT_NAME
            case AgentsBy.PC_Name:
                key = self.api.Agents.all_agents.get(AGENT_NAME).get("pc_name")
            case AgentsBy.ID:
                key = self.api.Agents.all_agents.get(AGENT_NAME).get("id")
        self.api.Agents.add_user_capabilities(key, by, {TEST_CAPABILITY_NAME: "valueofvar"})
        capabilities = self.api.Agents.get_agent_capabilities(key, by)
        assert capabilities.get("userCapabilities").get(TEST_CAPABILITY_NAME) == "valueofvar"

    @pytest.mark.skipif(not AGENT_NAME, reason="Agents name not defined.")
    @pytest.mark.parametrize("by", [AgentsBy.Agent_Name, AgentsBy.PC_Name, AgentsBy.ID])
    def test_remove_user_capabilities(self, by, fixture_create_capability):
        match by:
            case AgentsBy.Agent_Name:
                key = AGENT_NAME
            case AgentsBy.PC_Name:
                key = self.api.Agents.all_agents.get(AGENT_NAME).get("pc_name")
            case AgentsBy.ID:
                key = self.api.Agents.all_agents.get(AGENT_NAME).get("id")
        self.api.Agents.remove_user_capabilities(key, by, TEST_CAPABILITY_NAME)
        capabilities = self.api.Agents.get_agent_capabilities(key, by)
        assert not capabilities.get("userCapabilities").get(TEST_CAPABILITY_NAME)
