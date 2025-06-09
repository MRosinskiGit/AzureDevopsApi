import json
from enum import auto, Enum
from functools import wraps
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from AzApi.AzApi import AzApi
import requests


def _require_valid_pool_name(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        repo_name = getattr(self, "_AzRepos__repo_name", None)
        if not isinstance(repo_name, str) or not repo_name.strip():
            raise AttributeError("Invalid repository name: must be a non-empty string.")
        return method(self, *args, **kwargs)

    return wrapper


class AgentsBy(Enum):
    Agent_Name = auto()
    PC_Name = auto()
    ID = auto()


class _AzAgents:
    def __init__(self, api: "AzApi", pool_name):  # noqa: F821
        logger.info("Initializing AzApi Agents Tool.")
        self.__pool_name = pool_name
        self.__azure_api = api
        self.__all_pools = self.__get_all_pools()
        self.__pool_id = self.__all_pools.get(self.__pool_name)
        if self.__pool_id is None:
            logger.error("Pool name not detected in organization.")
            logger.debug(f"{self.__pool_name} not found in {self.__all_pools}.")
            raise NameError("Pool name not detected in organization.")
        self.__all_agents = self.__get_all_agents(self.__pool_id)
        logger.success("Agents Component initialized.")

    @property
    def all_agents(self):
        return self.__all_agents

    def __get_all_pools(self):
        logger.debug("Downloading list of all available pools...")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools?api-version=7.2-preview.1"
        response = requests.get(url, headers=self.__azure_api._headers())

        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.debug(f"Found {response.json()['count']} pools.")
        response_json = response.json()["value"]
        logger.success("Pools list updated.")
        return {pool.get("name"): pool.get("id") for pool in response_json}

    def __get_all_agents(self, pool_id):
        logger.debug("Downloading list of all available agents...")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools/{pool_id}/agents?api-version=7.1"
        response = requests.get(url, headers=self.__azure_api._headers())

        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
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

    def __resolve_agent_key(self, key, by: AgentsBy):
        match by:
            case AgentsBy.ID:
                return key
            case AgentsBy.Agent_Name:
                _ = key
                key = self.__all_agents[key]["id"]
                logger.trace(f"Swapping {_} to {key}")
                return key
            case AgentsBy.PC_Name:
                for agent, agent_data in self.__all_agents.items():
                    if agent_data.get("pc_name") == key:
                        _ = key
                        key = agent_data.get("id")
                        logger.trace(f"Swapping {_} to {key}")
                        return key
                    raise KeyError(f"{key} not found in all agents list.")
            case _:
                raise AttributeError(f"{by} is not recognised AgentsBy object.")

    @_require_valid_pool_name
    def get_agent_capabilities(self, key, by: AgentsBy) -> dict:
        logger.info(f"Reading capabilities for agent: {key}...")
        key = self.__resolve_agent_key(key, by)
        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools/{self.__pool_id}/agents/{key}?includeCapabilities=true&api-version=7.2-preview.1"
        response = requests.get(url, headers=self.__azure_api._headers())

        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")

        response_json = response.json()
        return {
            "systemCapabilities": response_json.get("systemCapabilities"),
            "userCapabilities": response_json.get("userCapabilities"),
        }

    @_require_valid_pool_name
    def add_user_capabilities(self, key, by, capabilities: dict):
        logger.info(f"Adding capability: {capabilities} for agent: {key}...")
        key = self.__resolve_agent_key(key, by)
        agent_name, agent_data = None, None
        for tmp_agent_name, tmp_agent_data in self.__all_agents.items():
            if tmp_agent_data.get("id") == key:
                agent_name = tmp_agent_name
                agent_data = tmp_agent_data
                break
        if agent_name is None:
            raise KeyError(f"{key} not found in all agents list.")

        new_capabilities = agent_data["capabilities"].get("userCapabilities", {})
        new_capabilities.update(capabilities)
        # TODO Update API version once clarified
        # url=f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools/{self.__pool_id}/agents/{key}?api-version=7.1"
        # payload = {"userCapabilities":capabilities}
        # response = requests.patch(            url,
        #     headers=self.__azure_api._headers("application/json"),
        #     data=json.dumps(payload))

        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/distributedtask/pools/{self.__pool_id}/agents/{key}/usercapabilities?api-version=5.0"
        response = requests.put(
            url, headers=self.__azure_api._headers("application/json"), data=json.dumps(new_capabilities)
        )

        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success("Capabilities modified.")
        self.__all_agents[agent_name]["capabilities"]["userCapabilities"] = new_capabilities
