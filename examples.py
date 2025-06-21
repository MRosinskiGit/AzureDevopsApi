import tempfile

from AzApi.AzApi import AzApi
from AzApi.utils.AzApi_agents import AgentsBy
from AzApi.utils.AzApi_boards import WorkItemsDef, WorkItemsStatesDef

# Examples:
## Init
api = AzApi(organization="ORGANIZATION_NAME", project="PROJECT_NAME", token="PAT")

## Init Repo Component
api.repository_name = "REPOSITORY_NAME"

## Init Agents Pool Component
api.agent_pool_name = "AGENT_POOL_NAME"


################################################### Boards Examples: ###################################################
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

## Get all work items of type Task
work_items = api.Boards.get_work_items(
    WorkItemsDef.Task, allowed_states=[WorkItemsStatesDef.Task.To_Do, WorkItemsStatesDef.Task.Doing]
)


################################################### Repos Examples: ####################################################
## Clone repository without history
api.Repos.clone_repository(tempfile.gettempdir(), branch="main", depth=1, submodules=True)

## Get list of all available branches
all_branches_list = api.Repos.get_all_branches()

## Check available pull requests
prs = api.Repos.get_active_pull_requests()

## Create Pull Request
pr_id = api.Repos.create_pr("Test PullRequest", "TestBranch", "main", "Testing API Request.")
## Add Reviewer to PR
api.Repos.add_pr_reviewer(pr_id, "user1@gmail.com")


################################################### Agents Examples: ###################################################
## Add Agents userCapabilies
api.Agents.add_user_capabilities("AgentLab", by=AgentsBy.Agent_Name, capabilities={"buildAvailable": "true"})
api.Agents.add_user_capabilities("Laboratory-123", by=AgentsBy.PC_Name, capabilities={"buildAvailable": "true"})
api.Agents.add_user_capabilities(1, by=AgentsBy.ID, capabilities={"buildAvailable": "true"})
