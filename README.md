# taskpods: Parallel AI Task Pods via Git Worktrees

[![CI](https://github.com/yanairon/taskpods/workflows/CI/badge.svg)](https://github.com/yanairon/taskpods/actions)
[![Codecov](https://codecov.io/gh/yanairon/taskpods/branch/main/graph/badge.svg)](https://codecov.io/gh/yanairon/taskpods)
[![PyPI](https://img.shields.io/pypi/v/taskpods.svg)](https://pypi.org/project/taskpods/)
[![Python](https://img.shields.io/pypi/pyversions/taskpods.svg)](https://pypi.org/project/taskpods/)
[![License](https://img.shields.io/github/license/yanairon/taskpods.svg)](https://github.com/yanairon/taskpods/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`taskpods` is a tiny command‑line tool that lets you spawn disposable "AI pods" in your Git repository.  Each pod is its own worktree and branch, so you can run Copilot, Cursor, or Claude Code on isolated tasks without polluting your main branch.  When you're done, you can commit and push the work to a pull request or nuke the pod entirely.

## Features

- **Instant sandbox:** `taskpods start <name>` creates a new worktree under `.taskpods/<name>` and checks out a branch `pods/<name>` from a base branch (default `main`).
- **Clean exit:** `taskpods done <name>` stages, commits, and pushes everything in the pod, optionally opening a GitHub pull request via [`gh` CLI], then removes the worktree.
- **Abort button:** `taskpods abort <name>` deletes an unpushed pod and its branch without a trace.
- **Status overview:** `taskpods list` shows your active pods and where they live in the file system.
- **House‑keeping:** `taskpods prune` removes pods whose branches have been merged into their base branch.

## Installation

### Quick Install (Recommended)

Install from PyPI:

```bash
pip install taskpods
```

### Alternative Installation Methods

**From GitHub** (latest development version):

```bash
pip install git+https://github.com/yanairon/taskpods.git
```

**Manual installation**:

```bash
# Download and install manually
curl -O https://raw.githubusercontent.com/yanairon/taskpods/main/taskpods.py
chmod +x taskpods.py
sudo mv taskpods.py /usr/local/bin/taskpods
```

**Requirements**:

- Python 3.9+
- Git 2.5+ with worktree support
- A Git repository with a remote named `origin`

## Usage

### Create a new pod

```bash
taskpods start fix‑typos
```

This will:

1. Fetch the latest changes from `main` and fast‑forward your local `main`.
2. Create a new branch `pods/fix‑typos` from `main`.
3. Add a Git worktree at `.taskpods/fix‑typos`.
4. Drop you into a new editor window (Cursor if available, otherwise VS Code) with the worktree opened.

### Finish a pod and create a pull request

```bash
taskpods done fix‑typos -m "Fix docs typos" --remove
```

This will stage and commit all changes in the worktree with the given message, push the branch to `origin`, open a pull request via the [`gh` CLI] (if installed), and remove the worktree.  The branch remains so you can still interact with the PR.

### Abort a pod

```bash
taskpods abort fix‑typos
```

If the branch hasn't been pushed to `origin`, this will delete the worktree and local branch.  It refuses to abort pods whose branches are already on `origin` to avoid data loss.

### List active pods

```bash
taskpods list
```

Lists all worktrees under `.taskpods`, showing the pod name, branch, and path.

### Prune merged pods

```bash
taskpods prune
```

Finds pods whose remote branches are fully merged into their base branch and removes their worktrees.

## Requirements

- **Python 3.9+** – This script uses only the standard library.
- **Git** – You need Git installed with worktree support (Git 2.5+).  The repository must already be initialised with a remote named `origin`.
- **Editor (optional)** – The script will try to open your preferred editor. You can configure it via:
  - Environment variable: `export TASKPODS_EDITOR="vim"`
  - Configuration file: `~/.taskpodsrc`
  - Command line: `taskpods start my-feature --editor vim`
  - Auto-detection: Falls back to common editors if none configured
- **`gh` CLI (optional)** – If installed, `taskpods done` will automatically open a GitHub pull request.  Otherwise, it simply pushes the branch and prints a success message.

## Editor Configuration

### Environment Variable
```bash
export TASKPODS_EDITOR="vim"
export TASKPODS_EDITOR="code"
export TASKPODS_EDITOR="cursor"
```

### Configuration File
Create `~/.taskpodsrc`:
```json
{
  "editor": "vim",
  "default_base": "main"
}
```

### Command Line
```bash
taskpods start my-feature --editor vim
taskpods start my-feature --editor code
taskpods start my-feature --editor cursor
```

### Supported Editors
- **Modern**: Cursor, VS Code, Sublime Text, Atom
- **Terminal**: Vim, Neovim, Emacs
- **Custom**: Any editor available in your PATH

## Support

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X51K73WN)

## License

This project is released under the MIT License.  See the [LICENSE](LICENSE) file for details.

---

### Why worktrees?

Git worktrees let you have multiple branches checked out in separate directories without duplicating your entire `.git` object store.  They're faster than clones, don't waste disk space, and make cleanup trivial.  `taskpods` wraps a handful of `git worktree` commands with sensible defaults and adds quality‑of‑life features like automatic PR creation and safe aborts.

### DISCLAIMER

This tool is provided "as is" with no warranty.  It writes to your Git repository and could potentially cause data loss if used incorrectly.  Read the code, use it at your own risk, and always back up anything important before experimenting.

---

## Development

*For contributors and developers:*

### Setting up the development environment

```bash
git clone https://github.com/yanairon/taskpods.git
cd taskpods
pip install -e ".[dev]"
pre-commit install
```

### Running tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run all quality checks
make check
```

### Code quality

The project uses several tools to maintain code quality:

- **Black** - Code formatting
- **Flake8** - Linting
- **MyPy** - Type checking
- **Pre-commit** - Automated quality checks

Run `make format` to format code and `make lint` to check for issues.

## Contributing

Contributions, bug reports, and feature requests are welcome!  Feel free to open an issue or submit a pull request.
