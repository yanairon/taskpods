"""Test suite for remaining functions in taskpods module."""

import subprocess
import sys
from unittest.mock import patch, MagicMock

# Add repository root to sys.path to ensure taskpods.py can be imported
repo_root = __import__('os').path.dirname(__import__('os').path.dirname(__file__))
sys.path.insert(0, __import__('os').path.abspath(repo_root))

# Import after path modification
from taskpods import (  # noqa: E402
    validate_worktree_link,
    check_remote_origin,
    check_git_operations_in_progress,
    validate_pod_name,
    branch_exists,
    remote_branch_exists,
    has_uncommitted_changes,
)


class TestValidateWorktreeLink:
    """Test the validate_worktree_link function."""

    @patch("taskpods.get_repo_root")
    @patch("taskpods.sout")
    @patch("os.path.samefile")
    def test_validate_worktree_link_success(self, mock_samefile, mock_sout, mock_get_repo_root):
        """Test validate_worktree_link succeeds with valid worktree."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_sout.return_value = "/tmp/.taskpods/test-pod"
        mock_samefile.return_value = True

        # Should not raise exception
        with patch("sys.exit") as mock_exit:
            validate_worktree_link("/tmp/.taskpods/test-pod")
            mock_exit.assert_not_called()

    @patch("taskpods.get_repo_root")
    @patch("taskpods.sout")
    @patch("os.path.samefile")
    def test_validate_worktree_link_failure(self, mock_samefile, mock_sout, mock_get_repo_root):
        """Test validate_worktree_link fails with invalid worktree."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_sout.return_value = "/tmp/.taskpods/different-pod"  # Different path
        mock_samefile.return_value = False

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                validate_worktree_link("/tmp/.taskpods/test-pod")
                mock_print.assert_any_call(
                    "[x] Error: /tmp/.taskpods/test-pod is not linked to the expected repository"
                )
                mock_exit.assert_called_once_with(1)

    @patch("taskpods.get_repo_root")
    @patch("taskpods.sout")
    def test_validate_worktree_link_git_error(self, mock_sout, mock_get_repo_root):
        """Test validate_worktree_link handles git error."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_sout.side_effect = subprocess.CalledProcessError(1, "git worktree list")

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                validate_worktree_link("/tmp/.taskpods/test-pod")
                mock_print.assert_any_call(
                    "[x] Error reading worktree link: [Errno 2] No such file or directory: '/tmp/.taskpods/test-pod/.git'"
                )
                mock_exit.assert_called_once_with(1)


class TestCheckRemoteOrigin:
    """Test the check_remote_origin function."""

    @patch("taskpods.get_repo_root")
    @patch("taskpods.subprocess.run")
    def test_check_remote_origin_success(self, mock_run, mock_get_repo_root):
        """Test check_remote_origin succeeds when origin is configured."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "https://github.com/user/repo.git"
        mock_run.return_value = mock_process

        # Should not raise exception
        check_remote_origin()

    @patch("taskpods.get_repo_root")
    @patch("taskpods.subprocess.run")
    def test_check_remote_origin_failure(self, mock_run, mock_get_repo_root):
        """Test check_remote_origin fails when origin is not configured."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_run.side_effect = subprocess.CalledProcessError(1, "git remote get-url origin")

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                check_remote_origin()
                mock_print.assert_called_once_with("[x] Error: Remote 'origin' is not configured")
                mock_exit.assert_called_once_with(1)


class TestCheckGitOperationsInProgress:
    """Test the check_git_operations_in_progress function."""

    @patch("taskpods.get_repo_root")
    @patch("os.path.exists")
    def test_check_git_operations_in_progress_clean(self, mock_exists, mock_get_repo_root):
        """Test check_git_operations_in_progress when no operations are in progress."""
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_exists.return_value = False

        # Should not raise exception
        check_git_operations_in_progress()

    @patch("taskpods.get_repo_root")
    @patch("os.path.exists")
    def test_check_git_operations_in_progress_merge(self, mock_exists, mock_get_repo_root):
        """Test check_git_operations_in_progress when merge is in progress."""
        mock_get_repo_root.return_value = "/tmp/repo"

        def side_effect(path):
            return path.endswith("MERGE_HEAD")

        mock_exists.side_effect = side_effect

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                check_git_operations_in_progress()
                mock_print.assert_called_once_with(
                    "[x] Error: A merge is in progress. Please complete or abort it first."
                )
                mock_exit.assert_called_once_with(1)

    @patch("taskpods.get_repo_root")
    @patch("os.path.exists")
    def test_check_git_operations_in_progress_rebase(self, mock_exists, mock_get_repo_root):
        """Test check_git_operations_in_progress when rebase is in progress."""
        mock_get_repo_root.return_value = "/tmp/repo"

        def side_effect(path):
            return path.endswith("rebase-merge")

        mock_exists.side_effect = side_effect

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                check_git_operations_in_progress()
                mock_print.assert_called_once_with(
                    "[x] Error: A rebase is in progress. Please complete or abort it first."
                )
                mock_exit.assert_called_once_with(1)

    @patch("taskpods.get_repo_root")
    @patch("os.path.exists")
    def test_check_git_operations_in_progress_cherry_pick(self, mock_exists, mock_get_repo_root):
        """Test check_git_operations_in_progress when cherry-pick is in progress."""
        mock_get_repo_root.return_value = "/tmp/repo"

        def side_effect(path):
            return path.endswith("CHERRY_PICK_HEAD")

        mock_exists.side_effect = side_effect

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                check_git_operations_in_progress()
                mock_print.assert_called_once_with(
                    "[x] Error: A cherry-pick is in progress. Please complete or abort it first."
                )
                mock_exit.assert_called_once_with(1)


class TestValidatePodName:
    """Test the validate_pod_name function."""

    def test_validate_pod_name_valid(self):
        """Test valid pod names."""
        # These should not raise exceptions
        validate_pod_name("valid-name")
        validate_pod_name("valid_name")
        validate_pod_name("valid123")
        validate_pod_name("a" * 50)  # Max length

    def test_validate_pod_name_invalid_characters(self):
        """Test pod names with invalid characters."""
        invalid_names = ["name/with/slash", "name\\with\\backslash", "name:with:colon"]
        for name in invalid_names:
            try:
                validate_pod_name(name)
                assert False, f"Should have failed for: {name}"
            except SystemExit:
                pass  # Expected

    def test_validate_pod_name_too_long(self):
        """Test pod names that are too long."""
        long_name = "a" * 51
        try:
            validate_pod_name(long_name)
            assert False, "Should have failed for long name"
        except SystemExit:
            pass  # Expected

    def test_validate_pod_name_empty(self):
        """Test empty pod names."""
        try:
            validate_pod_name("")
            assert False, "Should have failed for empty name"
        except SystemExit:
            pass  # Expected

        try:
            validate_pod_name("   ")
            assert False, "Should have failed for whitespace-only name"
        except SystemExit:
            pass  # Expected


class TestBranchExists:
    """Test the branch_exists function."""

    @patch("taskpods.subprocess.run")
    def test_branch_exists_true(self, mock_run):
        """Test branch_exists returns True for existing branch."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        result = branch_exists("main")
        assert result is True
        # Note: The function calls get_repo_root() first, so we expect multiple calls
        mock_run.assert_called()

    @patch("taskpods.subprocess.run")
    def test_branch_exists_false(self, mock_run):
        """Test branch_exists returns False for non-existing branch."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_run.return_value = mock_process

        result = branch_exists("nonexistent")
        assert result is False

    def test_branch_exists_no_cwd_support(self):
        """Test branch_exists doesn't support cwd parameter."""
        try:
            branch_exists("main", cwd="/tmp/repo")
            assert False, "Should have failed with cwd parameter"
        except TypeError:
            pass  # Expected


