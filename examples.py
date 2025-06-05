import os
import sys

from loguru import logger
from AzApi.AzApi import AzApi
from dotenv import load_dotenv
import tempfile

from AzApi.utils.AzApi_agents import AgentsBy
from AzApi.utils.AzApi_boards import WorkItemsDef, WorkItemsStatesDef

logger.remove()
logger.add(
    sys.stderr,
    level="TRACE",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
load_dotenv()

# Examples:
## Init
ORG = os.getenv("ORGANIZATION")
PRO = os.getenv("PROJECT")
PAT = os.getenv("PAT")
api = AzApi(organization=ORG, project=PRO, token=PAT)

## Init Repo Component
REPO = os.getenv("REPOSITORY")
api.repository_name = REPO

## Init Agents Pool Component
POOL = os.getenv("AGENT_POOL")
api.agent_pool_name = POOL

# Boards Examples:
## Create new Task and TestCase Objects in Boards
task_id = api.Boards.create_new_item(
    WorkItemsDef.Task, item_name="Review Task", description="Review Task for Documentation"
)
testcase_id = api.Boards.create_new_item(
    WorkItemsDef.TestCase, "Regression Tests", "Regression tests for API requests."
)

## Change States of created objects
api.Boards.change_work_item_state(task_id, WorkItemsStatesDef.Task.Done)
api.Boards.change_work_item_state(testcase_id, WorkItemsStatesDef.TestCase.Closed)


# Repo Examples:
## Clone repository without history
api.Repo.clone_repository(tempfile.gettempdir(), branch="main", depth=1, submodules=True)

## Get list of all available branches
all_branches_list = api.Repo.get_all_branches()

## Check available pull requests
prs = api.Repo.get_active_pull_requests()

## Create Pull Request
pr_id = api.Repo.create_pr("Test PullRequest", "TestBranch", "main", "Testing API Request.")
## Add Reviewer to PR
api.Repo.add_pr_reviewer(pr_id, "user1@gmail.com")

# Agents Examples:
## Add Agents userCapabilies
api.Agents.add_user_capabilities("AgentLab", by=AgentsBy.Agent_Name, capabilities={"buildAvailable": "true"})
api.Agents.add_user_capabilities("Laboratory-123", by=AgentsBy.PC_Name, capabilities={"buildAvailable": "true"})
api.Agents.add_user_capabilities(1, by=AgentsBy.ID, capabilities={"buildAvailable": "true"})
