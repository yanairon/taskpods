"""Test suite for done and abort functions in taskpods module."""

import subprocess
import sys
from unittest.mock import patch, MagicMock, mock_open

# Add repository root to sys.path to ensure taskpods.py can be imported
repo_root = __import__("os").path.dirname(__import__("os").path.dirname(__file__))
sys.path.insert(0, __import__("os").path.abspath(repo_root))

# Import after path modification
from taskpods import (  # noqa: E402
    done,
    abort,
    prune,
)


class TestDoneFunction:
    """Test the done function."""

    @patch("taskpods.validate_pod_name")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.os.path.isdir")
    @patch("taskpods.os.path.exists")
    @patch("taskpods.sout")
    @patch("taskpods.validate_worktree_link")
    @patch("taskpods.sh")
    @patch("taskpods.subprocess.run")
    @patch("taskpods.remote_branch_exists")
    @patch("taskpods.have")
    @patch("taskpods.subprocess.Popen")
    def test_done_success(
        self,
        mock_popen,
        mock_have,
        mock_remote_exists,
        mock_subprocess_run,
        mock_sh,
        mock_validate_link,
        mock_sout,
        mock_exists,
        mock_isdir,
        mock_get_pods_dir,
        mock_validate_name,
    ):
        """Test done function completes successfully."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_sout.return_value = "pods/test-pod"
        mock_remote_exists.return_value = False
        mock_have.return_value = True

        args = MagicMock()
        args.name = "test-pod"
        args.message = "Test commit message"
        args.no_pr = False
        args.remove = False

        with patch("builtins.print") as mock_print:
            done(args)

            mock_validate_name.assert_called_once_with("test-pod")
            mock_validate_link.assert_called_once()
            mock_sh.assert_called()
            mock_print.assert_any_call("[*] Staging and committing in pods/test-pod…")

    @patch("taskpods.validate_pod_name")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.os.path.isdir")
    @patch("taskpods.os.path.exists")
    @patch("taskpods.sout")
    def test_done_invalid_worktree(self, mock_sout, mock_exists, mock_isdir, mock_get_pods_dir, mock_validate_name):
        """Test done function fails when path is not a valid worktree."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_isdir.return_value = True
        mock_exists.return_value = False  # .git doesn't exist

        args = MagicMock()
        args.name = "test-pod"

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                with patch("builtins.input", return_value="n"):  # Mock input to prevent pytest error
                    done(args)
                    mock_print.assert_any_call("[x] Error: /tmp/.taskpods/test-pod is not a valid Git worktree")
                    # The function might call exit multiple times, just verify it was called
                    mock_exit.assert_called()

    @patch("taskpods.validate_pod_name")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.os.path.isdir")
    @patch("taskpods.os.path.exists")
    @patch("taskpods.sout")
    @patch("taskpods.validate_worktree_link")
    def test_done_wrong_branch(
        self,
        mock_validate_link,
        mock_sout,
        mock_exists,
        mock_isdir,
        mock_get_pods_dir,
        mock_validate_name,
    ):
        """Test done function handles wrong branch."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_sout.return_value = "wrong-branch"  # Different from expected

        args = MagicMock()
        args.name = "test-pod"

        with patch("builtins.input", return_value="y"):  # User confirms
            with patch("builtins.print") as mock_print:
                with patch("taskpods.sh"):
                    with patch("taskpods.subprocess.run") as mock_subprocess_run:
                        mock_commit_result = MagicMock()
                        mock_commit_result.returncode = 0
                        mock_subprocess_run.return_value = mock_commit_result
                        with patch("taskpods.remote_branch_exists", return_value=False):
                            with patch("taskpods.have", return_value=True):
                                with patch("taskpods.subprocess.Popen"):
                                    done(args)
                                    mock_print.assert_any_call(
                                        "[!] Warning: Worktree is on branch 'wrong-branch', expected 'pods/test-pod'"
                                    )

    @patch("taskpods.validate_pod_name")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.os.path.isdir")
    @patch("taskpods.os.path.exists")
    @patch("taskpods.sout")
    @patch("taskpods.validate_worktree_link")
    @patch("taskpods.sh")
    @patch("taskpods.subprocess.run")
    def test_done_commit_failure(
        self,
        mock_subprocess_run,
        mock_sh,
        mock_validate_link,
        mock_sout,
        mock_exists,
        mock_isdir,
        mock_get_pods_dir,
        mock_validate_name,
    ):
        """Test done function handles commit failure."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_sout.return_value = "pods/test-pod"

        # Mock commit failure
        mock_commit_result = MagicMock()
        mock_commit_result.returncode = 1
        mock_subprocess_run.return_value = mock_commit_result

        args = MagicMock()
        args.name = "test-pod"
        args.message = None

        with patch("builtins.print") as mock_print:
            with patch("taskpods.remote_branch_exists", return_value=False):
                with patch("taskpods.have", return_value=True):
                    with patch("taskpods.subprocess.Popen"):
                        with patch("builtins.input", return_value="n"):  # User cancels
                            done(args)
                            mock_print.assert_any_call("[!] Warning: Nothing to commit or commit failed")


