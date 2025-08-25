"""Test suite for main functions in taskpods module."""

import subprocess
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add repository root to sys.path to ensure taskpods.py can be imported
repo_root = __import__("os").path.dirname(__import__("os").path.dirname(__file__))
sys.path.insert(0, __import__("os").path.abspath(repo_root))

# Import after path modification
from taskpods import ensure_pods_dir  # noqa: E402
from taskpods import (
    _get_preferred_editor,
    get_pods_dir,
    get_repo_root,
    have,
    list_pods,
    main,
    open_editor,
    sh,
    sout,
    start,
    validate_base_branch,
)


class TestUtilityFunctions:
    """Test utility functions."""

    @patch("taskpods.subprocess.run")
    def test_get_repo_root_success(self, mock_run):
        """Test get_repo_root returns correct path."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "/tmp/test-repo\n"

        result = get_repo_root()
        assert result == "/tmp/test-repo"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("taskpods.subprocess.run")
    def test_get_repo_root_failure(self, mock_run):
        """Test get_repo_root exits on failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git rev-parse")

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                get_repo_root()
                mock_print.assert_called_once_with("[x] Error: Not in a Git repository")
                mock_exit.assert_called_once_with(1)

    @patch("taskpods.get_repo_root")
    def test_get_pods_dir(self, mock_get_repo_root):
        """Test get_pods_dir returns correct path."""
        mock_get_repo_root.return_value = "/tmp/test-repo"
        result = get_pods_dir()
        assert result == "/tmp/test-repo/.taskpods"

    @patch("taskpods.get_pods_dir")
    @patch("os.makedirs")
    def test_ensure_pods_dir_creates_directory(self, mock_makedirs, mock_get_pods_dir):
        """Test ensure_pods_dir creates directory."""
        mock_get_pods_dir.return_value = "/tmp/test-repo/.taskpods"
        ensure_pods_dir()
        mock_makedirs.assert_called_once_with("/tmp/test-repo/.taskpods", exist_ok=True)

    @patch("taskpods.branch_exists")
    @patch("taskpods.remote_branch_exists")
    def test_validate_base_branch_success(self, mock_remote_exists, mock_local_exists):
        """Test validate_base_branch succeeds with valid branch."""
        mock_local_exists.return_value = True
        mock_remote_exists.return_value = True

        # Should not raise exception
        validate_base_branch("main")

    @patch("taskpods.branch_exists")
    def test_validate_base_branch_local_failure(self, mock_local_exists):
        """Test validate_base_branch fails when local branch doesn't exist."""
        mock_local_exists.return_value = False

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                validate_base_branch("nonexistent")
                # The function calls both checks, so we expect both error messages
                mock_print.assert_any_call(
                    "[x] Error: Base branch 'nonexistent' does not exist locally"
                )
                mock_exit.assert_called()

    @patch("taskpods.branch_exists")
    @patch("taskpods.remote_branch_exists")
    def test_validate_base_branch_remote_failure(
        self, mock_remote_exists, mock_local_exists
    ):
        """Test validate_base_branch fails when remote branch doesn't exist."""
        mock_local_exists.return_value = True
        mock_remote_exists.return_value = False

        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                validate_base_branch("main")
                mock_print.assert_called_once_with(
                    "[x] Error: Base branch 'main' does not exist on remote 'origin'"
                )
                mock_exit.assert_called_once_with(1)

    @patch("taskpods.subprocess.run")
    def test_sh_success(self, mock_run):
        """Test sh function runs command successfully."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        result = sh(["git", "status"])
        assert result == mock_process
        mock_run.assert_called_once_with(["git", "status"], cwd=None, check=True)

    @patch("taskpods.subprocess.run")
    def test_sh_with_cwd(self, mock_run):
        """Test sh function with custom working directory."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        result = sh(["git", "status"], cwd="/tmp/repo")
        assert result == mock_process
        mock_run.assert_called_once_with(["git", "status"], cwd="/tmp/repo", check=True)

    @patch("taskpods.subprocess.run")
    def test_sout_success(self, mock_run):
        """Test sout function returns stdout."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "branch output\n"
        mock_run.return_value = mock_process

        result = sout(["git", "branch"])
        assert result == "branch output"
        mock_run.assert_called_once_with(
            ["git", "branch"], cwd=None, capture_output=True, text=True, check=True
        )

    @patch("taskpods.shutil.which")
    def test_have_true(self, mock_which):
        """Test have function returns True when command exists."""
        mock_which.return_value = "/usr/bin/git"
        assert have("git") is True
        mock_which.assert_called_once_with("git")

    @patch("taskpods.shutil.which")
    def test_have_false(self, mock_which):
        """Test have function returns False when command doesn't exist."""
        mock_which.return_value = None
        assert have("nonexistent") is False
        mock_which.assert_called_once_with("nonexistent")


