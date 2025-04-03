import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Union

import requests
from loguru import logger


def _require_valid_repo_name(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        repo_name = getattr(self, "_AzRepos__repo_name", None)
        if not isinstance(repo_name, str) or not repo_name.strip():
            raise AttributeError("Invalid repository name: must be a non-empty string.")
        return method(self, *args, **kwargs)

    return wrapper


class AzRepos:
    def __init__(self, api: "AzApi", repo_name):  # noqa: F821
        self.__repo_name = repo_name
        self.__azure_api = api

    @_require_valid_repo_name
    def get_active_pull_requests(self, raw=False):
        logger.info("Downloading list of active Pull Requests...")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/git/repositories/{self.__repo_name}/pullrequests?api-version=7.1"
        response = requests.get(url, headers=self.__azure_api._headers())
        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success("Response received.")

        response_json = response.json()
        logger.success(f"Detected {response_json['count']} active Pull Requests.")
        for pr_ix, pr_params in enumerate(response_json["value"], 1):
            logger.debug(f"\t{pr_ix}. \t{pr_params['title']}")
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
    def create_pr(self, pr_title, source_branch, target_branch, description="") -> Union[int, None]:
        logger.info(f"Creating new PR: {pr_title}")
        if "refs/head" not in source_branch:
            source_branch = "refs/heads/" + source_branch
            logger.trace(f"Adding prefix to source branch name: {source_branch}")
        if "refs/head" not in target_branch:
            target_branch = "refs/heads/" + target_branch
            logger.trace(f"Adding prefix to target branch name: {target_branch}")

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
        if response.status_code != 201:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")

        pr_id = response.json()["pullRequestId"]
        logger.success(f"Response received. PR numer: {pr_id}")
        return pr_id

    @_require_valid_repo_name
    def get_all_branches(self, raw=False):
        logger.info("Reading list of all branches...")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/git/repositories/{self.__repo_name}/refs?filter=heads/&api-version=7.1"
        response = requests.get(url, headers=self.__azure_api._headers())
        if response.status_code != 200:
            logger.error(f"Connection error: {response.status_code}")
            logger.debug(f"Error message: {response.text}")
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success("Response received.")
        for index, branch in enumerate(response.json()["value"], 1):
            logger.debug(f"\t\t{index}:\t {branch['name']}")
        if raw:
            return response.json()["value"]
        return {
            branch_iter["name"]: {"creator": branch_iter["creator"]["displayName"]}
            for branch_iter in response.json()["value"]
        }

    @_require_valid_repo_name
    def get_pullrequest_url(self, pr_id):
        return f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_git/{self.__repo_name}/pullrequest/{pr_id}"

    @_require_valid_repo_name
    def clone_repository(self, output_dir, depth=None, branch=None, submodules=False):
        logger.info(f"Cloning repository {self.__repo_name}")
        logger.trace(f"\tOutput directory: {output_dir}, Depth {depth}, Branch: {branch}")
        command = "git clone "
        git_url = f"https://{self.__azure_api.organization}@dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_git/{self.__repo_name}"

        command += f"{git_url} "
        if submodules:
            command += "--recurse-submodules --shallow-submodules "
        if branch:
            command += f"--branch {branch} "
        if depth:
            command += f"--depth {depth} "
        env = os.environ.copy()

        logger.debug("Clone repository")
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
            executor.submit(__thread_pool_stream_reader, proc.stderr, logger.trace)
            logger.debug("Reading stderr initialized...")

        logger.debug("Remove token configuration")
        subprocess.run("git config --global --unset-all http.https://SW4ZF@dev.azure.com/.extraHeader")

        if proc.wait() != 0:
            logger.error(f"Error on cloning - Return code {proc.wait()}")
            raise RuntimeError
        logger.success("Cloning finished.")
        try:
            proc.terminate()
            proc.wait(timeout=5)
            logger.success("Process terminated.")
        except subprocess.TimeoutExpired:
            logger.warning("Terminate timed out. Killing process.")
            proc.kill()
            proc.wait()