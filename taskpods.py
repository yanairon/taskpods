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
from typing import List, Optional, Tuple


def get_repo_root() -> str:
    """Get the Git repository root directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("[x] Error: Not in a Git repository")
        sys.exit(1)


def get_pods_dir() -> str:
    """Get the taskpods directory path."""
    return os.path.join(get_repo_root(), ".taskpods")


# Initialize these lazily to avoid errors at import time
REPO_ROOT = None
PODS_DIR = None


def sh(
    cmd: List[str], cwd: Optional[str] = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a command and optionally check for errors."""
    return subprocess.run(cmd, cwd=cwd, check=check)


def sout(cmd: List[str], cwd: Optional[str] = None) -> str:
    """Run a command and return stdout as a string."""
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def have(cmd_name: str) -> bool:
    """Return True if an executable exists on the system PATH."""
    return shutil.which(cmd_name) is not None


def ensure_pods_dir() -> None:
    """Create the pods directory if it does not exist."""
    pods_dir = get_pods_dir()
    os.makedirs(pods_dir, exist_ok=True)


def validate_base_branch(base: str) -> None:
    """Validate that the base branch exists and is accessible."""
    if not branch_exists(base):
        print(f"[x] Error: Base branch '{base}' does not exist locally")
        sys.exit(1)

    # Check if remote branch exists
    if not remote_branch_exists(base):
        print(f"[x] Error: Base branch '{base}' does not exist on remote 'origin'")
        sys.exit(1)


def check_remote_origin() -> None:
    """Check if remote 'origin' is configured."""
    repo_root = get_repo_root()
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        if not result.stdout.strip():
            print("[x] Error: Remote 'origin' is not configured")
            sys.exit(1)
    except subprocess.CalledProcessError:
        print("[x] Error: Remote 'origin' is not configured")
        sys.exit(1)


