# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
### Added 
- Boards docs ✘
- Boards ut ✘
- Agents docs ✘
- Agents ut ✘
- System tests ✘
- Preparation for PyPi deploy ✘

### Changed
- Simplified `examples.py` ✘
- Split for prod dependencies and dev ones. ✘
- Modified README description ✘

### Removed
- .env template, not needed and user knows the best how he wants to use AzApi ✘


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
