# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-08-24

### Added
- Release 0.2.0


## [Unreleased]

### Added

- Production-grade GitHub repository configuration
- Comprehensive CI/CD workflow with testing, linting, and security checks
- Automated release workflow for PyPI publishing and GitHub releases
- Pull request and issue templates for better contribution experience
- Enhanced security policy and contributing guidelines
- Code quality badges and comprehensive documentation
- Enhanced development dependencies including security tools (bandit, safety)
- Parallel testing support with pytest-xdist
- Comprehensive Makefile with production commands
- Enhanced .gitignore for production environments
- Comprehensive input validation for pod names and base branches
- Enhanced error handling with clear, actionable error messages
- Git operation safety checks (merge/rebase/cherry-pick in progress)
- Worktree integrity validation
- User confirmation prompts for destructive operations
- Comprehensive test suite with mocking support
- Modern Python packaging with pyproject.toml

### Changed

- Replaced setup.py with modern pyproject.toml
- Improved error messages and user feedback
- Enhanced code organization and function design
- Better Git operation safety and validation

### Fixed

- Critical syntax error in `remote_branch_exists` function
- Global variable initialization failure causing immediate crashes
- Poor error handling for Git operations
- Missing validation for user inputs
- Inadequate testing coverage

### Security

- Input sanitization for pod names
- Path validation to prevent directory traversal
- Git repository isolation improvements

## [0.1.0] - 2024-01-XX

### Added

- Initial release of taskpods
- Basic worktree management functionality
- Support for creating, finishing, and aborting pods
- GitHub CLI integration for pull requests
- Editor integration (Cursor, VS Code)

### Features

- `taskpods start <name>` - Create new pod worktree
- `taskpods done <name>` - Commit, push, and optionally create PR
- `taskpods abort <name>` - Safely delete unpushed pods
- `taskpods list` - List active pods
- `taskpods prune` - Remove merged pods
