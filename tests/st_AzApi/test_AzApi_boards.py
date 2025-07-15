import os
from pathlib import Path

import pytest
from beartype.door import is_bearable
from dotenv import load_dotenv
from loguru import logger

from azapidevops.AzApi import AzApi
from azapidevops.utils.AzApi_boards import WorkItem, WorkItemsDef, WorkItemsStatesDef

try:
    env_path = Path(__file__).resolve().parent / "systemtest.env"
except NameError:
    env_path = "st_AzApi/systemtest.env"
load_dotenv(env_path)
ORG = os.getenv("ORGANIZATION")
PRO = os.getenv("PROJECT")
PAT = os.getenv("PAT")

USER_EMAIL = os.getenv("USER_EMAIL")
MAIN_BRANCH_NAME = os.getenv("MAIN_BRANCH_NAME")
TEST_TASK_NAME = "TEST_TASK"


@pytest.fixture(scope="function")
def create_test_testcase(request):
    self = request.instance
    id = self.api.Boards.create_new_item(work_item_type=WorkItemsDef.TestCase, item_name=TEST_TASK_NAME)
    yield id


@pytest.fixture(scope="function")
def create_test_task(request):
    self = request.instance
    id = self.api.Boards.create_new_item(work_item_type=WorkItemsDef.Task, item_name=TEST_TASK_NAME)
    yield id


@pytest.fixture
def remove_test_task(request):
    yield
    self = request.instance
    tasks = self.api.Boards.get_work_items(
        WorkItemsDef.Task, allowed_states=[WorkItemsStatesDef.Task.To_Do, WorkItemsStatesDef.Task.Doing]
    )
    for _, workitem in tasks.items():
        if workitem.title == TEST_TASK_NAME:
            logger.info(f"Removing test task {workitem.id}")
            self.api.Boards.change_work_item_state(workitem.id, WorkItemsStatesDef.Task.Done)


@pytest.fixture
def remove_test_testcase(request):
    yield
    self = request.instance
    tasks = self.api.Boards.get_work_items(
        WorkItemsDef.TestCase, allowed_states=[WorkItemsStatesDef.TestCase.Ready, WorkItemsStatesDef.TestCase.Design]
    )
    for _, workitem in tasks.items():
        if workitem.title == TEST_TASK_NAME:
            logger.info(f"Removing test TestCase {workitem.id}")
            self.api.Boards.change_work_item_state(workitem.id, WorkItemsStatesDef.TestCase.Closed)


class Tests_AzApi_boards:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = AzApi(ORG, PRO, PAT)

    def test_create_new_item_task(self, remove_test_task):
        self.api.Boards.create_new_item(work_item_type=WorkItemsDef.Task, item_name=TEST_TASK_NAME)
        tasks = self.api.Boards.get_work_items(type_of_workitem=WorkItemsDef.Task)
        assert any([workitem.title == TEST_TASK_NAME for id, workitem in tasks.items()]), "Test task was not created."

    def test_create_new_item_testcase(self, remove_test_testcase):
        self.api.Boards.create_new_item(work_item_type=WorkItemsDef.TestCase, item_name=TEST_TASK_NAME)
        testcases = self.api.Boards.get_work_items(type_of_workitem=WorkItemsDef.TestCase)
        assert any([workitem.title == TEST_TASK_NAME for id, workitem in testcases.items()]), (
            "Test TestCase was not created."
        )

    @pytest.mark.parametrize(
        "workitem_type, expected_state",
        [
            (WorkItemsDef.Task, WorkItemsStatesDef.Task.Doing),
            (WorkItemsDef.Task, WorkItemsStatesDef.Task.Done),
            (WorkItemsDef.Task, WorkItemsStatesDef.Task.To_Do),
            (WorkItemsDef.TestCase, WorkItemsStatesDef.TestCase.Ready),
            (WorkItemsDef.TestCase, WorkItemsStatesDef.TestCase.Closed),
            (WorkItemsDef.TestCase, WorkItemsStatesDef.TestCase.Design),
        ],
    )
    def test_change_work_item_state(
        self,
        create_test_testcase,
        create_test_task,
        remove_test_task,
        remove_test_testcase,
        workitem_type,
        expected_state,
    ):
        id = create_test_testcase if workitem_type == WorkItemsDef.TestCase else create_test_task
        self.api.Boards.change_work_item_state(id, expected_state)
        workitems_list = self.api.Boards.get_work_items(type_of_workitem=workitem_type, allowed_states=expected_state)
        assert any([workitem.title == TEST_TASK_NAME for id, workitem in workitems_list.items()]), (
            f"Work item {id} state was not found"
        )
        assert any([workitem.state == expected_state for id, workitem in workitems_list.items()]), (
            f"Work item {id} state was not changed to {expected_state}."
        )

    def test_get_work_items(self, create_test_testcase, create_test_task, remove_test_task, remove_test_testcase):
        tasks = self.api.Boards.get_work_items(
            WorkItemsDef.Task, allowed_states=[WorkItemsStatesDef.Task.To_Do, WorkItemsStatesDef.Task.Doing]
        )
        testcases = self.api.Boards.get_work_items(WorkItemsDef.TestCase)
        assert is_bearable(tasks, dict[int, WorkItem])
        assert is_bearable(testcases, dict[int, WorkItem])