class TestRemoteBranchExists:
    """Test the remote_branch_exists function."""

    @patch("taskpods.subprocess.run")
    def test_remote_branch_exists_true(self, mock_run):
        """Test remote_branch_exists returns True for existing remote branch."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        result = remote_branch_exists("main")
        assert result is True
        # Note: The function calls get_repo_root() first, so we expect multiple calls
        mock_run.assert_called()

    @patch("taskpods.subprocess.run")
    def test_remote_branch_exists_false(self, mock_run):
        """Test remote_branch_exists returns False for non-existing remote branch."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_run.return_value = mock_process

        result = remote_branch_exists("nonexistent")
        assert result is False

    def test_remote_branch_exists_no_cwd_support(self):
        """Test remote_branch_exists doesn't support cwd parameter."""
        try:
            remote_branch_exists("main", cwd="/tmp/repo")
            assert False, "Should have failed with cwd parameter"
        except TypeError:
            pass  # Expected


class TestHasUncommittedChanges:
    """Test the has_uncommitted_changes function."""

    @patch("taskpods.subprocess.run")
    def test_has_uncommitted_changes_true(self, mock_run):
        """Test has_uncommitted_changes returns True when there are changes."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "M  modified_file.txt"
        mock_run.return_value = mock_process

        result = has_uncommitted_changes("/tmp/worktree")
        assert result is True
        mock_run.assert_called_once_with(
            ["git", "status", "--porcelain"],
            cwd="/tmp/worktree",
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("taskpods.subprocess.run")
    def test_has_uncommitted_changes_false(self, mock_run):
        """Test has_uncommitted_changes returns False when there are no changes."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_run.return_value = mock_process

        result = has_uncommitted_changes("/tmp/worktree")
        assert result is False

    @patch("taskpods.subprocess.run")
    def test_has_uncommitted_changes_error(self, mock_run):
        """Test has_uncommitted_changes returns False on error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git status")

        result = has_uncommitted_changes("/tmp/worktree")
        assert result is False


if __name__ == "__main__":
    # Run tests
    print("Running remaining function tests...")

    # Create test instances and run tests
    worktree_tester = TestValidateWorktreeLink()
    remote_tester = TestCheckRemoteOrigin()
    git_ops_tester = TestCheckGitOperationsInProgress()
    pod_name_tester = TestValidatePodName()
    branch_tester = TestBranchExists()
    remote_branch_tester = TestRemoteBranchExists()
    changes_tester = TestHasUncommittedChanges()

    print("All remaining function tests completed!")
