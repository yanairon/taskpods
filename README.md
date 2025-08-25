# taskpods: Parallel AI Task Pods via Git Worktrees

[![CI](https://github.com/yanairon/taskpods/workflows/CI/badge.svg)](https://github.com/yanairon/taskpods/actions)
[![Codecov](https://codecov.io/gh/yanairon/taskpods/branch/main/graph/badge.svg)](https://codecov.io/gh/yanairon/taskpods)
[![PyPI](https://img.shields.io/pypi/v/taskpods.svg)](https://pypi.org/project/taskpods/)
[![Python](https://img.shields.io/pypi/pyversions/taskpods.svg)](https://pypi.org/project/taskpods/)
[![License](https://img.shields.io/github/license/yanairon/taskpods.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)  
[![GitHub Sponsors](https://img.shields.io/badge/sponsor-%F0%9F%A7%91%E2%80%8D%F0%9F%92%BB-ff69b4)](https://github.com/sponsors/yanairon)
[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X51K73WN)

---

`taskpods` is a lightweight CLI that lets you spin up disposable **AI pods** inside your Git repo.  
Each pod is an isolated Git worktree/branch — perfect for experimenting with Copilot, Cursor, or Claude Code without polluting `main`.  
When done, you can merge, PR, or nuke the pod entirely.

---

## ✨ Features

- **Instant sandbox:** `taskpods start <name>` → creates `.taskpods/<name>` and `pods/<name>` from `main`.  
- **Clean exit:** `taskpods done <name>` → commit, push, open a PR (via [`gh` CLI]), then remove the worktree.  
- **Abort button:** `taskpods abort <name>` → deletes an unpushed pod safely.  
- **Status overview:** `taskpods list` → see all active pods and paths.  
- **Housekeeping:** `taskpods prune` → removes pods already merged upstream.  

---

## 🚀 Installation

### Quick Install

```bash
pip install taskpods
```

### Alternatives

From GitHub (latest dev):

```bash
pip install git+https://github.com/yanairon/taskpods.git
```

Manual:

```bash
curl -O https://raw.githubusercontent.com/yanairon/taskpods/main/taskpods.py
chmod +x taskpods.py
sudo mv taskpods.py /usr/local/bin/taskpods
```

**Requirements**:

- Python 3.9+  
- Git 2.5+ with worktree support  
- A Git repo with a remote named `origin`  

---

## 📖 Usage

### Start a new pod

```bash
taskpods start fix-typos
```

### Finish & PR

```bash
taskpods done fix-typos -m "Fix docs typos" --remove
```

### Abort

```bash
taskpods abort fix-typos
```

### List pods

```bash
taskpods list
```

### Prune merged

```bash
taskpods prune
```

---

## ⚙️ Editor Configuration

- Env var:

```bash
export TASKPODS_EDITOR="vim"
export TASKPODS_EDITOR="code"
export TASKPODS_EDITOR="cursor"
```

- Config file `~/.taskpodsrc`:

```json
{
  "editor": "vim",
  "default_base": "main"
}
```

- CLI flag:

```bash
taskpods start my-feature --editor vim
```

Supported editors: Cursor, VS Code, Sublime, Atom, Vim/Neovim, Emacs, or any in your PATH.

---

## ❤️ Support

If `taskpods` saves you time, please consider supporting:  

- [GitHub Sponsors](https://github.com/sponsors/yanairon)  
- [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X51K73WN)  

Your support helps keep the project maintained and evolving for the community!

---

## 📜 License

MIT – see [LICENSE](LICENSE).

---

## 🤔 Why worktrees?

Git worktrees let you check out multiple branches in separate dirs without cloning. They’re fast, disk-light, and easy to clean up.  
`taskpods` wraps the common `git worktree` operations with sensible defaults and quality-of-life features like PR creation and safe aborts.

---

## 👩‍💻 Development

```bash
git clone https://github.com/yanairon/taskpods.git
cd taskpods
pip install -e ".[dev]"
pre-commit install
```

Run tests:

```bash
make test
make test-cov
make check
```

Tools used: **Black**, **Flake8**, **MyPy**, **Pre-commit**.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome!  
Open an issue or submit a PR.
