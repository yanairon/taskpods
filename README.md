# taskpods: Parallel AI Task Pods via Git Worktrees

`taskpods` is a tiny command‑line tool that lets you spawn disposable “AI pods” in your Git repository.  Each pod is its own worktree and branch, so you can run Copilot, Cursor, or Claude Code on isolated tasks without polluting your main branch.  When you’re done, you can commit and push the work to a pull request or nuke the pod entirely.

## Features

- **Instant sandbox:** `taskpods start <name>` creates a new worktree under `.taskpods/<name>` and checks out a branch `pods/<name>` from a base branch (default `main`).
- **Clean exit:** `taskpods done <name>` stages, commits, and pushes everything in the pod, optionally opening a GitHub pull request via [`gh` CLI], then removes the worktree.
- **Abort button:** `taskpods abort <name>` deletes an unpushed pod and its branch without a trace.
- **Status overview:** `taskpods list` shows your active pods and where they live in the file system.
- **House‑keeping:** `taskpods prune` removes pods whose branches have been merged into their base branch.

## Installation

This repository contains a single script, `taskpods.py`, which can be run directly with Python 3.  To install it globally, copy it somewhere on your `PATH` and make it executable:

```bash
cp taskpods.py ~/.local/bin/taskpods
chmod +x ~/.local/bin/taskpods
```

Alternatively, you can run it in place:

```bash
python3 taskpods.py start myfeature
```

## Usage

### Create a new pod

```bash
taskpods start fix‑typos
```

This will:

1. Fetch the latest changes from `main` and fast‑forward your local `main`.
2. Create a new branch `pods/fix‑typos` from `main`.
3. Add a Git worktree at `.taskpods/fix‑typos`.
4. Drop you into a new editor window (Cursor if available, otherwise VS Code) with the worktree opened.

### Finish a pod and create a pull request

```bash
taskpods done fix‑typos -m "Fix docs typos" --remove
```

This will stage and commit all changes in the worktree with the given message, push the branch to `origin`, open a pull request via the [`gh` CLI] (if installed), and remove the worktree.  The branch remains so you can still interact with the PR.

### Abort a pod

```bash
taskpods abort fix‑typos
```

If the branch hasn’t been pushed to `origin`, this will delete the worktree and local branch.  It refuses to abort pods whose branches are already on `origin` to avoid data loss.

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

- **Python 3.7+** – This script uses only the standard library.
- **Git** – You need Git installed with worktree support (Git 2.5+).  The repository must already be initialised with a remote named `origin`.
- **Editor (optional)** – The script will try to open your editor.  It prefers `cursor` (Cursor’s CLI), then `code` (VS Code).  If neither is found, it won’t open anything.
- **`gh` CLI (optional)** – If installed, `taskpods done` will automatically open a GitHub pull request.  Otherwise, it simply pushes the branch and prints a success message.

## Making Money

You’re welcome to use this tool for free.  If it saves you time or makes you smile, consider buying me a coffee via [Ko‑fi](https://ko‑fi.com/yourname) or [GitHub Sponsors](https://github.com/sponsors/yourname).  Even \$1 helps justify the time spent maintaining and improving this little hack.

## License

This project is released under the MIT License.  See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions, bug reports, and feature requests are welcome!  Feel free to open an issue or submit a pull request.

---

### Why worktrees?

Git worktrees let you have multiple branches checked out in separate directories without duplicating your entire `.git` object store.  They’re faster than clones, don’t waste disk space, and make cleanup trivial.  `taskpods` wraps a handful of `git worktree` commands with sensible defaults and adds quality‑of‑life features like automatic PR creation and safe aborts.

### DISCLAIMER

This tool is provided “as is” with no warranty.  It writes to your Git repository and could potentially cause data loss if used incorrectly.  Read the code, use it at your own risk, and always back up anything important before experimenting.