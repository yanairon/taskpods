#!/usr/bin/env python3
"""
taskpods: spin up isolated Git worktrees for parallel development tasks.

This script allows you to create disposable "pods" backed by Git worktrees and
branches.  Each pod lives under `.taskpods/<name>` in your repository and is
checked out on its own branch (`pods/<name>` by default) based off a base
branch (`main` by default).  When you finish or abandon a pod, you can commit
and push the work, then remove the worktree, or delete everything if the
branch was never pushed.

Commands:

* `start <name>` – create a new pod worktree and branch from the base.
* `done <name>` – stage, commit, push the pod, optionally open a PR via `gh`.
* `abort <name>` – remove an unpushed pod and its branch.
* `list` – list all pods currently checked out.
* `prune` – remove pods whose branches are fully merged into their base.

Usage:

    taskpods start myfeature
    taskpods done myfeature -m "Implement feature X" --remove
    taskpods abort spike-experiment
    taskpods list
    taskpods prune

See the README.md for more details.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import List, Tuple, Optional

REPO_ROOT = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
).stdout.strip()
PODS_DIR = os.path.join(REPO_ROOT, ".taskpods")


def sh(cmd: List[str], cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and optionally check for errors."""
    return subprocess.run(cmd, cwd=cwd, check=check)


def sout(cmd: List[str], cwd: Optional[str] = None) -> str:
    """Run a command and return stdout as a string."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def have(cmd_name: str) -> bool:
    """Return True if an executable exists on the system PATH."""
    return shutil.which(cmd_name) is not None


def ensure_pods_dir() -> None:
    """Create the pods directory if it does not exist."""
    os.makedirs(PODS_DIR, exist_ok=True)


def branch_exists(branch: str) -> bool:
    """Check if a local git branch exists."""
    code = subprocess.run([
        "git",
        "rev-parse",
        "--verify",
        branch,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=REPO_ROOT).returncode
    return code == 0


def remote_branch_exists(branch: str) -> bool:
    """Check if a branch exists on the remote 'origin'."""
    code = subprocess.run([
        "git",
        "ls-remote",
        "--exit-code",
        "--heads",
        "origin",
        branch,
    ] stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,, cwd=REPO_ROOT).returncode
    return code == 0


def open_editor(path: str) -> None:
    """Open the given path in Cursor or VS Code if available."""
    editor = shutil.which("cursor") or shutil.which("code")
    if not editor:
        return
    # Try launching a new window; ignore failures.
    try:
        subprocess.Popen([editor, "--new-window", path])
    except Exception:
        pass


def start(args: argparse.Namespace) -> None:
    """Create a new pod worktree and branch."""
    ensure_pods_dir()
    base = args.base
    name = args.name
    branch = f"pods/{name}"
    worktree_path = os.path.join(PODS_DIR, name)
    if os.path.exists(worktree_path):
        print(f"[x] Pod path exists: {worktree_path}")
        sys.exit(1)

    # Fetch and update base branch
    print(f"[*] Fetching {base}…")
    sh(["git", "fetch", "origin", base], cwd=REPO_ROOT)
    # Ensure local base is up to date
    sh(["git", "checkout", base], cwd=REPO_ROOT)
    sh(["git", "pull", "--ff-only", "origin", base], cwd=REPO_ROOT)

    if branch_exists(branch):
        print(f"[!] Branch {branch} exists, reusing it.")
    # Create worktree and branch
    print(f"[*] Creating worktree at {worktree_path} on {branch}")
    # `git worktree add -b` will create branch if it doesn’t exist
    sh(["git", "worktree", "add", "-b", branch, worktree_path, base], cwd=REPO_ROOT)

    # Write metadata file for future reference
    meta = {
        "name": name,
        "branch": branch,
        "base": base,
        "created_by": "taskpods",
    }
    with open(os.path.join(worktree_path, ".taskpod.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[✓] Pod ready: {worktree_path}  (branch: {branch})")
    open_editor(worktree_path)


def list_pods(_args: argparse.Namespace) -> None:
    """List all active pod worktrees."""
    if not os.path.isdir(PODS_DIR):
        print("(no pods)")
        return
    try:
        out = sout(["git", "worktree", "list", "--porcelain"], REPO_ROOT)
    except subprocess.CalledProcessError:
        print("[x] Failed to list worktrees")
        return
    blocks = [b for b in out.split("\n\n") if b.strip()]
    rows: List[Tuple[str, str, str]] = []
    for b in blocks:
        path: Optional[str] = None
        branch: Optional[str] = None
        for line in b.splitlines():
            if line.startswith("worktree "):
                path = line.split(" ", 1)[1]
            if line.startswith("branch "):
                branch = line.split(" ", 1)[1]
        if path and path.startswith(PODS_DIR):
            name = os.path.relpath(path, PODS_DIR)
            rows.append((name, branch or "", path))
    if not rows:
        print("(no pods)")
        return
    for name, branch, path in rows:
        print(f"- {name:<20} {branch:<30} {path}")


def done(args: argparse.Namespace) -> None:
    """Finish a pod: commit, push, open PR, optionally remove."""
    name = args.name
    worktree_path = os.path.join(PODS_DIR, name)
    if not os.path.isdir(worktree_path):
        print(f"[x] No such pod: {name}")
        sys.exit(1)
    branch = sout(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree_path)
    print(f"[*] Staging and committing in {branch}…")
    sh(["git", "add", "-A"], cwd=worktree_path)
    msg = args.message or f"pod({name}): complete"
    # Allow commit to fail (e.g. nothing to commit)
    subprocess.run(["git", "commit", "-m", msg], cwd=worktree_path)
    sh(["git", "push", "-u", "origin", branch], cwd=worktree_path)

    if not args.no_pr and have("gh"):
        title = msg
        print("[*] Opening PR via gh…")
        # Determine base branch from metadata if available
        base = "main"
        meta_path = os.path.join(worktree_path, ".taskpod.json")
        if os.path.exists(meta_path):
            try:
                base = json.load(open(meta_path))["base"]
            except Exception:
                pass
        # Use gh to create a PR; ignore failures
        subprocess.run([
            "gh",
            "pr",
            "create",
            "--fill",
            "--base",
            base,
            "--head",
            branch,
        ], cwd=worktree_path)

    if args.remove:
        print("[*] Removing worktree…")
        sh(["git", "worktree", "remove", "--force", worktree_path], cwd=REPO_ROOT)
        # Keep branch for PR; deletion can be performed manually
    print("[✓] Done.")


def abort(args: argparse.Namespace) -> None:
    """Abort a pod: delete worktree and branch if unpushed."""
    name = args.name
    worktree_path = os.path.join(PODS_DIR, name)
    if not os.path.isdir(worktree_path):
        print(f"[x] No such pod: {name}")
        sys.exit(1)
    branch = sout(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree_path)
    pushed = remote_branch_exists(branch)
    if pushed:
        print(f"[!] Branch {branch} exists on origin.  Refusing to abort automatically.")
        print("    Consider `taskpods done` or remove manually after merging.")
        sys.exit(2)
    print(f"[*] Removing worktree {worktree_path} and deleting {branch}…")
    sh(["git", "worktree", "remove", "--force", worktree_path], cwd=REPO_ROOT)
    if branch_exists(branch):
        sh(["git", "branch", "-D", branch], cwd=REPO_ROOT)
    print("[✓] Aborted.")


def prune(_args: argparse.Namespace) -> None:
    """Remove pods whose remote branches are merged into their base."""
    try:
        out = sout(["git", "worktree", "list", "--porcelain"], REPO_ROOT)
    except subprocess.CalledProcessError:
        print("[x] Failed to list worktrees")
        return
    blocks = [b for b in out.split("\n\n") if b.strip()]
    for b in blocks:
        path: Optional[str] = None
        branch: Optional[str] = None
        for line in b.splitlines():
            if line.startswith("worktree "):
                path = line.split(" ", 1)[1]
            if line.startswith("branch "):
                branch = line.split(" ", 1)[1]
        if not path or not branch or not path.startswith(PODS_DIR):
            continue
        # Determine base branch from metadata
        base = "main"
        meta_path = os.path.join(path, ".taskpod.json")
        if os.path.exists(meta_path):
            try:
                base = json.load(open(meta_path))["base"]
            except Exception:
                pass
        # Find remote branches merged into base
        merged = subprocess.run([
            "git",
            "branch",
            "--remotes",
            "--merged",
            f"origin/{base}",
        ], cwd=REPO_ROOT, capture_output=True, text=True).stdout
        if f"origin/{branch}" in merged:
            print(f"[*] Pruning {path} (merged into {base})")
            sh(["git", "worktree", "remove", "--force", path], cwd=REPO_ROOT)
            # Keep remote branch; deletion should be manual


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="taskpods",
        description="Parallel AI task pods via git worktrees.",
    )
    sub = parser.add_subparsers(dest="cmd")

    s = sub.add_parser("start", help="create a new pod")
    s.add_argument("name")
    s.add_argument("--base", default="main", help="base branch to fork from (default: main)")
    s.set_defaults(func=start)

    s2 = sub.add_parser("done", help="commit, push, optionally remove pod")
    s2.add_argument("name")
    s2.add_argument("-m", "--message", dest="message", help="commit message")
    s2.add_argument("--no-pr", action="store_true", help="do not open a pull request")
    s2.add_argument(
        "--remove",
        action="store_true",
        help="remove the worktree after pushing (branch stays)",
    )
    s2.set_defaults(func=done)

    s3 = sub.add_parser("abort", help="delete unpushed pod")
    s3.add_argument("name")
    s3.set_defaults(func=abort)

    s4 = sub.add_parser("list", help="list pods")
    s4.set_defaults(func=list_pods)

    s5 = sub.add_parser("prune", help="remove merged pods")
    s5.set_defaults(func=prune)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