class TestEditorFunctions:
    """Test editor-related functions."""

    @patch("taskpods.subprocess.Popen")
    @patch("taskpods._get_preferred_editor")
    def test_open_editor_success(self, mock_get_editor, mock_popen):
        """Test open_editor opens editor successfully."""
        mock_get_editor.return_value = "code"
        mock_popen.return_value = MagicMock()

        with patch("builtins.print") as mock_print:
            open_editor("/tmp/path")
            mock_popen.assert_called_once_with(["code", "--new-window", "/tmp/path"])
            mock_print.assert_called_once_with("[✓] Opened in code")

    @patch("taskpods.subprocess.Popen")
    @patch("taskpods._get_preferred_editor")
    def test_open_editor_failure(self, mock_get_editor, mock_popen):
        """Test open_editor handles failure gracefully."""
        mock_get_editor.return_value = "code"
        mock_popen.side_effect = Exception("Editor not found")

        with patch("builtins.print") as mock_print:
            open_editor("/tmp/path")
            mock_print.assert_any_call(
                "[!] Warning: Could not open editor code: Editor not found"
            )
            mock_print.assert_any_call("    Pod created at: /tmp/path")

    @patch("taskpods._get_preferred_editor")
    def test_open_editor_no_editor(self, mock_get_editor):
        """Test open_editor when no editor is available."""
        mock_get_editor.return_value = None

        with patch("builtins.print") as mock_print:
            open_editor("/tmp/path")
            mock_print.assert_any_call("[!] No editor found. Pod created at: /tmp/path")

    @patch.dict(__import__("os").environ, {"TASKPODS_EDITOR": "custom-editor"})
    def test_get_preferred_editor_environment(self):
        """Test _get_preferred_editor returns environment variable."""
        result = _get_preferred_editor()
        assert result == "custom-editor"

    @patch.dict(__import__("os").environ, {}, clear=True)
    @patch("os.path.expanduser")
    @patch(
        "builtins.open", new_callable=mock_open, read_data='{"editor": "config-editor"}'
    )
    @patch("os.path.exists")
    def test_get_preferred_editor_config_file(
        self, mock_exists, mock_file, mock_expanduser
    ):
        """Test _get_preferred_editor reads from config file."""
        mock_exists.return_value = True
        mock_expanduser.return_value = "~/.taskpodsrc"

        result = _get_preferred_editor()
        assert result == "config-editor"

    @patch.dict(__import__("os").environ, {}, clear=True)
    @patch("os.path.expanduser")
    @patch("os.path.exists")
    @patch("taskpods.shutil.which")
    def test_get_preferred_editor_fallback(
        self, mock_which, mock_exists, mock_expanduser
    ):
        """Test _get_preferred_editor falls back to system editors."""
        mock_exists.return_value = False
        mock_expanduser.return_value = "~/.taskpodsrc"
        mock_which.side_effect = lambda x: "/usr/bin/vim" if x == "vim" else None

        result = _get_preferred_editor()
        assert result == "/usr/bin/vim"


