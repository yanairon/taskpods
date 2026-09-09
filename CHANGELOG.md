# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-09-10

### Added

- `--agent` flag on `taskpods start`: run any AI coding agent (Claude Code,
  Codex CLI, Gemini CLI, opencode, aider, ...) inside the new pod, e.g.
  `taskpods start fix-typos --agent claude -p "fix the typos"`. The agent runs
  in the foreground in the pod's worktree and its exit code is propagated.
  Configurable via the `TASKPODS_AGENT` env var or the `agent` key in
  `~/.taskpodsrc`.
- Zed editor auto-detection.
- CI now also tests on Python 3.13.

### Fixed

- Running multiple pods in parallel: the `.taskpods/` pods directory is now
  added to `.git/info/exclude` automatically. Previously an active pod showed
  up as an untracked directory, which tripped the uncommitted-changes safety
  check and made `taskpods start` refuse to create a second pod.
- The `default_base` key in `~/.taskpodsrc` is now honored when `--base` is
  not passed (it was documented but ignored).

### Changed

- Minimum Python version is now 3.9, matching the README (3.7/3.8 are EOL).
- All development dependencies bumped to their latest releases (pytest 9.1,
  pytest-cov 7.1, black 26.5, flake8 7.3, mypy 2.3, coverage 7.16, bandit
  1.9, build 1.6, twine 7.0, and friends), and the pre-commit hooks updated
  (pre-commit-hooks v6, black 26.5.1, flake8 7.3.0, mypy v2.3.1, isort 9.0.1).
- Lint and release workflows now run on Python 3.13.

## [0.2.0] - 2025-08-24

### Added
- Release 0.2.0


## [0.3.0] - 2025-08-24

### Added
- Release 0.3.0


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

## [0.4.0] - 2026-09-10

### Added

- Future features and improvements

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