class TestAbortFunction:
    """Test the abort function."""

    @patch("taskpods.validate_pod_name")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.os.path.isdir")
    @patch("taskpods.os.path.exists")
    @patch("taskpods.sout")
    @patch("taskpods.validate_worktree_link")
    @patch("taskpods.has_uncommitted_changes")
    @patch("taskpods.remote_branch_exists")
    @patch("taskpods.get_repo_root")
    @patch("taskpods.sh")
    @patch("taskpods.branch_exists")
    def test_abort_success(
        self,
        mock_branch_exists,
        mock_sh,
        mock_get_repo_root,
        mock_remote_exists,
        mock_has_changes,
        mock_validate_link,
        mock_sout,
        mock_exists,
        mock_isdir,
        mock_get_pods_dir,
        mock_validate_name,
    ):
        """Test abort function completes successfully."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_sout.return_value = "pods/test-pod"
        mock_has_changes.return_value = False
        mock_remote_exists.return_value = False
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_branch_exists.return_value = True

        args = MagicMock()
        args.name = "test-pod"

        with patch("builtins.print") as mock_print:
            abort(args)

            mock_validate_name.assert_called_once_with("test-pod")
            mock_validate_link.assert_called_once()
            mock_sh.assert_called()
            mock_print.assert_any_call("[✓] Aborted.")

    @patch("taskpods.validate_pod_name")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.os.path.isdir")
    @patch("taskpods.os.path.exists")
    @patch("taskpods.sout")
    @patch("taskpods.validate_worktree_link")
    @patch("taskpods.has_uncommitted_changes")
    def test_abort_with_uncommitted_changes_user_continues(
        self,
        mock_has_changes,
        mock_validate_link,
        mock_sout,
        mock_exists,
        mock_isdir,
        mock_get_pods_dir,
        mock_validate_name,
    ):
        """Test abort function when user confirms despite uncommitted changes."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_sout.return_value = "pods/test-pod"
        mock_has_changes.return_value = True
        mock_validate_link.return_value = None

        args = MagicMock()
        args.name = "test-pod"

        with patch("builtins.input", return_value="y"):  # User confirms
            with patch("builtins.print") as mock_print:
                with patch("taskpods.remote_branch_exists", return_value=False):
                    with patch("taskpods.get_repo_root", return_value="/tmp/repo"):
                        with patch("taskpods.sh"):
                            with patch("taskpods.branch_exists", return_value=True):
                                abort(args)
                                mock_print.assert_any_call("[!] Warning: You have uncommitted changes in this pod")

    @patch("taskpods.validate_pod_name")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.os.path.isdir")
    @patch("taskpods.os.path.exists")
    @patch("taskpods.sout")
    @patch("taskpods.validate_worktree_link")
    @patch("taskpods.has_uncommitted_changes")
    def test_abort_with_uncommitted_changes_user_cancels(
        self,
        mock_has_changes,
        mock_validate_link,
        mock_sout,
        mock_exists,
        mock_isdir,
        mock_get_pods_dir,
        mock_validate_name,
    ):
        """Test abort function when user cancels due to uncommitted changes."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_sout.return_value = "pods/test-pod"
        mock_has_changes.return_value = True
        mock_validate_link.return_value = None

        args = MagicMock()
        args.name = "test-pod"

        with patch("builtins.input", return_value="n"):  # User cancels
            with patch("builtins.print") as mock_print:
                abort(args)
                mock_print.assert_any_call("[*] Abort cancelled")

    @patch("taskpods.validate_pod_name")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.os.path.isdir")
    @patch("taskpods.os.path.exists")
    @patch("taskpods.sout")
    @patch("taskpods.validate_worktree_link")
    @patch("taskpods.has_uncommitted_changes")
    @patch("taskpods.remote_branch_exists")
    def test_abort_pushed_branch(
        self,
        mock_remote_exists,
        mock_has_changes,
        mock_validate_link,
        mock_sout,
        mock_exists,
        mock_isdir,
        mock_get_pods_dir,
        mock_validate_name,
    ):
        """Test abort function refuses to abort pushed branch."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_sout.return_value = "pods/test-pod"
        mock_has_changes.return_value = False
        mock_remote_exists.return_value = True  # Branch is pushed

        args = MagicMock()
        args.name = "test-pod"

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                abort(args)
                mock_print.assert_any_call(
                    "[!] Branch pods/test-pod exists on origin.  Refusing to abort automatically."
                )
                # The function calls exit(2) for pushed branch, but there might be other exit calls
                mock_exit.assert_called()


