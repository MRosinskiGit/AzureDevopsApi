# AzApi

**AzApi** is a complementary Python library designed to simplify and unify access to various Azure DevOps services via the REST API.

> **Status**: Early development stage, not all features are implemented yet. The library is under active development and new features are being added regularly.

Current progress and expected features are described in [`CHANGELOG.md`](CHANGELOG.md) on the repository.
All progress can be tracked on the [GitHub repository](https://github.com/MRosinskiGit/AzureDevopsApi).

## Features

AzApi provides a modular, object-oriented interface to the most commonly used Azure DevOps services with logger support:

- `Boards` – work items, queries, iterations, and more
- `Repos` – repositories, branches, pull requests
- `Agents` – agent pools and agents management

## Requirements

- Tested on Python 3.11 and above, lower versions may work but are not guaranteed
- A Personal Access Token (PAT) with appropriate Azure DevOps permissions

## Installation

Clone the repository:

```bash
git clone https://github.com/MRosinskiGit/AzureDevopsApi.git
```
and install dependencies from [pyproject.toml](pyproject.toml) or from [requirements.txt](requirements.txt):

or install directly from PyPi:

```bash
pip install azapidevops
```
## Authentication

Authentication is handled via a Personal Access Token (PAT). You will need to provide the token when initializing the main API class and pass it to AzApi class as `token` attribute.

## Usage

See the [`examples.py`](examples.py)  file on the repository for practical usage of each module. Short example:

```python
from azapidevops.AzApi import AzApi
from azapidevops.utils.AzApi_boards import WorkItemsDef, WorkItemsStatesDef

api = AzApi(organization="ORGANIZATION_NAME", project="PROJECT_NAME", token="PAT")
api.repository_name = 'REPO_NAME'
api.agent_pool_name = 'POOL_NAME'

task_id = api.Boards.create_new_item(
    WorkItemsDef.Task, item_name="Review Task", description="Review Task for Documentation"
)
api.Boards.change_work_item_state(task_id, WorkItemsStatesDef.Task.Done)
all_branches_list = api.Repos.get_all_branches()
prs = api.Repos.get_active_pull_requests()
pr_id = api.Repos.create_pr("Test PullRequest", "TestBranch", "main", "Testing API Request.")
api.Repos.add_pr_reviewer(pr_id, "user1@gmail.com")

```
## Logging
AzApi supports logging via the standard Python `logging` module. You can configure the logger to output to a file or console as needed. The library provides detailed logs for API requests and responses, which can be useful for debugging.

## Testing

The repository includes both unit and integration tests, located in the `ut_AzApi` folder and system tests in `st_AzApi` directory. System tests require `systemtest.env` with environment variables for Azure DevOps connection (example with required parameters in [systemtest.env.template](tests/st_AzApi/systemtest.env.template))

For testing install production dependencies:
```bash
pip install -r requirements.txt
```
To run all tests set working directory to main project dir and run:

```bash
pytest 
```

or open terminal in `tools` as cwd directory and run `./run_test.bat` for full unit and system test report with coverage logs.


## License

This project is licensed under the [Apache License 2.0](LICENSE).
