import os
import sys

# Add repository root to sys.path to ensure taskpods.py can be imported when running tests
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from taskpods import branch_exists, remote_branch_exists

def test_branch_exists_true_for_main():
    # main branch should exist in the repository
    assert branch_exists("main") is True

def test_branch_exists_false_for_nonexistent():
    # Nonexistent branch should return False without printing fatal error
    assert branch_exists("this-branch-does-not-exist") is False

def test_remote_branch_exists_false_for_nonexistent():
    # remote branch existence check should return False for a nonexistent branch
    assert remote_branch_exists("this-branch-does-not-exist") is False
