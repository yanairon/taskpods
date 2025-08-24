# Release Script

A production-grade, automated release script for taskpods that handles version management, changelog updates, and Git operations.

## 🚀 Features

- **Automatic Version Incrementing**: Semantic versioning (major.minor.patch)
- **Manual Version Specification**: Set exact version numbers
- **Changelog Management**: Automatic CHANGELOG.md updates
- **Git Integration**: Automated commit, tag, and push operations
- **Quality Assurance**: Pre-release testing and linting
- **Validation**: Comprehensive release validation
- **CI/CD Integration**: Works with GitHub Actions workflows

## 📋 Prerequisites

- Python 3.7+
- Git repository with proper remote configuration
- `make` command available (for tests and linting)
- `packaging` Python package installed

## 🛠️ Installation

1. **Install dependencies**:
   ```bash
   pip install packaging
   ```

2. **Make script executable**:
   ```bash
   chmod +x scripts/release.py
   ```

## 📖 Usage

### Basic Commands

```bash
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
```

### Advanced Options

```bash
# Skip tests and linting (use with caution)
python scripts/release.py --type patch --skip-tests

# Dry run (show what would happen without making changes)
python scripts/release.py --type patch --dry-run

# Combine options
python scripts/release.py --type minor --description "New features" --dry-run
```

## 🔄 Release Process

The script follows this workflow:

1. **Validation**:
   - Check Git status (must be on main branch)
   - Verify no uncommitted changes
   - Ensure remote is up to date

2. **Quality Checks**:
   - Run test suite
   - Run linting checks
   - Validate code quality

3. **File Updates**:
   - Update version in `pyproject.toml`
   - Update `CHANGELOG.md` with new version entry

4. **Git Operations**:
   - Commit release changes
   - Push to remote main branch
   - Create and push version tag

5. **CI/CD Trigger**:
   - GitHub Actions automatically builds and publishes to PyPI
   - Creates GitHub release with changelog

## 📁 File Structure

```
scripts/
├── release.py          # Main release script
├── README.md          # This documentation
└── __init__.py        # Package initialization
```

## ⚙️ Configuration

The script automatically detects:
- Project root directory
- `pyproject.toml` location
- `CHANGELOG.md` location
- Git repository status

## 🧪 Testing

### Dry Run
```bash
python scripts/release.py --type patch --dry-run
```

### Skip Quality Checks
```bash
python scripts/release.py --type patch --skip-tests
```

## 🚨 Error Handling

The script includes comprehensive error handling:

- **Validation Errors**: Git status, branch checks, file existence
- **Quality Failures**: Test failures, linting issues
- **Git Errors**: Commit, push, or tag failures
- **File Errors**: Version or changelog update failures

## 🔧 Customization

### Adding Custom Validation
Extend the `ReleaseManager` class to add custom validation logic:

```python
def custom_validation(self):
    """Add custom validation logic."""
    # Your custom validation here
    pass
```

### Custom Release Steps
Override the `release` method to add custom steps:

```python
def release(self, new_version: str, description: Optional[str] = None, skip_tests: bool = False):
    # Custom pre-release steps
    self.custom_validation()
    
    # Standard release process
    super().release(new_version, description, skip_tests)
    
    # Custom post-release steps
    self.notify_team(new_version)
```

## 📚 Examples

### Patch Release
```bash
python scripts/release.py --type patch --description "Bug fixes and security updates"
```

### Minor Release
```bash
python scripts/release.py --type minor --description "New features and improvements"
```

### Major Release
```bash
python scripts/release.py --type major --description "Breaking changes and major features"
```

### Hotfix Release
```bash
python scripts/release.py --version 0.1.1 --description "Critical security fix"
```

## 🎯 Best Practices

1. **Always use dry-run first** for important releases
2. **Write descriptive release descriptions** for changelog
3. **Run on main branch** with clean working directory
4. **Review changes** before confirming release
5. **Monitor CI/CD pipeline** after release

## 🆘 Troubleshooting

### Common Issues

**"Must be on main branch"**
- Switch to main branch: `git checkout main`
- Pull latest changes: `git pull origin main`

**"Working directory has uncommitted changes"**
- Commit changes: `git add . && git commit -m "message"`
- Or stash changes: `git stash`

**"Tests failed"**
- Fix test failures before releasing
- Use `--skip-tests` only for emergency releases

**"Linting failed"**
- Fix linting issues before releasing
- Use `--skip-tests` only for emergency releases

### Getting Help

```bash
# Show help
python scripts/release.py --help

# Check script version
python scripts/release.py --version
```

## 🤝 Contributing

To improve the release script:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This script is part of the taskpods project and follows the same license terms.