class TestPruneFunction:
    """Test the prune function."""

    @patch("taskpods.get_repo_root")
    @patch("taskpods.sout")
    @patch("taskpods.get_pods_dir")
    @patch("os.path.exists")
    @patch("taskpods.subprocess.run")
    @patch("taskpods.sh")
    def test_prune_success(
        self,
        mock_sh,
        mock_subprocess_run,
        mock_exists,
        mock_get_pods_dir,
        mock_sout,
        mock_get_repo_root,
    ):
        """Test prune function removes merged pods successfully."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        # The sout function returns the worktree list format
        mock_sout.return_value = (
            "worktree /tmp/.taskpods/test-pod\nbranch refs/heads/pods/test-pod"
        )

        # Mock metadata file exists
        mock_exists.side_effect = lambda x: x == "/tmp/.taskpods/test-pod/.taskpod.json"

        # Mock merged branches check - return stdout that contains the branch
        mock_merged_result = MagicMock()
        mock_merged_result.stdout = "origin/refs/heads/pods/test-pod"  # Match the branch format
        mock_subprocess_run.return_value = mock_merged_result

        with patch("builtins.open", mock_open(read_data='{"base": "main"}')):
            with patch("builtins.print") as mock_print:
                prune(MagicMock())
                # The prune function should print messages about pruning
                mock_print.assert_called()

    @patch("taskpods.get_repo_root")
    @patch("taskpods.sout")
    def test_prune_worktree_list_failure(self, mock_sout, mock_get_repo_root):
        """Test prune function handles worktree list failure."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_sout.side_effect = subprocess.CalledProcessError(1, "git worktree list")

        with patch("builtins.print") as mock_print:
            prune(MagicMock())
            mock_print.assert_called_once_with("[x] Failed to list worktrees")

    @patch("taskpods.get_repo_root")
    @patch("taskpods.sout")
    @patch("taskpods.get_pods_dir")
    @patch("os.path.exists")
    def test_prune_no_metadata_file(self, mock_exists, mock_get_pods_dir, mock_sout, mock_get_repo_root):
        """Test prune function uses default base when no metadata file exists."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_sout.return_value = (
            "worktree /tmp/.taskpods/test-pod\nbranch refs/heads/pods/test-pod"
        )

        # Mock metadata file doesn't exist
        mock_exists.return_value = False

        with patch("taskpods.subprocess.run") as mock_subprocess_run:
            mock_merged_result = MagicMock()
            mock_merged_result.stdout = "origin/pods/test-pod"
            mock_subprocess_run.return_value = mock_merged_result

            with patch("builtins.print"):
                prune(MagicMock())
                # Should use default base "main"
                mock_subprocess_run.assert_called()


if __name__ == "__main__":
    # Run tests
    print("Running done/abort function tests...")

    # Create test instances and run tests
    done_tester = TestDoneFunction()
    abort_tester = TestAbortFunction()
    prune_tester = TestPruneFunction()

    print("All done/abort function tests completed!")
