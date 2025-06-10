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

    def create_new_item(
        self,
        work_item_type: WorkItemsDef,
        item_name: str,
        description: Optional[str] = None,
    ) -> int:
        """
        Creates a new item in Boards tab
        Args:
            work_item_type (WorkItemsDef): WorkItemsDef object to define type of Work Item.
            item_name (str): Item name
            description (Optional[str]): Description of Work Item.

        Returns:
            int: id of created object

        Examples:
            >>> api = AzApi("Org","Pro","PAT")
            >>> task_id = api.Boards.create_new_item(WorkItemsDef.TestCase,"TC")
        """
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

        if response.status_code != 200:
            logger.error(f"Failed to create work item. Status code: {response.status_code}")
            logger.debug(response.text)
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")

        logger.success("Work item created successfully.")
        logger.debug(response.json())
        return response.json()["id"]

    def change_work_item_state(self, work_item_id: int, state: WorkItemsStatesDef) -> None:
        """
        Changes current state of Work Item.

        Args:
            work_item_id (int): Unique ID of Work Item.
            state (WorkItemsStatesDef): Expected state of Work Item

        Examples:
            >>> api = AzApi("Org","Pro","PAT")
            >>> task_id = api.Boards.create_new_item(WorkItemsDef.TestCase,"TC")
            >>> api.Boards.change_work_item_state(task_id, WorkItemsStatesDef.TestCase.Ready)
        """
        logger.info(f"Changing work item state to {state}")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        data = [{"op": "add", "path": "/fields/System.State", "value": state}]
        response = requests.patch(url, headers=self.__azure_api._headers(), json=data)

        if response.status_code != 200:
            logger.error(f"Error: {response.status_code}")
            logger.debug(response.json())
            raise requests.RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.success(f"State of object changed to {state}.")
