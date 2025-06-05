import json

import requests
from loguru import logger

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from AzApi.AzApi import AzApi


class WorkItemsDef:
    Task = "Task"
    TestCase = "Test Case"


class WorkItemsStatesDef:
    class Task:
        To_Do = "To Do"
        Doing = "Doing"
        Done = "Done"

    class TestCase:
        Design = "Design"
        Ready = "Ready"
        Closed = "Closed"


class _AzBoards:
    def __init__(self, api: "AzApi"):  # noqa: F821
        self.__azure_api = api

    def get_all_items(self, raw=False):
        pass

    def create_new_item(
        self,
        work_item_type: WorkItemsDef,
        item_name,
        description: Optional[str] = None,
    ) -> int:
        logger.info(f"Creating new item in Boards: {item_name} as {work_item_type}")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
        payload = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": f"{item_name}",
            }
        ]
        if description:
            payload.append(
                {
                    "op": "add",
                    "path": "/fields/System.Description",
                    "value": f"{description}",
                }
            )

        response = requests.post(url, headers=self.__azure_api._headers(), data=json.dumps(payload))

        if response.status_code == 200:
            logger.success("Work item created successfully.")
            logger.debug(response.json())
            return response.json()["id"]

        else:
            logger.error(f"Failed to create work item. Status code: {response.status_code}")
            logger.debug(response.text)
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")

    def change_work_item_state(self, work_item_id: int, state: WorkItemsStatesDef) -> None:
        logger.info(f"Changing work item state to {state}")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        data = [{"op": "add", "path": "/fields/System.State", "value": state}]
        response = requests.patch(url, headers=self.__azure_api._headers(), json=data)

        if response.status_code == 200:
            logger.success(f"State of object changed to {state}.")
        else:
            logger.error(f"Error: {response.status_code}")
            logger.debug(response.json())
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
