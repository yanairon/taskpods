import os
import subprocess
import sys
from unittest.mock import patch

# Add repository root to sys.path to ensure taskpods.py can be imported when running tests
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import after path modification
from taskpods import (branch_exists, check_git_operations_in_progress,
                      check_remote_origin, has_uncommitted_changes,
                      remote_branch_exists, validate_pod_name)


class TestTaskpodsValidation:
    """Test validation functions."""

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


class TestTaskpodsGitOperations:
    """Test Git operation functions."""

    @patch("taskpods.subprocess.run")
    def test_branch_exists_true(self, mock_run):
        """Test branch_exists returns True for existing branch."""
        mock_run.return_value.returncode = 0
        assert branch_exists("main") is True

    @patch("taskpods.subprocess.run")
    def test_branch_exists_false(self, mock_run):
        """Test branch_exists returns False for non-existing branch."""
        mock_run.return_value.returncode = 1
        assert branch_exists("nonexistent") is False

    @patch("taskpods.subprocess.run")
    def test_remote_branch_exists_true(self, mock_run):
        """Test remote_branch_exists returns True for existing remote branch."""
        mock_run.return_value.returncode = 0
        assert remote_branch_exists("main") is True

    @patch("taskpods.subprocess.run")
    def test_remote_branch_exists_false(self, mock_run):
        """Test remote_branch_exists returns False for non-existing remote branch."""
        mock_run.return_value.returncode = 1
        assert remote_branch_exists("nonexistent") is False


class TestTaskpodsErrorHandling:
    """Test error handling improvements."""

    @patch("taskpods.get_repo_root")
    def test_check_remote_origin_success(self, mock_get_repo_root):
        """Test check_remote_origin succeeds when origin is configured."""
        mock_get_repo_root.return_value = "/tmp/repo"

        with patch("taskpods.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "https://github.com/user/repo.git"

            # Should not raise exception
            check_remote_origin()

    @patch("taskpods.get_repo_root")
    def test_check_remote_origin_failure(self, mock_get_repo_root):
        """Test check_remote_origin fails when origin is not configured."""
        mock_get_repo_root.return_value = "/tmp/repo"

        with patch("taskpods.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "git remote get-url origin"
            )

            try:
                check_remote_origin()
                assert False, "Should have raised SystemExit"
            except SystemExit:
                pass  # Expected


class TestTaskpodsWorktreeValidation:
    """Test worktree validation functions."""

    def test_has_uncommitted_changes_true(self):
        """Test has_uncommitted_changes returns True when there are changes."""
        with patch("taskpods.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "M  modified_file.txt"

            assert has_uncommitted_changes("/tmp/worktree") is True

    def test_has_uncommitted_changes_false(self):
        """Test has_uncommitted_changes returns False when there are no changes."""
        with patch("taskpods.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""

            assert has_uncommitted_changes("/tmp/worktree") is False

    def test_has_uncommitted_changes_error(self):
        """Test has_uncommitted_changes returns False on error."""
        with patch("taskpods.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git status")

            assert has_uncommitted_changes("/tmp/worktree") is False


class TestTaskpodsGitOperationsInProgress:
    """Test Git operations in progress detection."""

    @patch("taskpods.get_repo_root")
    def test_check_git_operations_in_progress_clean(self, mock_get_repo_root):
        """Test check_git_operations_in_progress when no operations are in progress."""
        mock_get_repo_root.return_value = "/tmp/repo"

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            # Should not raise exception
            check_git_operations_in_progress()

    @patch("taskpods.get_repo_root")
    def test_check_git_operations_in_progress_merge(self, mock_get_repo_root):
        """Test check_git_operations_in_progress when merge is in progress."""
        mock_get_repo_root.return_value = "/tmp/repo"

        with patch("os.path.exists") as mock_exists:

            def side_effect(path):
                return path.endswith("MERGE_HEAD")

            mock_exists.side_effect = side_effect

            try:
                check_git_operations_in_progress()
                assert False, "Should have raised SystemExit"
            except SystemExit:
                pass  # Expected


@patch("taskpods.subprocess.run")
def test_branch_exists_true_for_main(mock_run):
    """main branch should exist in the repository"""
    mock_run.return_value.returncode = 0
    assert branch_exists("main") is True


@patch("taskpods.subprocess.run")
def test_branch_exists_false_for_nonexistent(mock_run):
    """Nonexistent branch should return False without printing fatal error"""
    mock_run.return_value.returncode = 1
    assert branch_exists("this-branch-does-not-exist") is False


@patch("taskpods.subprocess.run")
def test_remote_branch_exists_false_for_nonexistent(mock_run):
    """remote branch existence check should return False for a nonexistent branch"""
    mock_run.return_value.returncode = 1
    assert remote_branch_exists("this-branch-does-not-exist") is False


if __name__ == "__main__":
    # Run basic tests
    print("Running basic tests...")

    # Create test instances
    validation_tester = TestTaskpodsValidation()
    git_ops_tester = TestTaskpodsGitOperations()
    error_handling_tester = TestTaskpodsErrorHandling()
    worktree_tester = TestTaskpodsWorktreeValidation()
    git_progress_tester = TestTaskpodsGitOperationsInProgress()

    # Test validation functions
    validation_tester.test_validate_pod_name_valid()
    validation_tester.test_validate_pod_name_invalid_characters()
    validation_tester.test_validate_pod_name_too_long()
    validation_tester.test_validate_pod_name_empty()

    # Test Git operations
    test_branch_exists_true_for_main()
    test_branch_exists_false_for_nonexistent()
    test_remote_branch_exists_false_for_nonexistent()

    print("All basic tests passed!")
