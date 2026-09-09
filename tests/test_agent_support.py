"""Test suite for agent support, base resolution, and pods-dir exclusion."""

import argparse
import sys
from unittest.mock import MagicMock, patch

# Add repository root to sys.path to ensure taskpods.py can be imported
repo_root = __import__("os").path.dirname(__import__("os").path.dirname(__file__))
sys.path.insert(0, __import__("os").path.abspath(repo_root))

# Import after path modification
from taskpods import (  # noqa: E402
    _get_default_base,
    _get_preferred_agent,
    _resolve_agent,
    ensure_pods_excluded,
    run_agent,
    start,
)


class TestGetPreferredAgent:
    """Test agent command resolution from env and config."""

    @patch.dict(__import__("os").environ, {"TASKPODS_AGENT": "claude -p"})
    def test_env_var_splits_command(self):
        """Test TASKPODS_AGENT is split shell-style."""
        assert _get_preferred_agent() == ["claude", "-p"]

    @patch.dict(__import__("os").environ, {}, clear=True)
    @patch("taskpods._load_config")
    def test_config_string(self, mock_config):
        """Test config 'agent' string is split shell-style."""
        mock_config.return_value = {"agent": "codex exec --sandbox workspace-write"}
        assert _get_preferred_agent() == [
            "codex",
            "exec",
            "--sandbox",
            "workspace-write",
        ]

    @patch.dict(__import__("os").environ, {}, clear=True)
    @patch("taskpods._load_config")
    def test_config_list(self, mock_config):
        """Test config 'agent' list is used as-is."""
        mock_config.return_value = {"agent": ["opencode", "run"]}
        assert _get_preferred_agent() == ["opencode", "run"]

    @patch.dict(__import__("os").environ, {}, clear=True)
    @patch("taskpods._load_config")
    def test_no_agent_configured(self, mock_config):
        """Test None when no agent is configured anywhere."""
        mock_config.return_value = {}
        assert _get_preferred_agent() is None


class TestResolveAgent:
    """Test CLI flag precedence over env/config."""

    def test_cli_remainder_wins(self):
        """Test --agent arguments are used when given."""
        args = argparse.Namespace(agent=["claude", "-p", "fix it"])
        assert _resolve_agent(args) == ["claude", "-p", "fix it"]

    @patch("taskpods._get_preferred_agent")
    def test_env_fallback(self, mock_preferred):
        """Test env/config agent is used when --agent is absent."""
        mock_preferred.return_value = ["gemini", "-p"]
        args = argparse.Namespace(agent=None)
        assert _resolve_agent(args) == ["gemini", "-p"]

    def test_empty_remainder_warns(self):
        """Test bare --agent prints a warning and resolves to None."""
        args = argparse.Namespace(agent=[])
        with patch("builtins.print") as mock_print:
            assert _resolve_agent(args) is None
            mock_print.assert_called_once()


class TestGetDefaultBase:
    """Test default base branch resolution."""

    @patch("taskpods._load_config")
    def test_config_default_base(self, mock_config):
        """Test default_base from config is honored."""
        mock_config.return_value = {"default_base": "develop"}
        assert _get_default_base() == "develop"

    @patch("taskpods._load_config")
    def test_fallback_main(self, mock_config):
        """Test fallback to main when not configured."""
        mock_config.return_value = {}
        assert _get_default_base() == "main"


class TestRunAgent:
    """Test agent execution inside a pod."""

    @patch("taskpods.subprocess.call")
    def test_runs_in_worktree(self, mock_call):
        """Test the agent command runs with the pod as cwd."""
        mock_call.return_value = 0
        code = run_agent(["claude", "-p", "hi"], "/tmp/.taskpods/x")
        assert code == 0
        mock_call.assert_called_once_with(
            ["claude", "-p", "hi"], cwd="/tmp/.taskpods/x"
        )

    @patch("taskpods.subprocess.call")
    def test_missing_command_returns_127(self, mock_call):
        """Test a missing agent binary returns 127."""
        mock_call.side_effect = FileNotFoundError()
        with patch("builtins.print"):
            assert run_agent(["no-such-agent"], "/tmp/x") == 127


class TestEnsurePodsExcluded:
    """Test .git/info/exclude handling for the pods directory."""

    @patch("taskpods.get_repo_root")
    def test_skips_inside_worktree(self, mock_root, tmp_path):
        """Test nothing happens when .git is a file (linked worktree)."""
        (tmp_path / ".git").write_text("gitdir: /elsewhere")
        mock_root.return_value = str(tmp_path)
        ensure_pods_excluded()
        assert not (tmp_path / ".git" / "info").exists()

    @patch("taskpods.get_repo_root")
    def test_adds_entry_when_missing(self, mock_root, tmp_path):
        """Test .taskpods/ is appended to .git/info/exclude."""
        (tmp_path / ".git" / "info").mkdir(parents=True)
        exclude = tmp_path / ".git" / "info" / "exclude"
        exclude.write_text("# default\n")
        mock_root.return_value = str(tmp_path)
        ensure_pods_excluded()
        assert ".taskpods/" in exclude.read_text().splitlines()

    @patch("taskpods.get_repo_root")
    def test_no_duplicate_entry(self, mock_root, tmp_path):
        """Test an existing entry is not duplicated."""
        (tmp_path / ".git" / "info").mkdir(parents=True)
        exclude = tmp_path / ".git" / "info" / "exclude"
        exclude.write_text("# default\n.taskpods/\n")
        mock_root.return_value = str(tmp_path)
        ensure_pods_excluded()
        assert exclude.read_text().splitlines().count(".taskpods/") == 1


class TestStartWithAgent:
    """Test start() agent integration."""

    @patch("taskpods.run_agent")
    @patch("taskpods.ensure_pods_excluded")
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
    def test_agent_runs_and_skips_editor(
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
        mock_ensure_excluded,
        mock_run_agent,
    ):
        """Test --agent runs in the pod, skips the editor, exits with its code."""
        mock_get_pods_dir.return_value = "/tmp/.taskpods"
        mock_get_repo_root.return_value = "/tmp/repo"
        mock_exists.return_value = False
        mock_has_changes.return_value = False
        mock_branch_exists.return_value = False
        mock_run_agent.return_value = 0

        args = MagicMock()
        args.base = None
        args.name = "test-pod"
        args.editor = None
        args.agent = ["claude", "-p", "fix typos"]

        with patch("builtins.print"), patch("taskpods._load_config") as mock_cfg:
            mock_cfg.return_value = {}
            try:
                start(args)
                raise AssertionError("start should exit with the agent code")
            except SystemExit as e:
                assert e.code == 0

        mock_run_agent.assert_called_once_with(
            ["claude", "-p", "fix typos"], "/tmp/.taskpods/test-pod"
        )
        mock_open_editor.assert_not_called()
        mock_validate_base.assert_called_once_with("main")
