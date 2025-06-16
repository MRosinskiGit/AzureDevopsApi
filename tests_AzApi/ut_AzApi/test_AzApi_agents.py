import json
from unittest.mock import MagicMock, patch

import pytest

from AzApi.AzApi import AzApi
from AzApi.utils.AzApi_agents import AgentsBy, _AzAgents
from tests_AzApi.ut_AzApi.testdata import (
    get_agent_capabilities_mock,
    get_agents_list_mock,
    get_pools_list_mock,
)

# logger.configure(handlers={})


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
            "mock_patch": mock_patch,
            "response": mock_response,
            "response_put": mock_response_put,
        }


def test_AzApi_agents_init_posittvie(api_mock):
    with (
        patch.object(_AzAgents, "_AzAgents__get_all_pools") as mock_get_all_pools,
        patch.object(_AzAgents, "_AzAgents__get_all_agents") as mock_get_all_agents,
    ):
        mock_get_all_pools.return_value = {"Project_pool": 10}
        mock_get_all_agents.return_value = {"Asus": {"id": 9, "pc_name": "ASUS-MR"}}
        api = AzApi("Org", "Pro", "123")
        assert api.agent_pool_name is Ellipsis
        with pytest.raises(AzApi.ComponentException):
            _ = api.Agents
        api.agent_pool_name = "Project_pool"
        assert api.agent_pool_name == "Project_pool"
        assert isinstance(api.Agents, _AzAgents)


@pytest.mark.parametrize("pool_name", [None, "", 123])
def test_AzApi_agents_init_negative(pool_name):
    api = AzApi("Org", "Pro", "123")
    with pytest.raises(AttributeError):
        api.agent_pool_name = pool_name
    assert api.agent_pool_name is Ellipsis
    with pytest.raises(AzApi.ComponentException):
        _ = api.Agents


class Tests_AzApi_agents:
    @pytest.fixture(autouse=True)
    def setup(self, api_mock):
        with (
            patch.object(_AzAgents, "_AzAgents__get_all_pools") as mock_get_all_pools,
            patch.object(_AzAgents, "_AzAgents__get_all_agents") as mock_get_all_agents,
        ):
            mock_get_all_pools.return_value = {"Project_pool": 10}
            mock_get_all_agents.return_value = {
                "Asus": {
                    "id": 9,
                    "pc_name": "ASUS-MR",
                    "capabilities": {"userCapabilities": {"existingflag1": "true", "existingflag2": "true"}},
                }
            }
            self.api_mock = api_mock
            self.api = AzApi("Org", "Pro", "123")
            self.api.agent_pool_name = "Project_pool"

    def test_all_agents_getter(self):
        assert self.api.Agents.all_agents == {
            "Asus": {
                "capabilities": {"userCapabilities": {"existingflag1": "true", "existingflag2": "true"}},
                "id": 9,
                "pc_name": "ASUS-MR",
            }
        }

    def test_get_all_pools(self):
        with patch.object(_AzAgents, "_AzAgents__get_all_agents") as mock_get_all_agents:
            mock_get_all_agents.return_value = {"AgentName": {"id": 4}}
            self.api_mock["get"].return_value = get_pools_list_mock
            api = AzApi("Org", "Pro", "123")
            api.agent_pool_name = "Project_pool"
            pools = api.Agents._AzAgents__get_all_pools()
            assert pools.get("Project_pool") == 10

    def test__get_all_agents(self):
        with (
            patch.object(_AzAgents, "_AzAgents__get_all_pools") as mock_get_all_pools,
            patch.object(_AzAgents, "get_agent_capabilities") as mock_capabilities,
        ):
            mock_capabilities.return_value = {
                "userCapabilities": {"hardware_available": "true"},
                "systemCapabilities": {
                    "Agent.Version": "4.255.0",
                },
            }
            mock_get_all_pools.return_value = {"Project_pool": 10}
            self.api_mock["get"].return_value = get_agents_list_mock
            api = AzApi("Org", "Pro", "123")
            api.agent_pool_name = "Project_pool"
            agents = api.Agents._AzAgents__get_all_agents(10)
            assert len(agents) == 1
            assert agents.get("Asus")
            print(agents["Asus"])
            assert agents["Asus"].get("id")
            assert agents["Asus"].get("capabilities")
            assert agents["Asus"].get("status")

    @pytest.mark.parametrize("key,by", [(9, AgentsBy.ID), ("Asus", AgentsBy.Agent_Name), ("ASUS-MR", AgentsBy.PC_Name)])
    def test__resolve_agent_key(self, key, by):
        assert self.api.Agents._AzAgents__resolve_agent_key(key, by) == 9

    @pytest.mark.parametrize("key,by", [(9, AgentsBy.ID), ("Asus", AgentsBy.Agent_Name), ("ASUS-MR", AgentsBy.PC_Name)])
    def test_get_agent_capabilities(self, key, by):
        self.api_mock["get"].return_value = get_agent_capabilities_mock
        agent = self.api.Agents.get_agent_capabilities(key, by)
        assert agent["systemCapabilities"].get("Agent.Name") == "Asus"
        assert agent["systemCapabilities"].get("Agent.ComputerName") == "ASUS-MR"
        assert agent["userCapabilities"].get("testflag") == "2"

    def test_add_user_capabilities(self):
        self.api_mock["get"].return_value = get_agent_capabilities_mock
        self.api_mock["put"].return_value = MagicMock(status_code=200)
        self.api.Agents.add_user_capabilities(9, AgentsBy.ID, {"testflag": "testval"})
        self.api_mock["put"].assert_called_once()
        args, kwargs = self.api_mock["put"].call_args
        data = kwargs.get("data")
        data = json.loads(data)
        assert data.get("existingflag1") == "true"
        assert data.get("testflag") == "testval"
        assert self.api.Agents._AzAgents__all_agents["Asus"]["capabilities"]["userCapabilities"] == {
            "existingflag1": "true",
            "existingflag2": "true",
            "testflag": "testval",
        }

    @pytest.mark.parametrize("cap_to_remove", ["existingflag1", ["existingflag1", "existingflag2"]])
    def test_remove_user_capabilities(self, cap_to_remove):
        self.api_mock["get"].return_value = get_agent_capabilities_mock
        self.api_mock["put"].return_value = MagicMock(status_code=200)
        self.api.Agents.remove_user_capabilities(9, AgentsBy.ID, cap_to_remove)
        self.api_mock["put"].assert_called_once()
        if cap_to_remove == "existingflag1":
            expected = {"existingflag2": "true"}
        else:
            expected = {}
        assert self.api.Agents._AzAgents__all_agents["Asus"]["capabilities"]["userCapabilities"] == expected
