#!/usr/bin/env python3
"""
Production-grade release script for taskpods.

This script automates the release process including:
- Version management (auto-increment or manual specification)
- Changelog updates
- Git operations (commit, tag, push)
- Release validation
- Integration with CI/CD workflows

Usage:
    python scripts/release.py [--version VERSION] [--type TYPE] [--description DESCRIPTION]
    python scripts/release.py --help

Examples:
    # Auto-increment patch version (0.1.0 -> 0.1.1)
    python scripts/release.py --type patch

    # Auto-increment minor version (0.1.0 -> 0.2.0)
    python scripts/release.py --type minor

    # Auto-increment major version (0.1.0 -> 1.0.0)
    python scripts/release.py --type major

    # Specify exact version
    python scripts/release.py --version 0.2.0

    # Add release description
    python scripts/release.py --type patch --description "Bug fixes and improvements"
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from packaging import version as pkg_version


class ReleaseError(Exception):
    """Custom exception for release-related errors."""

    pass


class ReleaseManager:
    """Manages the release process for taskpods."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.pyproject_path = project_root / "pyproject.toml"
        self.changelog_path = project_root / "CHANGELOG.md"
        self.scripts_dir = project_root / "scripts"

        # Validate project structure
        if not self.pyproject_path.exists():
            raise ReleaseError(f"pyproject.toml not found at {self.pyproject_path}")
        if not self.changelog_path.exists():
            raise ReleaseError(f"CHANGELOG.md not found at {self.changelog_path}")

    def get_current_version(self) -> str:
        """Extract current version from pyproject.toml."""
        content = self.pyproject_path.read_text()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise ReleaseError("Could not find version in pyproject.toml")
        return match.group(1)

    def update_version(self, new_version: str) -> None:
        """Update version in pyproject.toml."""
        content = self.pyproject_path.read_text()
        updated_content = re.sub(r'(version\s*=\s*["\'])[^"\']+(["\'])', rf'\g<1>{new_version}\g<2>', content)
        self.pyproject_path.write_text(updated_content)
        print(f"✅ Updated version to {new_version} in pyproject.toml")

    def calculate_next_version(self, version_type: str) -> str:
        """Calculate next version based on semantic versioning."""
        current = pkg_version.parse(self.get_current_version())

        if version_type == "major":
            return f"{current.major + 1}.0.0"
        elif version_type == "minor":
            return f"{current.major}.{current.minor + 1}.0"
        elif version_type == "patch":
            return f"{current.major}.{current.minor}.{current.micro + 1}"
        else:
            raise ReleaseError(f"Invalid version type: {version_type}")

    def update_changelog(self, new_version: str, description: Optional[str] = None) -> None:
        """Update CHANGELOG.md with new version entry."""
        content = self.changelog_path.read_text()

        # Create new version entry
        today = datetime.now().strftime("%Y-%m-%d")
        version_header = f"## [{new_version}] - {today}"

        if description:
            version_content = f"{version_header}\n\n{description}\n\n"
        else:
            version_content = f"{version_header}\n\n### Added\n- Release {new_version}\n\n"

        # Insert after the header and before [Unreleased]
        lines = content.split('\n')
        insert_index = None

        for i, line in enumerate(lines):
            if line.startswith('## [Unreleased]'):
                insert_index = i
                break

        if insert_index is None:
            # If no [Unreleased] section, insert after the header
            for i, line in enumerate(lines):
                if line.startswith('## [') and i > 0:
                    insert_index = i
                    break

        if insert_index is None:
            insert_index = 2  # Default to after header

        lines.insert(insert_index, version_content)
        self.changelog_path.write_text('\n'.join(lines))
        print(f"✅ Updated CHANGELOG.md with version {new_version}")

    def validate_git_status(self) -> None:
        """Validate Git repository status before release."""
        # Check if we're on main branch
        current_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=self.project_root
        ).stdout.strip()

        if current_branch != "main":
            raise ReleaseError(f"Must be on main branch, currently on {current_branch}")

        # Check for uncommitted changes
        status = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=self.project_root
        ).stdout.strip()

        if status:
            raise ReleaseError("Working directory has uncommitted changes. Please commit or stash them first.")

        # Check if remote is up to date
        subprocess.run(["git", "fetch", "origin"], check=True, cwd=self.project_root)

        local_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=self.project_root
        ).stdout.strip()

        remote_commit = subprocess.run(
            ["git", "rev-parse", "origin/main"], capture_output=True, text=True, cwd=self.project_root
        ).stdout.strip()

        if local_commit != remote_commit:
            raise ReleaseError("Local main branch is not up to date with remote. Please pull latest changes.")

    def run_tests(self) -> None:
        """Run the test suite to ensure quality before release."""
        print("🧪 Running tests...")
        try:
            subprocess.run(["make", "test"], check=True, cwd=self.project_root)
            print("✅ All tests passed")
        except subprocess.CalledProcessError:
            raise ReleaseError("Tests failed. Please fix all test failures before releasing.")

    def run_linting(self) -> None:
        """Run linting checks to ensure code quality."""
        print("🔍 Running linting checks...")
        try:
            subprocess.run(["make", "lint"], check=True, cwd=self.project_root)
            print("✅ All linting checks passed")
        except subprocess.CalledProcessError:
            raise ReleaseError("Linting failed. Please fix all linting issues before releasing.")

    def commit_release(self, new_version: str) -> None:
        """Commit release changes."""
        commit_message = f"chore: prepare for v{new_version} release"

        subprocess.run(["git", "add", "pyproject.toml", "CHANGELOG.md"], check=True, cwd=self.project_root)

        subprocess.run(["git", "commit", "-m", commit_message], check=True, cwd=self.project_root)
        print(f"✅ Committed release changes for v{new_version}")

    def create_tag(self, new_version: str) -> None:
        """Create and push Git tag."""
        tag_name = f"v{new_version}"

        # Create tag
        subprocess.run(["git", "tag", tag_name], check=True, cwd=self.project_root)
        print(f"✅ Created tag {tag_name}")

        # Push tag
        subprocess.run(["git", "push", "origin", tag_name], check=True, cwd=self.project_root)
        print(f"✅ Pushed tag {tag_name} to remote")

    def push_changes(self) -> None:
        """Push release changes to remote."""
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=self.project_root)
        print("✅ Pushed release changes to remote")

    def validate_release(self, new_version: str) -> None:
        """Validate the release configuration."""
        print(f"🔍 Validating release configuration for v{new_version}...")

        # Check if version was updated
        current_version = self.get_current_version()
        if current_version != new_version:
            raise ReleaseError(f"Version mismatch: expected {new_version}, got {current_version}")

        # Check if changelog was updated
        changelog_content = self.changelog_path.read_text()
        if f"[{new_version}]" not in changelog_content:
            raise ReleaseError(f"Changelog not updated for version {new_version}")

        print("✅ Release validation passed")

    def release(self, new_version: str, description: Optional[str] = None, skip_tests: bool = False) -> None:
        """Execute the complete release process."""
        print(f"🚀 Starting release process for v{new_version}")
        print("=" * 50)

        try:
            # Pre-release validation
            if not skip_tests:
                self.validate_git_status()
                self.run_tests()
                self.run_linting()

            # Update files
            self.update_version(new_version)
            self.update_changelog(new_version, description)

            # Validate changes
            self.validate_release(new_version)

            # Git operations
            self.commit_release(new_version)
            self.push_changes()
            self.create_tag(new_version)

            print("=" * 50)
            print(f"🎉 Successfully released v{new_version}!")
            print(f"📦 Package will be automatically built and published to PyPI")
            print(f"🏷️  GitHub release will be created automatically")
            print(f"🔗 Check GitHub Actions for build progress")

        except Exception as e:
            print(f"❌ Release failed: {e}")
            print("💡 You may need to manually clean up any partial changes")
            sys.exit(1)


