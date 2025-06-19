import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from functools import wraps
from http import HTTPStatus
from typing import TYPE_CHECKING, Dict, Optional, Union

from loguru import logger
from requests.exceptions import RequestException

from .http_client import requests

if TYPE_CHECKING:
    from AzApi.AzApi import AzApi


def _require_valid_repo_name(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        repo_name = getattr(self, "_AzRepos__repo_name", None)
        if not isinstance(repo_name, str) or repo_name == "":
            raise AttributeError("Invalid repository name: must be a non-empty string.")
        return method(self, *args, **kwargs)

    return wrapper


class PrStatusesDef(str, Enum):
    Abandoned = "abandoned"
    Active = "active"
    Completed = "completed"


class _AzRepos:
    def __init__(self, api: "AzApi", repo_name):  # noqa: F821
        self.__repo_name = repo_name
        self.__azure_api = api
        logger.success("Repository Module initiated.")

    @_require_valid_repo_name
    def get_active_pull_requests(self, raw: bool = False) -> Union[Dict[str, dict], list]:
        """
        Gets all active Pull Requests in defined repository.
        Args:
            raw (bool): simplified or raw response. If true main key is ID of PR
        Returns:
            raw:
                list: list of dicts with parameters
            simplified:
                dict: json returned by endpoint, keys are PR IDs
        Examples:
            >>> api.Repos.get_active_pull_requests(raw=False)
            { 12: {
                "title": "Test Pullrequest",
                "url": "https://dev.azure.com/org/project/_git/repo/pullrequest/12",
                "creationDate": "2025-06-04T06:58:04.8778256Z",
                "sourceRefName": "refs/heads/testbranch",
                "targetRefName": "refs/heads/master"}}
        """
        logger.info("Downloading list of active Pull Requests...")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/git/repositories/{self.__repo_name}/pullrequests?api-version=7.1"
        response = requests.get(url, headers=self.__azure_api._headers())
        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success("Response received.")

        response_json = response.json()
        logger.success(f"Detected {response_json['count']} active Pull Requests.")
        for pr_ix, pr_params in enumerate(response_json["value"], 1):
            logger.debug(f"\t{pr_ix}. \t{pr_params['title']} | ID: {pr_params['pullRequestId']}")
            logger.debug(f"\t\tFrom: {pr_params['sourceRefName']} to {pr_params['targetRefName']}")
        if raw:
            return response_json["value"]
        return {
            pr_iter["pullRequestId"]: {
                "title": pr_iter["title"],
                "url": self.get_pullrequest_url(pr_iter["pullRequestId"]),
                "creationDate": pr_iter["creationDate"],
                "sourceRefName": pr_iter["sourceRefName"],
                "targetRefName": pr_iter["targetRefName"],
            }
            for pr_iter in response_json["value"]
        }

    @_require_valid_repo_name
    def create_pr(self, pr_title: str, source_branch: str, target_branch: str, description: Optional[str] = "") -> int:
        """
        Creates Pull Request for specific branch.
        Args:
            pr_title (str): Pull Request title.
            source_branch (str): Source branch name. Method accepts both namings with or without refs/heads.
            target_branch (str): Target branch name.
            description (Optional[str]): Description of pull request

        Returns:
            int: ID of created PR.
        Examples:
            >>> pr_id1 = api.Repos.create_pr("Test PullRequest1", "TestBranch", "main", "Testing API Request.")
            >>> pr_id2 = api.Repos.create_pr("Test PullRequest2", "refs/heads/branch2", "refs/heads/main", "Testing API Request.")
        """  # noqa: E501
        logger.info(f"Creating new PR: {pr_title}")
        if "refs/head" not in source_branch:
            source_branch = "refs/heads/" + source_branch
            logger.trace(f"Adding prefix to source branch name: {source_branch}")
        if "refs/head" not in target_branch:
            target_branch = "refs/heads/" + target_branch
            logger.trace(f"Adding prefix to target branch name: {target_branch}")

        active_prs = self.get_active_pull_requests()
        for pr_id, pr_data in active_prs.items():
            if pr_data.get("sourceRefName") == source_branch and pr_data.get("targetRefName") == target_branch:
                logger.warning("This pull request already exists.")
                return pr_id

        logger.debug(f"\t\tFrom: {source_branch} to {target_branch}")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/git/repositories/{self.__repo_name}/pullrequests?api-version=7.1"
        logger.trace(f"Requesting URL: {url}")
        payload = {
            "sourceRefName": source_branch,
            "targetRefName": target_branch,
            "title": pr_title,
            "description": description,
            "reviewers": [],
        }

        response = requests.post(url, json=payload, headers=self.__azure_api._headers("application/json"))
        if response.status_code != HTTPStatus.CREATED:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        pr_id = response.json()["pullRequestId"]
        logger.success(f"Response received. PR numer: {pr_id}")
        return pr_id

    @_require_valid_repo_name
    def get_all_branches(self, raw: bool = False) -> Union[Dict[str, dict], list]:
        """
        Reads all existing branches on the repo.
        Args:
            raw (bool): simplified or raw response.

        Returns:
            raw:
                list: list of dicts
            simplified:
                dict: keys are branch names.

        Examples:
            >>> api.Repos.get_all_branches(raw = False)
            {"refs/heads/master": {"creator": "NameUser SurnameUser"}}
        """
        logger.info("Reading list of all branches...")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/git/repositories/{self.__repo_name}/refs?filter=heads/&api-version=7.1"
        response = requests.get(url, headers=self.__azure_api._headers())
        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success("Response received.")
        for index, branch in enumerate(response.json()["value"], 1):
            logger.debug(f"\t\t{index}:\t {branch['name']}")
        if raw:
            return response.json()["value"]
        return {
            branch_iter["name"]: {
                "creator": branch_iter["creator"]["displayName"],
                "objectId": branch_iter.get("objectId"),
            }
            for branch_iter in response.json()["value"]
        }

    @_require_valid_repo_name
    def get_pullrequest_url(self, pr_id: int) -> str:
        """
        Generates direct URL to Pull Request based on ID.
        Args:
            pr_id (int): ID of Pull request to generate url.

        Returns:
            str: url link to PR.
        """
        return f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_git/{self.__repo_name}/pullrequest/{pr_id}"

    def clone_repository(
        self,
        output_dir: str,
        submodules: bool = False,
        depth: Optional[int] = None,
        branch: Optional[str] = None,
        **kwargs,
    ) -> str | None:
        """
        Downloads repository to defined output directory.
        Args:
            output_dir (str): path to output dir.
            submodules (bool): flag to mark if submodules also should be downloaded
            depth (Optional[int]): depth of downloaded history of modifications on repository
            branch (Optional[str]): name of branch to download if different from default
            **kwargs:
                custom_url (Optional[str]): link to different repository then defined in parent AzApi class.
        Returns:
            str: Path to repository dir.
            or
            None: When directory to cloned repo was not found in output.
        """
        custom_url = kwargs.get("custom_url")
        repo_log_name = custom_url if custom_url is not None else self.__repo_name
        logger.info(f"Cloning repository {repo_log_name}...")
        logger.trace(f"\tOutput directory: {output_dir}, Depth {depth}, Branch: {branch}")
        git_url_std = f"https://{self.__azure_api.organization}@dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_git/{self.__repo_name}"  # noqa: E501
        repo_url = custom_url if custom_url else git_url_std
        command = ["git", "clone", repo_url]
        if submodules:
            command.extend(["--recurse-submodules", "--shallow-submodules"])
        if branch:
            command.extend(["--branch", branch])
        if depth:
            command.extend(["--depth", str(depth)])
        env = os.environ.copy()

        proc = subprocess.Popen(
            command,
            cwd=output_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        def __thread_pool_stream_reader(stream, log_function):
            for line in iter(stream.readline, ""):
                log_function(line.rstrip())
            stream.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(__thread_pool_stream_reader, proc.stdout, logger.info)
            logger.debug("Reading stdout initialized...")
            executor.submit(__thread_pool_stream_reader, proc.stderr, logger.debug)
            logger.debug("Reading stderr initialized...")

        if proc.wait() != 0:
            logger.error(f"Error on cloning - Return code {proc.wait()}")
            raise RuntimeError
        logger.success("Cloning finished.")
        try:
            proc.terminate()
            proc.wait(timeout=5)
            logger.success("Cloning process terminated.")
        except subprocess.TimeoutExpired:
            logger.warning("Terminate timed out. Killing process.")
            proc.kill()
            proc.wait()

        url_splitted = repo_url.split(sep="/")
        last_part = url_splitted[-1].lower().replace(".git", "")
        try:
            matched_dirs = [directory for directory in os.listdir(output_dir) if directory.lower() == last_part]
            if matched_dirs:
                return os.path.join(output_dir, matched_dirs[0])
        except FileNotFoundError:
            pass
        logger.warning("Directory not found.")

    @_require_valid_repo_name
    def add_pr_reviewer(self, pr_id: int, email: str):
        """
        Adds reviewer to Pull Request.
        Args:
            pr_id (int): ID of pull request
            email (str): mail of the reviewer.
        """
        logger.info(f"Adding User {email} to PR{pr_id}")
        descriptor = self.__azure_api.search_user_aad_descriptor_by_email(email)
        guid = self.__azure_api.get_guid_by_descriptor(descriptor)
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/git/repositories/{self.__repo_name}/pullRequests/{pr_id}/reviewers/{guid}?api-version=7.2-preview.1"
        payload = {
            "id": guid,
            "vote": 0,
        }
        response = requests.put(url, json=payload, headers=self.__azure_api._headers("application/json"))
        if response.status_code not in [200, 201]:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success(f"Response: {response.status_code}, User added as reviewer.")

    @_require_valid_repo_name
    def delete_branch(self, branch_name: str):
        """
        Deletes branch from repository. Accepts naming convention with refs/heads or just branch name.
        Args:
            branch_name: string with branch name
        """
        logger.info(f"Deleting {branch_name}")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/git/repositories/{self.__repo_name}/refs?api-version=7.2-preview.2"
        if not branch_name.startswith("refs/heads/"):
            branch_name = "refs/heads/" + branch_name
            logger.debug("Adding refs/heads/ to branch name.")
        all_branches = self.get_all_branches()
        branch_to_delete = all_branches.get(branch_name)
        if branch_to_delete is None:
            msg = f"Branch {branch_name} not found. Available branches: {all_branches.keys()}"
            logger.error(msg)
            raise KeyError(msg)

        payload = [
            {
                "name": branch_name,
                "oldObjectId": branch_to_delete.get("objectId"),
                "newObjectId": "0000000000000000000000000000000000000000",
            }
        ]
        response = requests.post(
            url=url, headers=self.__azure_api._headers("application/json"), data=json.dumps(payload)
        )
        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success("Branch deleted.")

    def change_pr_status(self, pr_id: int, status: PrStatusesDef):
        """
        Changes status of Pull Request.
        Args:
            pr_id (int): ID of pull request
            status (PrStatusesDef): new status of PR.
        """
        logger.info(f"Changing status of PR{pr_id} to {status}")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/git/repositories/{self.__repo_name}/pullRequests/{pr_id}?api-version=7.2-preview.1"
        payload = {
            "status": status,
        }
        response = requests.patch(url, json=payload, headers=self.__azure_api._headers("application/json"))
        if response.status_code != HTTPStatus.OK:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success(f"Response: {response.status_code}, PR status changed to {status}.")
