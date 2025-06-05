# AzApi

**AzApi** is a complementary Python library designed to simplify and unify access to various Azure DevOps services via the REST API.

> **Status**: Beta – under active development

## Features

AzApi provides a modular, object-oriented interface to the most commonly used Azure DevOps services:

- `Boards` – work items, queries, iterations, and more
- `Repos` – repositories, branches, pull requests
- `Agents` – agent pools and agents management

## Requirements

- Python 3.11+
- A Personal Access Token (PAT) with appropriate Azure DevOps permissions
- Dependencies listed in `requirements.txt`

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/AzApi.git
cd AzApi
pip install -r requirements.txt
```

## Authentication

Authentication is handled via a Personal Access Token (PAT). You will need to provide the token when initializing the main API class.

## Usage

See the [`examples.py`](examples.py) file for practical usage of each module. Example:

```python
from AzApi.AzApi import AzApi 
api = AzApi(organization='ORG', project='PRO', token='PAT')
api.repository_name = 'REPO'
api.agent_pool_name = 'POOL'

task_id = api.Boards.create_new_item(
    WorkItemsDef.Task, item_name="Review Task", description="Review Task for Documentation"
)
api.Boards.change_work_item_state(task_id, WorkItemsStatesDef.Task.Done)
all_branches_list = api.Repo.get_all_branches()
prs = api.Repo.get_active_pull_requests()
pr_id = api.Repo.create_pr("Test PullRequest", "TestBranch", "main", "Testing API Request.")
api.Repo.add_pr_reviewer(pr_id, "user1@gmail.com")

```

## Testing

The repository includes both unit and integration tests, located in the `tests_azapi` folder.

To run all tests set working directory to main project dir and:

```bash
pytest .\tests_AzApi\
```


## License

This project is licensed under the [Apache License 2.0](LICENSE).