def main():
    """Main entry point for the release script."""
    parser = argparse.ArgumentParser(
        description="Production-grade release script for taskpods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--version", help="Specify exact version (e.g., 0.2.0)")

    parser.add_argument("--type", choices=["major", "minor", "patch"], help="Auto-increment version type")

    parser.add_argument("--description", help="Release description for changelog")

    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests and linting (use with caution)")

    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    args = parser.parse_args()

    # Validate arguments
    if not args.version and not args.type:
        parser.error("Must specify either --version or --type")

    if args.version and args.type:
        parser.error("Cannot specify both --version and --type")

    # Initialize release manager
    try:
        project_root = Path(__file__).parent.parent
        manager = ReleaseManager(project_root)
    except ReleaseError as e:
        print(f"❌ Initialization failed: {e}")
        sys.exit(1)

    # Determine new version
    if args.version:
        new_version = args.version
    else:
        current_version = manager.get_current_version()
        new_version = manager.calculate_next_version(args.type)
        print(f"📈 Current version: {current_version}")
        print(f"📈 New version: {new_version}")

    # Confirm release
    if not args.dry_run:
        response = input(f"\n🤔 Proceed with release v{new_version}? (y/N): ")
        if response.lower() != 'y':
            print("❌ Release cancelled")
            sys.exit(0)

    # Execute release
    if args.dry_run:
        print(f"🔍 DRY RUN: Would release v{new_version}")
        print(f"🔍 Would update pyproject.toml and CHANGELOG.md")
        print(f"🔍 Would create and push tag v{new_version}")
    else:
        manager.release(new_version, args.description, args.skip_tests)


if __name__ == "__main__":
    main()
