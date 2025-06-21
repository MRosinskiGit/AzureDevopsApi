import json
from enum import Enum, auto
from functools import wraps
from typing import TYPE_CHECKING, Union

from loguru import logger
from requests.exceptions import RequestException

if TYPE_CHECKING:
    from AzApi.AzApi import AzApi
from .http_client import requests


def _require_valid_pool_name(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        pool_name = getattr(self, "_AzAgents__pool_name", None)
        if not isinstance(pool_name, str) or pool_name == "":
            raise AttributeError("Invalid pool name: must be a non-empty string.")
        return method(self, *args, **kwargs)

    return wrapper


class AgentsBy(Enum):
    Agent_Name = auto()
    PC_Name = auto()
    ID = auto()


class _AzAgents:
    def __init__(self, api: "AzApi", pool_name: str):  # noqa: F821
        """
        Constructor for Agents Pool control component.
        Args:
            api: Object of AzApi parent.
            pool_name: name of agents pool in Azure Devops portal.
        """
        logger.info("Initializing AzApi Agents Tool.")
        self.__pool_name = pool_name
        self.__azure_api = api
        self.__all_pools = self.__get_all_pools()
        self.__pool_id = self.__all_pools.get(self.__pool_name)
        if not self.__pool_id:
            logger.error("Pool name not detected in organization.")
            logger.debug(f"{self.__pool_name} not found in {self.__all_pools}.")
            raise NameError("Pool name not detected in organization.")
        self.__all_agents = self.__get_all_agents(self.__pool_id)
        logger.success("Agents Component initialized.")

    @property
    def all_agents(self) -> dict[str, dict]:
        """
        Getter for all available agents in the pool.
        Returns:
            dict: dict with agents names and properites
        Examples:
            >>> api = AzApi('org','pro','pat')
            >>> api.agent_pool_name = "pool"
            >>> api.Agents.all_agents
                {"Agents_Name": {
                "id": 4,
                "pc_name": "LAB_BENCH_5521,
                "capabilities": {
                    "userCapabilities":{"hardware_available":true}
                    "systemCapabilities":{...,"Agent.Version":"4.255.0",...},
                    },
                "status": "online",
            },}
        """
        return self.__all_agents

    def __get_all_pools(self) -> dict[str, int]:
        """
        Private method to download all available agents pools in the organization.
        Returns:
        dict: dict with name of pool as a key, and ID of pool as value.
        """
        logger.debug("Downloading list of all available pools...")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools?api-version=7.2-preview.1"
        response = requests.get(url, headers=self.__azure_api._headers())

        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.debug(f"Found {response.json()['count']} pools.")
        response_json = response.json()["value"]
        logger.success("Pools list updated.")
        return {pool.get("name"): pool.get("id") for pool in response_json}

    def __get_all_agents(self, pool_id: int) -> dict[str, dict]:
        """
        Private method to download all available agents in the specific pool.
        Returns:
            dict: dict with agents names and properites
        Examples:
            >>> self.__get_all_agents()
                {"Agents_Name": {
                "id": 4,
                "pc_name": "LAB_BENCH_5521,
                "capabilities": {
                    "userCapabilities":{"hardware_available":true},
                    "systemCapabilities":{...,"Agent.Version":"4.255.0",...},
                    },
                "status": "online",
            },}
        """
        logger.debug("Downloading list of all available agents...")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools/{pool_id}/agents?api-version=7.1"
        response = requests.get(url, headers=self.__azure_api._headers())

        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.debug(f"Found {response.json()['count']} agents.")
        response_json = response.json()["value"]
        result = {}
        for agent in response_json:
            capabilities = self.get_agent_capabilities(agent.get("id"), by=AgentsBy.ID)
            result[agent.get("name")] = {
                "id": agent.get("id"),
                "pc_name": capabilities.get("systemCapabilities", {}).get("Agent.ComputerName"),
                "capabilities": capabilities,
                "status": agent.get("status"),
            }
        logger.success("Agents list updated.")
        return result

    def __resolve_agent_key(self, key: Union[str, int], by: AgentsBy) -> int:
        """
        As Azure Devops always uses unique Agent's ID it translates agents name or PC name to Unique ID based on
        database of agents.
        Args:
            key (str or int): key to search Agent. It can be ID, PC name or Agent's Name.
            by (AgentsBy): Type of key data.

        Returns:
            int: unique Agent's ID in the pool.

        Raises:
            KeyError: When key was not found in agent's database.
            AttributeError: When `by` is not recognised as AgentsBy object.
        """
        match by:
            case AgentsBy.ID:
                return key
            case AgentsBy.Agent_Name:
                _ = key
                key = self.__all_agents[key]["id"]
                logger.trace(f"Swapping {_} to {key}")
                return key
            case AgentsBy.PC_Name:
                for _, agent_data in self.__all_agents.items():
                    if agent_data.get("pc_name") == key:
                        _ = key
                        key = agent_data.get("id")
                        logger.trace(f"Swapping {_} to {key}")
                        return key
                    raise KeyError(f"{key} not found in all agents list.")
            case _:
                raise AttributeError(f"{by} is not recognised AgentsBy object.")

    @_require_valid_pool_name
    def get_agent_capabilities(self, key: Union[str, int], by: AgentsBy) -> dict:
        """
        Requests Azure Api to get Agent's User and System Capabilities.
        Args:
            key (str or int): key to search Agent. It can be ID, PC name or Agent's Name.
            by (AgentsBy): Type of key data.

        Returns:
            dict: dict with user and system capabilities

        Examples:
            >>> api = AzApi('org','pro','pat')
            >>> api.agent_pool_name = "pool"
            >>> capabilities = api.Agents.get_agent_capabilities("BENCH_LAB_1234", AgentsBy.PC_Name)
            >>> capabilities
            {"userCapabilities":{"hardware_available":true}
             "systemCapabilities":{...,"Agent.Version":"4.255.0",...}
             }
        """
        logger.info(f"Reading capabilities for agent: {key}...")
        key = self.__resolve_agent_key(key, by)
        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools/{self.__pool_id}/agents/{key}?includeCapabilities=true&api-version=7.2-preview.1"
        response = requests.get(url, headers=self.__azure_api._headers())
        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")

        response_json = response.json()
        return {
            "systemCapabilities": response_json.get("systemCapabilities"),
            "userCapabilities": response_json.get("userCapabilities"),
        }

    @_require_valid_pool_name
    def add_user_capabilities(self, key: Union[str, int], by: AgentsBy, capabilities: dict[str, str]) -> None:
        """
        Adds new user capabiblity to Agent's Settings.
        Args:
            key (str or int): key to search Agent. It can be ID, PC name or Agent's Name.
            by (AgentsBy): Type of key data.
            capabilities (dict): dict with key as name of capabilitiy and value as value

        Examples:
            >>> api = AzApi('org','pro','pat')
            >>> api.agent_pool_name = "pool"
            >>> capabilities = api.Agents.add_user_capabilities(2, AgentsBy.ID, {"hardware_ready":"true"})
        """
        logger.info(f"Adding capability: {capabilities} for agent: {key}...")
        key = self.__resolve_agent_key(key, by)
        agent_name, agent_data = None, None
        for tmp_agent_name, tmp_agent_data in self.__all_agents.items():
            if tmp_agent_data.get("id") == key:
                agent_name = tmp_agent_name
                agent_data = tmp_agent_data
                break
        if not agent_name:
            raise KeyError(f"{key} not found in all agents list.")

        new_capabilities = agent_data["capabilities"].get("userCapabilities", {})
        new_capabilities.update(capabilities)

        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools/{self.__pool_id}/agents/{key}/usercapabilities?api-version=5.0"
        response = requests.put(
            url, headers=self.__azure_api._headers("application/json"), data=json.dumps(new_capabilities)
        )

        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success("Capabilities modified.")
        self.__all_agents[agent_name]["capabilities"]["userCapabilities"] = new_capabilities

    @_require_valid_pool_name
    def remove_user_capabilities(self, key: Union[str, int], by: AgentsBy, capabilities: Union[str, list]) -> None:
        """
        Removes capability from user capabiblits to Agent's Settings.
        Args:
            key (str or int): key to search Agent. It can be ID, PC name or Agent's Name.
            by (AgentsBy): Type of key data.
            capabilities (str or list): names of capabilities to remove.

        Examples:
            >>> api = AzApi('org','pro','pat')
            >>> api.agent_pool_name = "pool"
            >>> capabilities = api.Agents.remove_user_capabilities(2, AgentsBy.ID, ["hardware_ready","agent_busy"]})
        """
        logger.info(f"Removing capability: {capabilities} for agent: {key}...")
        key = self.__resolve_agent_key(key, by)
        agent_name, agent_data = None, None
        for tmp_agent_name, tmp_agent_data in self.__all_agents.items():
            if tmp_agent_data.get("id") == key:
                agent_name = tmp_agent_name
                agent_data = tmp_agent_data
                break
        if not agent_name:
            raise KeyError(f"{key} not found in all agents list.")

        new_capabilities = agent_data["capabilities"].get("userCapabilities", {})
        if isinstance(capabilities, str):
            capabilities = [capabilities]
        for capability in capabilities:
            new_capabilities.pop(capability, None)

        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools/{self.__pool_id}/agents/{key}/usercapabilities?api-version=5.0"
        response = requests.put(
            url, headers=self.__azure_api._headers("application/json"), data=json.dumps(new_capabilities)
        )

        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success("Capabilities removed.")
        self.__all_agents[agent_name]["capabilities"]["userCapabilities"] = new_capabilities
