import base64
from typing import Union, Dict

import requests
from loguru import logger

from .utils.AzApi_agents import _AzAgents
from .utils.AzApi_boards import _AzBoards
from .utils.AzApi_repos import _AzRepos


class AzApi:
    def __init__(self, organization: str, project: str, token: str):
        """
        Constructor for AzApi Tool.
        Args:
            organization (str): Azure's organization/owner name.
            project (str): Azure's Project name.
            token (str): Private Access Token for Azures Operations.
        """
        logger.info("Initializing AzApi Tool...")
        self.organization = organization
        self.project = project
        self.__b64_token = ...
        self.__token = ...
        self.token = token
        self.__users_data = ...

        # Components
        self.__repo_name: str = ...
        self.__Repos: _AzRepos = ...

        self.Boards = _AzBoards(self)

        self.__pool_name = ...
        self.__Agents: _AzAgents = ...

    @property
    def token(self) -> str:
        """
        Getter for current PAT. It output only part of token for security.
        Returns:
            str: Encoded PAT
        """
        return self.__token[:3] + "***" + self.__token[-3:]

    @token.setter
    def token(self, token: str) -> None:
        """
        Setter for PAT.
        Args:
            token (str): Private Access Token
        Raises:
             TypeError: if token is not a string type
        """
        if not isinstance(token, str):
            raise TypeError("Token is not a string object.")
        self.__token = token
        self.__b64_token = base64.b64encode(f":{self.__token}".encode()).decode()
        logger.success("Private Access Token is set.")

    class ComponentException(Exception):
        def __init__(self, msg="Component was not initiated."):
            super().__init__(msg)

    @property
    def repository_name(self) -> Union[str, Ellipsis]:
        """
        Getter for current repository name.
        Returns:
            str: Repository name
            of
            Ellipsis: if Repo name is not yet set.
        """
        return self.__repo_name

    @repository_name.setter
    def repository_name(self, name: str):
        """
        Setter for repository name. If repository name is valid it initiates constructor for AzRepos component.
        Args:
            name (str): Azures repository name.
        Raises:
            AttributeError: If `name` is not a string object or is empty string.
        """
        if not isinstance(name, str) or name == "":
            logger.error(f"{name} is not a valid repository name.")
            raise AttributeError("Invalid repository name: must be a non-empty string.")
        self.__repo_name = name
        self.__Repos = _AzRepos(self, self.__repo_name)

    @property
    def Repos(self) -> _AzRepos:
        """
        Getter for AzRepos component.
        Returns:
            _AzRepos: AzRepos instance.
        Raises:
            AzApi.ComponentException: When component is not initiated.
        """
        if self.__Repos is Ellipsis:
            raise AzApi.ComponentException(
                "Repository Component was not initiated. Please set `repository name` attribute."
            )
        return self.__Repos

    @property
    def agent_pool_name(self) -> Union[str, Ellipsis]:
        """
        Getter for current agent's pool name.
        Returns:
            str: Name of Agent's Pool
            of
            Ellipsis: if agent pool name is not yet set.
        """
        return self.__pool_name

    @agent_pool_name.setter
    def agent_pool_name(self, pool_name: str):
        """
        Setter for Agent's Pool name. If Pool name is valid it initiates constructor for AzRepos component.
        Args:
            pool_name (str): Agent's pool name
        Raises:
            AttributeError: If `pool_name` is not a string object or is empty string.
        """
        if not isinstance(pool_name, str) or not pool_name.strip():
            logger.error(f"{pool_name} is not a valid pool name.")
            raise AttributeError("Invalid pool name: must be a non-empty string.")
        self.__pool_name = pool_name
        self.__Agents = _AzAgents(self, pool_name)

    @property
    def Agents(self) -> _AzAgents:
        """
        Getter for AzAgents component.
        Returns:
            _AzAgents: AzAgents instance.
        Raises:
            AzApi.ComponentException: When component is not initiated.
        """
        if self.__Agents is Ellipsis:
            raise AzApi.ComponentException(
                "AzAgents Component was not initiated. Please set `agent_pool_name` attribute."
            )
        return self.__Agents

    def _headers(self, content_type: str = "application/json-patch+json") -> dict:
        """
        Private method to generate REST header with authentication method and provided data structure.
        Args:
            content_type (str): application/json-patch+json or application/json
        Returns:
            dict: dict ready for requests library.
        """
        return {
            "Content-Type": content_type,
            "Authorization": f"Basic {self.__b64_token}",
        }

    def __get_list_of_all_org_users(self) -> Dict[str, dict]:
        """
        Private method to download all organization's user's accounts data.
        Returns:
           Dict[str, dict]: Dict with all accounts data sorted with account's email as key.
        Example:
            >>> self.__get_list_of_all_org_users()
            {"user1@gmail.com": {... "principalName":"user1@gmail.com","mailAddress":"user1@gmail.com","origin":"msa","originId":"00034001089CAF73" ...},
            {"user2@gmail.com": {... "principalName":"user2@gmail.com","mailAddress":"user2@gmail.com","origin":"msa","originId":"00034001089CAF74" ...}}
        """  # noqa: E501
        url = f"https://vssps.dev.azure.com/{self.organization}/_apis/graph/users?api-version=7.2-preview.1"
        response = requests.get(url, headers=self._headers())
        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
        all_data_dict = {}
        for user in response.json()["value"]:
            if user.get("mailAddress"):
                all_data_dict.update({user.get("mailAddress").lower(): user})
        logger.debug(f"Downloading data... Currently downloaded: {len(all_data_dict)} records.")
        continuation_token = response.headers.get("x-ms-continuationtoken")
        logger.trace(f"Next page token: {continuation_token}")

        while continuation_token:
            url = f"https://vssps.dev.azure.com/SW4ZF/_apis/graph/users?api-version=7.2-preview.1&continuationToken={continuation_token}"
            response = requests.get(url, headers=self._headers())
            if response.status_code != 200:
                logger.error(f"Connection error: {response.status_code}")
                logger.debug(f"Error message: {response.text}")
                raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")

            for user in response.json()["value"]:
                if user.get("mailAddress"):
                    all_data_dict.update({user.get("mailAddress").lower(): user})
            logger.debug(f"Downloading data... Currently downloaded:{len(all_data_dict)}")
            continuation_token = response.headers.get("x-ms-continuationtoken")
            logger.debug(f"Next page token: {continuation_token}")
        logger.success("No continuation token — Download complete.")
        return all_data_dict

    def search_user_aad_descriptor_by_email(self, email: str) -> Union[str, None]:
        """
        Searches unique user's AAD identifier in the user's database. Descriptor is required to get unique Global User
        ID (GUID) for repository operations.
        Args:
            email: User's email.
        Returns:
            str: User's unique Azure Active Domain descriptor.
            or
            None: If email was not found in database.
        """
        logger.info(f"Searching Active Domain descriptor for email {email}")
        if self.__users_data is Ellipsis:
            logger.info("Users database empty. Downloading...")
            self.__users_data = self.__get_list_of_all_org_users()
        user = self.__users_data.get(email)
        if not user:
            logger.warning("User not found.")
            return None
        descriptor = user.get("descriptor")
        logger.success(f"Descriptor found: {descriptor}")
        return descriptor

    def get_guid_by_descriptor(self, descriptor: str) -> str:
        """
        Based on provided AAD Descriptor sends requests to get user's GUID (Global User ID).
        Args:
            descriptor (str): User's AAD Descriptor
        Returns:
            str: User's GUID
        Raises:
            requests.RequestException: When API Request was not successful.
        """
        logger.info(f"Reading GUID for descriptor {descriptor}")
        url = f"https://vssps.dev.azure.com/{self.organization}/_apis/graph/storageKeys/{descriptor}?api-version=7.2-preview.1"
        response = requests.get(url, headers=self._headers())
        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
        response = response.json()
        guid = response.get("value")
        logger.success(f"GUID found: {guid}")
        return guid
