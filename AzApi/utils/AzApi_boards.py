import datetime
import json
import logging
from enum import Enum
from http import HTTPStatus
from typing import TYPE_CHECKING, Optional, Union

from pydantic import BaseModel, EmailStr
from requests.exceptions import RequestException

try:
    from .http_client import requests
except ImportError:
    from AzApi.utils.http_client import requests

if TYPE_CHECKING:
    from AzApi.AzApi import AzApi
logger = logging.getLogger(__name__)


class WorkItemsDef(str, Enum):
    """Defines available work item types in Azure Boards."""

    Task = "Task"
    TestCase = "Test Case"


class WorkItemsStatesDef:
    """Container for enums representing possible states for each work item type."""

    class Task(str, Enum):
        """Possible states for Task work items."""

        To_Do = "To Do"
        Doing = "Doing"
        Done = "Done"

    class TestCase(str, Enum):
        """Possible states for Test Case work items."""

        Design = "Design"
        Ready = "Ready"
        Closed = "Closed"


class WorkItem(BaseModel):
    """Represents a single work item retrieved from Azure Boards.

    Attributes:
        id (int): Unique identifier of the work item.
        title (str): Title of the work item.
        state (Union[WorkItemsStatesDef.Task, WorkItemsStatesDef.TestCase]): Current state of the work item.
        creation_date (datetime.datetime): Date and time when the work item was created.
        created_by (str): Email of the creator account.
    """

    id: int
    title: str
    state: Union[WorkItemsStatesDef.Task, WorkItemsStatesDef.TestCase]
    creation_date: datetime.datetime
    created_by: EmailStr


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

        Raises:
            RequestException: If the API request fails or returns a non-OK status code.

        Examples:
            >>> api = AzApi("Org","Pro","PAT")
            >>> task_id = api.Boards.create_new_item(WorkItemsDef.TestCase,"TC")
        """
        logger.info(f"Creating new item in Boards: {item_name} as {work_item_type}")
        url = f"https://dev.azure.com/{self.__azure_api.organization}/{self.__azure_api.project}/_apis/wit/workitems/${work_item_type.value}?api-version=7.1"
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
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")

        logger.info("SUCCESS: Work item created successfully.")
        return response.json()["id"]

    def change_work_item_state(self, work_item_id: int, state: WorkItemsStatesDef) -> None:
        """
        Changes current state of Work Item.

        Args:
            work_item_id (int): Unique ID of Work Item.
            state (WorkItemsStatesDef): Expected state of Work Item

        Raises:
            RequestException: If the API request fails or returns a non-OK status code.

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
            raise RequestException(f"Response Error. Status Code: {response.status_code}.")
        logger.info(f"SUCCESS: State of object changed to {state}.")

    def get_work_items(self, type_of_workitem: WorkItemsDef, **kwargs) -> dict[int, WorkItem]:
        """
        Retrieves work items of a given type and state(s) from Azure DevOps Boards.

        Args:
            type_of_workitem (WorkItemsDef): The type of work item to retrieve (e.g., Task, Test Case).
            kwargs: Additional keyword arguments to filter work items.
                allowed_states (Union[list[WorkItemsStatesDef], WorkItemsStatesDef]): Allowed state or list of states to
                filter work items.

        Returns:
            dict[int, WorkItem]: A dictionary mapping work item IDs to their corresponding WorkItem objects.

        Raises:
            RequestException: If the API request fails or returns a non-OK status code.

        Example:
            >>> api = AzApi("Org", "Pro", "PAT")
            >>> items = api.Boards.get_work_items(type_of_workitem=WorkItemsDef.Task,
            >>>        allowed_states=[WorkItemsStatesDef.Task.To_Do, WorkItemsStatesDef.Task.Doing])
        """
        logger.info(
            f"Retrieving work items of type {type_of_workitem} with states {kwargs.get('allowed_states', 'all')}"
        )
        states_wiql = None
        if allowed_states := kwargs.get("allowed_states"):
            if isinstance(allowed_states, list):
                states_wiql = " OR ".join(f"[State] = '{state.value}'" for state in allowed_states)
            else:
                states_wiql = f"[State] = '{allowed_states.value}'"

        wiql = (
            f"Select [System.Id], [System.Title], [System.State], [System.CreatedDate], [System.CreatedBy] "
            f"From WorkItems "
            f"Where [System.WorkItemType] = '{type_of_workitem.value}' "
        )

        wiql += "" if not states_wiql else f"AND {states_wiql} "

        wiql += "order by [System.CreatedDate] desc, [Microsoft.VSTS.Common.Priority] asc"
        query = {"query": wiql}

        url = f"https://dev.azure.com/{self.__azure_api.organization}/_apis/wit/wiql?api-version=7.1"
        response = requests.post(url=url, data=json.dumps(query), headers=self.__azure_api._headers("application/json"))
        logger.debug(f"WIQL Query: {wiql}")

        if response.status_code != HTTPStatus.OK:
            logger.error(f"Failed to retrieve work items. Status code: {response.status_code}")

            raise RequestException(f"Response Error. Status Code: {response.status_code}.")

        ids = [item["id"] for item in response.json()["workItems"]]
        if not ids:
            return {}
        ids_str = ",".join(map(str, ids))
        params_to_read = ",".join(
            ["System.Id", "System.Title", "System.State", "System.CreatedBy", "System.CreatedDate"]
        )
        details_url = (
            f"https://dev.azure.com/{self.__azure_api.organization}/_apis/wit/workitems"
            f"?ids={ids_str}&fields={params_to_read}&api-version=7.1"
        )
        logger.debug(f"Details URL: {details_url}")
        details_response = requests.get(details_url, headers=self.__azure_api._headers())

        if details_response.status_code != HTTPStatus.OK:
            logger.error(f"Failed to retrieve work item details. Status code: {details_response.status_code}")
            raise RequestException(f"Response Error. Status Code: {details_response.status_code}.")

        work_items = {}
        for item in details_response.json()["value"]:
            try:
                work_items[item["id"]] = WorkItem(
                    id=item["id"],
                    title=item["fields"]["System.Title"],
                    state=item["fields"]["System.State"],
                    creation_date=datetime.datetime.fromisoformat(
                        item["fields"]["System.CreatedDate"].replace("Z", "+00:00")
                    ),
                    created_by=item["fields"]["System.CreatedBy"]["uniqueName"],
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"Failed to parse work item {item['id']}. Skipping.")
        logger.info(
            f"Retrieved {len(work_items)} work items of type {type_of_workitem} "
            f"with states {kwargs.get('allowed_states', 'all')}."
        )
        logger.debug(work_items)
        return work_items