def has_uncommitted_changes(worktree_path: str) -> bool:
    """Check if there are uncommitted changes in the worktree."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def check_git_operations_in_progress() -> None:
    """Check if there are any Git operations in progress that could interfere."""
    repo_root = get_repo_root()

    # Check for merge/rebase/cherry-pick in progress
    git_dir = os.path.join(repo_root, ".git")
    merge_head = os.path.join(git_dir, "MERGE_HEAD")
    rebase_merge = os.path.join(git_dir, "rebase-merge")
    cherry_pick = os.path.join(git_dir, "CHERRY_PICK_HEAD")

    if os.path.exists(merge_head):
        print("[x] Error: A merge is in progress. Please complete or abort it first.")
        sys.exit(1)

    if os.path.exists(rebase_merge):
        print("[x] Error: A rebase is in progress. Please complete or abort it first.")
        sys.exit(1)

    if os.path.exists(cherry_pick):
        print(
            "[x] Error: A cherry-pick is in progress. Please complete or abort it first."
        )
        sys.exit(1)


def validate_worktree_link(worktree_path: str) -> None:
    """Validate that the worktree is properly linked to the main repository."""
    repo_root = get_repo_root()

    # Check if the worktree's .git file points to the main repository
    git_file = os.path.join(worktree_path, ".git")
    if not os.path.isfile(git_file):
        print(f"[x] Error: {worktree_path} is not a valid linked worktree")
        sys.exit(1)

    try:
        with open(git_file, "r") as f:
            git_content = f.read().strip()
            if not git_content.startswith("gitdir: "):
                print(f"[x] Error: {worktree_path} is not a valid linked worktree")
                sys.exit(1)

            # Extract the path to the main repository
            main_git_dir = git_content[8:]  # Remove "gitdir: " prefix
            if not os.path.isabs(main_git_dir):
                # Relative path, resolve it
                main_git_dir = os.path.join(worktree_path, main_git_dir)

            if not os.path.samefile(main_git_dir, os.path.join(repo_root, ".git")):
                print(
                    f"[x] Error: {worktree_path} is not linked to the expected repository"
                )
                sys.exit(1)
    except IOError as e:
        print(f"[x] Error reading worktree link: {e}")
        sys.exit(1)


def validate_pod_name(name: str) -> None:
    """Validate that the pod name is valid."""
    if not name or not name.strip():
        print("[x] Error: Pod name cannot be empty")
        sys.exit(1)

    # Check for invalid characters that could cause issues
    invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in invalid_chars:
        if char in name:
            print(f"[x] Error: Pod name cannot contain '{char}'")
            sys.exit(1)

    # Check if name is too long
    if len(name) > 50:
        print("[x] Error: Pod name is too long (max 50 characters)")
        sys.exit(1)

    # Check if the branch name would conflict with existing branches
    branch_name = f"pods/{name}"
    if branch_exists(branch_name):
        print(f"[!] Warning: Branch '{branch_name}' already exists")
        print("    This pod will reuse the existing branch")


def branch_exists(branch: str) -> bool:
    """Check if a local git branch exists."""
    repo_root = get_repo_root()
    code = subprocess.run(
        [
            "git",
            "rev-parse",
            "--verify",
            branch,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=repo_root,
    ).returncode
    return code == 0


def remote_branch_exists(branch: str) -> bool:
    """Check if a branch exists on the remote 'origin'."""
    repo_root = get_repo_root()
    code = subprocess.run(
        [
            "git",
            "ls-remote",
            "--exit-code",
            "--heads",
            "origin",
            branch,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=repo_root,
    ).returncode
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

    # Validate inputs
    validate_pod_name(name)
    validate_base_branch(base)

    branch = f"pods/{name}"
    worktree_path = os.path.join(get_pods_dir(), name)

    # Check if the worktree path is already in use
    if os.path.exists(worktree_path):
        # Check if it's actually a Git worktree
        if os.path.exists(os.path.join(worktree_path, ".git")):
            print(
                f"[x] Error: Pod path already exists and contains a Git repository: {worktree_path}"
            )
            print("    This might be an existing pod or a manually created directory")
            print("    Use 'taskpods list' to see existing pods")
            sys.exit(1)
        else:
            print(
                f"[x] Error: Pod path exists but is not a Git worktree: {worktree_path}"
            )
            print(
                "    Please remove this directory manually or choose a different name"
            )
            sys.exit(1)

    # Fetch and update base branch
    print(f"[*] Fetching {base}…")
    repo_root = get_repo_root()

    # Check if current directory is clean before switching branches
    if has_uncommitted_changes(repo_root):
        print("[x] Error: You have uncommitted changes in the main repository")
        print("    Please commit, stash, or discard them before creating a pod")
        sys.exit(1)

    try:
        sh(["git", "fetch", "origin", base], cwd=repo_root)
        # Ensure local base is up to date
        sh(["git", "checkout", base], cwd=repo_root)
        sh(["git", "pull", "--ff-only", "origin", base], cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"[x] Error updating base branch '{base}': {e}")
        sys.exit(1)

    if branch_exists(branch):
        print(f"[!] Branch {branch} exists, reusing it.")
    # Create worktree and branch
    print(f"[*] Creating worktree at {worktree_path} on {branch}")
    # `git worktree add -b` will create branch if it doesn’t exist
    try:
        sh(["git", "worktree", "add", "-b", branch, worktree_path, base], cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"[x] Error creating worktree: {e}")
        sys.exit(1)

    # Write metadata file for future reference
    meta = {
        "name": name,
        "branch": branch,
        "base": base,
        "created_by": "taskpods",
    }
    try:
        with open(os.path.join(worktree_path, ".taskpod.json"), "w") as f:
            json.dump(meta, f, indent=2)
    except IOError as e:
        print(f"[!] Warning: Could not write metadata file: {e}")
        # Continue anyway, this is not critical

    print(f"[✓] Pod ready: {worktree_path}  (branch: {branch})")
    open_editor(worktree_path)


def list_pods(_args: argparse.Namespace) -> None:
    """List all active pod worktrees."""
    pods_dir = get_pods_dir()
    if not os.path.isdir(pods_dir):
        print("(no pods)")
        return
    try:
        repo_root = get_repo_root()
        out = sout(["git", "worktree", "list", "--porcelain"], repo_root)
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
        if path and path.startswith(pods_dir):
            name = os.path.relpath(path, pods_dir)
            rows.append((name, branch or "", path))
    if not rows:
        print("(no pods)")
        return
    for name, branch, path in rows:
        print(f"- {name:<20} {branch:<30} {path}")


def done(args: argparse.Namespace) -> None:
    """Finish a pod: commit, push, open PR, optionally remove."""
    name = args.name
    validate_pod_name(name)
    worktree_path = os.path.join(get_pods_dir(), name)
    if not os.path.isdir(worktree_path):
        print(f"[x] No such pod: {name}")
        sys.exit(1)

    # Verify this is actually a Git worktree
    if not os.path.exists(os.path.join(worktree_path, ".git")):
        print(f"[x] Error: {worktree_path} is not a valid Git worktree")
        print("    This might be a manually created directory")
        sys.exit(1)
    try:
        branch = sout(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree_path)
    except subprocess.CalledProcessError:
        print(f"[x] Error: Could not determine current branch in {worktree_path}")
        sys.exit(1)

    # Verify the worktree is on the expected branch
    expected_branch = f"pods/{name}"
    if branch != expected_branch:
        print(
            f"[!] Warning: Worktree is on branch '{branch}', expected '{expected_branch}'"
        )
        print("    This might indicate the worktree was modified manually")
        response = input("    Continue anyway? (y/N): ")
        if response.lower() != "y":
            print("[*] Operation cancelled")
            return

    # Validate the worktree link
    validate_worktree_link(worktree_path)

    print(f"[*] Staging and committing in {branch}…")

    try:
        sh(["git", "add", "-A"], cwd=worktree_path)
        msg = args.message or f"pod({name}): complete"
        # Allow commit to fail (e.g. nothing to commit)
        commit_result = subprocess.run(["git", "commit", "-m", msg], cwd=worktree_path)
        if commit_result.returncode != 0:
            print("[!] Warning: Nothing to commit or commit failed")
    except subprocess.CalledProcessError as e:
        print(f"[x] Error staging changes: {e}")
        sys.exit(1)

    try:
        sh(["git", "push", "-u", "origin", branch], cwd=worktree_path)
    except subprocess.CalledProcessError as e:
        print(f"[x] Error pushing to remote: {e}")
        sys.exit(1)

    if not args.no_pr and have("gh"):
        print("[*] Opening PR via gh…")
        # Determine base branch from metadata if available
        base = "main"
        meta_path = os.path.join(worktree_path, ".taskpod.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta_data = json.load(f)
                    base = meta_data.get("base", "main")
            except (json.JSONDecodeError, IOError) as e:
                print(f"[!] Warning: Could not read metadata file: {e}")
                # Fall back to default base branch
        # Use gh to create a PR; ignore failures
        try:
            pr_result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--fill",
                    "--base",
                    base,
                    "--head",
                    branch,
                ],
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )
            if pr_result.returncode == 0:
                print("[✓] Pull request created successfully")
            else:
                print(f"[!] Warning: Failed to create PR: {pr_result.stderr}")
        except Exception as e:
            print(f"[!] Warning: Could not create PR: {e}")

    if args.remove:
        # Check for uncommitted changes
        if has_uncommitted_changes(worktree_path):
            print("[!] Warning: You have uncommitted changes in this pod")
            print("    These changes will be lost when removing the worktree")
            response = input("    Continue anyway? (y/N): ")
            if response.lower() != "y":
                print("[*] Worktree removal cancelled")
                return

        print("[*] Removing worktree…")
        repo_root = get_repo_root()
        try:
            sh(["git", "worktree", "remove", "--force", worktree_path], cwd=repo_root)
            print(f"[✓] Worktree removed: {worktree_path}")
        except subprocess.CalledProcessError as e:
            print(f"[x] Error removing worktree: {e}")
            sys.exit(1)
        # Keep branch for PR; deletion can be performed manually
    print("[✓] Done.")


def abort(args: argparse.Namespace) -> None:
    """Abort a pod: delete worktree and branch if unpushed."""
    name = args.name
    validate_pod_name(name)
    worktree_path = os.path.join(get_pods_dir(), name)
    if not os.path.isdir(worktree_path):
        print(f"[x] No such pod: {name}")
        sys.exit(1)

    # Verify this is actually a Git worktree
    if not os.path.exists(os.path.join(worktree_path, ".git")):
        print(f"[x] Error: {worktree_path} is not a valid Git worktree")
        print("    This might be a manually created directory")
        sys.exit(1)
    try:
        branch = sout(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree_path)
    except subprocess.CalledProcessError:
        print(f"[x] Error: Could not determine current branch in {worktree_path}")
        sys.exit(1)

    # Verify the worktree is on the expected branch
    expected_branch = f"pods/{name}"
    if branch != expected_branch:
        print(
            f"[!] Warning: Worktree is on branch '{branch}', expected '{expected_branch}'"
        )
        print("    This might indicate the worktree was modified manually")
        response = input("    Continue anyway? (y/N): ")
        if response.lower() != "y":
            print("[*] Operation cancelled")
            return

    # Validate the worktree link
    validate_worktree_link(worktree_path)

    # Check for uncommitted changes
    if has_uncommitted_changes(worktree_path):
        print("[!] Warning: You have uncommitted changes in this pod")
        print("    These changes will be lost when aborting")
        response = input("    Continue anyway? (y/N): ")
        if response.lower() != "y":
            print("[*] Abort cancelled")
            return

    pushed = remote_branch_exists(branch)
    if pushed:
        print(
            f"[!] Branch {branch} exists on origin.  Refusing to abort automatically."
        )
        print("    Consider `taskpods done` or remove manually after merging.")
        sys.exit(2)
    print(f"[*] Removing worktree {worktree_path} and deleting {branch}…")
    repo_root = get_repo_root()

    try:
        sh(["git", "worktree", "remove", "--force", worktree_path], cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"[x] Error removing worktree: {e}")
        sys.exit(1)

    if branch_exists(branch):
        try:
            sh(["git", "branch", "-D", branch], cwd=repo_root)
        except subprocess.CalledProcessError as e:
            print(f"[!] Warning: Could not delete branch {branch}: {e}")
            # Continue anyway, the worktree is already removed
    print("[✓] Aborted.")


def prune(_args: argparse.Namespace) -> None:
    """Remove pods whose remote branches are merged into their base."""
    try:
        repo_root = get_repo_root()
        out = sout(["git", "worktree", "list", "--porcelain"], repo_root)
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
        if not path or not branch or not path.startswith(get_pods_dir()):
            continue
        # Determine base branch from metadata
        base = "main"
        meta_path = os.path.join(path, ".taskpod.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta_data = json.load(f)
                    base = meta_data.get("base", "main")
            except (json.JSONDecodeError, IOError) as e:
                print(f"[!] Warning: Could not read metadata file for {path}: {e}")
                # Fall back to default base branch
        # Find remote branches merged into base
        try:
            merged = subprocess.run(
                [
                    "git",
                    "branch",
                    "--remotes",
                    "--merged",
                    f"origin/{base}",
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
            ).stdout
            if f"origin/{branch}" in merged:
                print(f"[*] Pruning {path} (merged into {base})")
                try:
                    sh(["git", "worktree", "remove", "--force", path], cwd=repo_root)
                    print(f"[✓] Pruned {path}")
                except subprocess.CalledProcessError as e:
                    print(f"[!] Warning: Could not remove worktree {path}: {e}")
                # Keep remote branch; deletion should be manual
        except subprocess.CalledProcessError as e:
            print(f"[!] Warning: Could not check merge status for {branch}: {e}")
            continue


def main() -> None:
    # Ensure we're in a Git repository before proceeding
    try:
        get_repo_root()
        check_remote_origin()
        check_git_operations_in_progress()
    except SystemExit:
        # get_repo_root already printed the error and called sys.exit(1)
        return

    parser = argparse.ArgumentParser(
        prog="taskpods",
        description="Parallel AI task pods via git worktrees.",
    )
    sub = parser.add_subparsers(dest="cmd")

    s = sub.add_parser("start", help="create a new pod")
    s.add_argument("name")
    s.add_argument(
        "--base", default="main", help="base branch to fork from (default: main)"
    )
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
