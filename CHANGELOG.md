# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [Unreleased]
### Changed
- Clean up code for pylint analysis ✘
- Updated README with new features and usage examples ✘

## [0.0.3] - 17-07-2025
### Changed
- Extended logging to include more details about API requests and responses (Debug level) ✔

## [0.0.2] - 15-07-2025
### Added
- Repos: `get_active_pull_requests` now returns info about active reviewers ✔

### Changed
- Repos: `add_pr_reviewer` attribute `email` was changed to `user`. Method now supports adding reviewer by GUID and allows to set/change review status with `ReviewStateDef` enum.


## [0.0.2] - 15-07-2025
### Added
- Repos: `get_active_pull_requests` now returns info about active reviewers ✔

### Changed
- Repos: `add_pr_reviewer` attribute `email` was changed to `user`. Method now supports adding reviewer by GUID and allows to set/change review status with `ReviewStateDef` enum.

## [0.0.1] - 24-06-2025
### Added
- Boards: `get_work_items` method ✔
- System tests ✔
- Preparation for PyPi deploy ✔
### Changed
- Replaced loguru logging with standard logging module ✔
- Changed the newest release version to 0.0.1 for PyPi ✔
- Changed structure of AzApi to match the project convention ✔

## [1.2.4] - 19.06.2025
### Added
- Repos: `change_pr_status` method ✔
- AzApi: added connection verification ✔
- added `beartype` input parameters check ✔

## [1.2.3] - 12.06.2025
### Added
- Agents: `remove_user_capabilities` method ✔
- Repos: `delete_branch` method ✔
- System tests: Base - 100%, Agents - 100%, Repos - 70% ✔

## [1.2.2] - 10.06.2025
### Changed
- Retries on connection lost response 
- Modified README description

## [1.2.1] - 10.06.2025
### Added 
- Boards docs 
- Boards ut 
- Agents docs 
- Agents ut 

### Changed
- Simplified `examples.py` 
- Split for prod dependencies and dev ones. 

### Removed
- .env template, not needed and user knows the best how he wants to use AzApi 

## [1.2.0] - 9.06.2025
### Added
- Docstrings and full test coverage for AzApi Repos
- Batch script to run tests and generate coverage logs
- Exception raising when uninitiated component is used.

### Changed
- Added handling of downloading repository from custom url by keyword arg in `clone_repository` method.
- Changed Repo to Repos name component to match project convention.

### Fixed
- Fixed hardcoded email in AzApi class


## [0.1.1] - 
### Added
- Docstrings for AzApi

## [0.1.0] - 2025-06-06
### Added
- Created basic structure.