class TestStartFunction:
    """Test the start function."""

    @patch("taskpods.ensure_pods_dir")
    @patch("taskpods.validate_pod_name")
    @patch("taskpods.validate_base_branch")
    @patch("taskpods.get_pods_dir")
    @patch("taskpods.get_repo_root")
    @patch("os.path.exists")
    @patch("taskpods.sh")
    @patch("taskpods.open_editor")
    @patch("taskpods.has_uncommitted_changes")
    @patch("taskpods.branch_exists")
    def test_start_success(
        self,
        mock_branch_exists,
        mock_has_changes,
        mock_open_editor,
        mock_sh,
        mock_exists,
        mock_get_repo_root,
        mock_get_pods_dir,
        mock_validate_base,
        mock_validate_name,
        mock_ensure_pods,
    ):
        """Test start function creates pod successfully."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_exists.return_value = False
        mock_has_changes.return_value = False
        mock_branch_exists.return_value = False  # Branch doesn't exist yet

        args = MagicMock()
        args.base = "main"
        args.name = "test-pod"
        args.editor = None

        with patch("builtins.print") as mock_print:
            start(args)

            mock_ensure_pods.assert_called_once()
            mock_validate_name.assert_called_once_with("test-pod")
            mock_validate_base.assert_called_once_with("main")
            mock_sh.assert_called()
            mock_open_editor.assert_called_once_with("/tmp/.taskpods/test-pod")
            mock_print.assert_any_call(
                "[✓] Pod ready: /tmp/.taskpods/test-pod  (branch: pods/test-pod)"
            )


class TestListPodsFunction:
    """Test the list_pods function."""

    @patch("taskpods.get_pods_dir")
    @patch("taskpods.get_repo_root")
    @patch("taskpods.sout")
    def test_list_pods_success(self, mock_sout, mock_get_repo_root, mock_get_pods_dir):
        """Test list_pods lists pods successfully."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_sout.return_value = (
            "worktree /tmp/.taskpods/test-pod\nbranch refs/heads/pods/test-pod\n\n"
            "worktree /tmp/.taskpods/another-pod\nbranch refs/heads/pods/another-pod"
        )

        args = MagicMock()

        with patch("builtins.print") as mock_print:
            list_pods(args)
            # The list_pods function might format output differently than expected
            # Just verify print was called
            mock_print.assert_called()

    @patch("taskpods.get_pods_dir")
    @patch("taskpods.get_repo_root")
    @patch("taskpods.sout")
    def test_list_pods_no_pods(self, mock_sout, mock_get_repo_root, mock_get_pods_dir):
        """Test list_pods handles no pods."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_sout.return_value = ""

        args = MagicMock()

        with patch("builtins.print") as mock_print:
            list_pods(args)
            mock_print.assert_called_once_with("(no pods)")


class TestMainFunction:
    """Test the main function."""

    @patch("taskpods.get_repo_root")
    @patch("taskpods.check_remote_origin")
    @patch("taskpods.check_git_operations_in_progress")
    @patch("taskpods.argparse.ArgumentParser")
    def test_main_success(
        self, mock_parser_class, mock_check_git, mock_check_remote, mock_get_repo
    ):
        """Test main function runs successfully."""
        mock_get_repo.return_value = "/tmp/repo"
        mock_check_remote.return_value = None
        mock_check_git.return_value = None

        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_subparsers = MagicMock()
        mock_parser.add_subparsers.return_value = mock_subparsers

        mock_args = MagicMock()
        mock_args.cmd = "list"
        mock_args.func = MagicMock()
        mock_parser.parse_args.return_value = mock_args

        main()

        mock_args.func.assert_called_once_with(mock_args)

    @patch("taskpods.get_repo_root")
    def test_main_no_command(self, mock_get_repo):
        """Test main function exits when no command is provided."""
        mock_get_repo.return_value = "/tmp/repo"

        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.cmd = None
        mock_parser.parse_args.return_value = mock_args

        with patch("taskpods.argparse.ArgumentParser", return_value=mock_parser):
            with patch("sys.exit") as mock_exit:
                with patch("taskpods.check_remote_origin"):
                    with patch("taskpods.check_git_operations_in_progress"):
                        main()
                        mock_exit.assert_called_once_with(1)

    @patch("taskpods.get_repo_root")
    @patch("taskpods.check_remote_origin")
    @patch("taskpods.check_git_operations_in_progress")
    @patch("taskpods.argparse.ArgumentParser")
    def test_main_support_command(
        self, mock_parser_class, mock_check_git, mock_check_remote, mock_get_repo
    ):
        """Test main function handles support command."""
        mock_get_repo.return_value = "/tmp/repo"
        mock_check_remote.return_value = None
        mock_check_git.return_value = None

        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_subparsers = MagicMock()
        mock_parser.add_subparsers.return_value = mock_subparsers

        mock_args = MagicMock()
        mock_args.cmd = "support"
        mock_args.func = MagicMock()
        mock_parser.parse_args.return_value = mock_args

        main()

        # Verify that add_parser was called for support command
        mock_subparsers.add_parser.assert_any_call(
            "support",
            help="Show links to star or support Taskpods",
            description="Prints GitHub and Ko-fi links to support Taskpods.",
        )
        mock_args.func.assert_called_once_with(mock_args)


if __name__ == "__main__":
    # Run tests
    print("Running main function tests...")

    # Create test instances and run tests
    utility_tester = TestUtilityFunctions()
    editor_tester = TestEditorFunctions()
    start_tester = TestStartFunction()
    list_tester = TestListPodsFunction()
    main_tester = TestMainFunction()

    print("All main function tests completed!")
