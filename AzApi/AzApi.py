import base64
from loguru import logger
from .utils.AzApi_repos import AzRepos


class AzApi:
    def __init__(self, organization: str, project: str, token: str):
        logger.info("Initializing AzApi Tool...")
        self.organization = organization
        self.project = project
        self.__b64_token = ...
        self.__token = ...
        self.token = token

        # Components
        self.__repo_name = ""
        self.Repo = AzRepos(self, self.__repo_name)

    @property
    def token(self):
        return self.__token[:3] + "***" + self.__token[-3:]

    @token.setter
    def token(self, token):
        if not isinstance(token, str):
            raise TypeError("Token is not a string object.")
        self.__token = token
        self.__b64_token = base64.b64encode(f":{self.__token}".encode()).decode()
        logger.success("Private Access Token is set.")

    @property
    def repository_name(self):
        return self.__repo_name

    @repository_name.setter
    def repository_name(self, name: str):
        if not isinstance(name, str) or not name.strip():
            logger.error(f"{name} is not a valid repository name.")
            raise AttributeError("Invalid repository name: must be a non-empty string.")
        self.__repo_name = name
        self.Repo = AzRepos(self, self.__repo_name)

    def _headers(self, content_type: str = "application/json-patch+json"):
        return {
            "Content-Type": content_type,
            "Authorization": f"Basic {self.__b64_token}",
        }

