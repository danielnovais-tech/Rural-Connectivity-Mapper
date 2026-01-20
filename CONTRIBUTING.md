# Contributing to Rural Connectivity Mapper 2026

Thank you for your interest in contributing to the Rural Connectivity Mapper 2026! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pip package manager

### Development Setup

1. **Fork and Clone**

   ```bash
   git clone https://github.com/YOUR_USERNAME/Rural-Connectivity-Mapper-2026.git
   cd Rural-Connectivity-Mapper-2026
   ```

2. **Create Virtual Environment** (Recommended)

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Verify Setup**

   ```bash
   pytest tests/ -v
   ```

## 📋 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/amazing-feature
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write clean, documented code
- Follow existing code style and conventions
- Add docstrings (Google-style) to functions and classes

### 3. Write Tests

- Add tests for new features
- Ensure existing tests still pass
- Aim for 80%+ code coverage

```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### 4. Run Linters

```bash
# Ruff (fast Python linter)
ruff check .

# Flake8 (code style checker)
flake8 src/ tests/ main.py demo_workflow.py
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add amazing feature"
```

**Commit Message Format:**

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/modifications
- `refactor:` - Code refactoring
- `style:` - Formatting changes
- `chore:` - Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/amazing-feature
```

Then create a Pull Request on GitHub.

## 🧪 Testing Guidelines (Quick Start)

### Writing Tests (Quick Start)

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names that explain what is being tested

### Test Structure

```python
def test_feature_description():
    """Brief description of what this test verifies."""
    # Arrange - Set up test data
    input_data = {...}
    
    # Act - Execute the function
    result = function_to_test(input_data)
    
    # Assert - Verify the result
    assert result == expected_value
```

### Running Tests (Quick Start)

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_models.py -v

# Specific test
pytest tests/test_models.py::test_connectivity_point_creation -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## 🎨 Code Style Guidelines

### Python Style

- Follow PEP 8 style guide
- Maximum line length: 120 characters
- Use meaningful variable and function names
- Add type hints where appropriate

### Documentation (Code Style)

- All public functions must have docstrings
- Use Google-style docstrings
- Include examples for complex functions

## Contributing to Rural Connectivity Mapper

Thank you for your interest in contributing to the Rural Connectivity Mapper project! We welcome contributions from the community to help improve rural connectivity analysis in Brazil.

## 🤝 How to Contribute

### Reporting Bugs (Overview)

If you find a bug, please create an issue using our [Bug Report template](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues/new/choose). Make sure to include:

- A clear description of the bug
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment details (OS, Python version, etc.)
- **Estimated Effort** for fixing the bug

### Suggesting Features (Overview)

We love new ideas! Please create a [Feature Request](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues/new/choose) with:

- A clear problem statement
- Your proposed solution
- Alternative approaches you've considered
- **Estimated Effort** for implementation
- Priority level

### Submitting Pull Requests

1. Fork the repository and create a new branch from `main`

   ```bash
   git checkout -b feature/amazing-feature
   ```

2. Make your changes following our coding standards (see below)

3. **Run tests** to ensure everything works

   ```bash
   pytest tests/ -v
   ```

4. **Commit your changes** with clear, descriptive messages

   ```bash
   git commit -m "Add feature: description of what you added"
   ```

5. **Push to your fork** and submit a Pull Request

   ```bash
   git push origin feature/amazing-feature
   ```

## 📏 Estimated Effort Guidelines

To help with planning and task assignment, we use an effort estimation system. When creating issues or planning work, use these guidelines:

### Effort Levels

| Level | Time Range | Description | Examples |
| ------- | ----------- | ------------- | ---------- |
| **S (Small)** | < 2 hours | Minor fixes, simple updates | Fix typo, update dependency version, add docstring |
| **M (Medium)** | 2-8 hours | Moderate features or fixes | Add new utility function, fix complex bug, improve validation |
| **L (Large)** | > 8 hours (1-3 days) | Significant features or refactoring | New CLI command, major algorithm improvement, comprehensive docs |
| **XL (Extra Large)** | > 1 week | Major features or architecture changes | New data model, web dashboard, ML integration, API development |

### How to Estimate

1. **Break down the task** into smaller subtasks
2. **Consider all aspects**:
   - Writing code
   - Writing tests
   - Writing documentation
   - Code review iterations
   - Testing and validation
3. **Add buffer time** for unforeseen issues (20-30%)
4. **If uncertain**, choose "Unknown" and we'll help estimate

### Effort in Hours (Alternative)

If you prefer hours over S/M/L/XL, you can also estimate in hours:

- List specific tasks and their time estimates
- Include testing, documentation, and review time
- Example: "Implementation: 3h, Tests: 2h, Docs: 1h = Total: 6h (Medium)"

## 💻 Development Guidelines

### Code Style

- Follow **PEP 8** style guide for Python code
- Use **Google-style docstrings** for all functions and classes
- Keep functions focused and under 50 lines when possible
- Use meaningful variable and function names

#### Example

```python
def calculate_quality_score(speed_test: SpeedTest) -> float:
    """Calculate quality score from speed test results.
    
    Args:
        speed_test: SpeedTest instance with measurement data
        
    Returns:
        Quality score from 0 to 100
        
    Example:
        >>> st = SpeedTest(download=150.0, upload=18.0, latency=25.0)
        >>> score = calculate_quality_score(st)
        >>> print(score)
        92.5

Thank you for your interest in contributing to the Rural Connectivity Mapper 2026! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Coding Standards](#coding-standards)
5. [Pull Request Process](#pull-request-process)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How Can I Contribute?

### Reporting Bugs (Detailed)

- Use the [GitHub Issues](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues) page
- Search existing issues to avoid duplicates
- Provide detailed reproduction steps
- Include your environment details (Python version, OS, etc.)

### Suggesting Enhancements

- Check the [project roadmap](README.md#-roadmap) first
- Open a GitHub issue with the `enhancement` label
- Clearly describe the proposed feature and its benefits
- Explain how it aligns with the project's goals

### Contributing Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following our coding standards
4. Write or update tests
5. Run the full test suite
6. Commit your changes with clear messages
7. Push to your fork
8. Submit a Pull Request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/Rural-Connectivity-Mapper-2026.git
cd Rural-Connectivity-Mapper-2026

# Add upstream remote
git remote add upstream https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026.git

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if any)
pip install pytest pytest-cov
```

### Running the Application

```bash
# Run demo workflow
python demo_workflow.py

# Run CLI
python main.py --help
```

## Coding Standards

### Python Style Guide

- **Follow PEP 8** - Use consistent Python style conventions
- **Line length:** Maximum 79 characters for code, 72 for comments (per PEP 8)
- **Indentation:** 4 spaces (no tabs)
- **Naming conventions:**
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_CASE`

### Documentation

- **Docstrings:** Use Google-style docstrings for all public functions and classes

Example:

```python
def calculate_quality_score(download: float, upload: float, latency: float) -> float:

    """Calculate connectivity quality score.

    """Calculate overall connectivity quality score.

    Args:
        download: Download speed in Mbps
        upload: Upload speed in Mbps
        latency: Latency in milliseconds

    
    Returns:
        Quality score from 0-100
    
    Examples:
        >>> calculate_quality_score(100, 20, 30)
        85.5
    """
    # Implementation here
```

### Imports

- Group imports: standard library, third-party, local
- Use absolute imports
- Sort imports alphabetically within groups

## 🔄 CI/CD Pipeline

### Automated Checks

All pull requests automatically run:

1. **Tests** - Across Python 3.8, 3.9, 3.10, 3.11, 3.12
2. **Linting** - Ruff and Flake8 code quality checks
3. **Coverage** - Code coverage analysis

### What Happens When You Submit a PR

1. CI workflow runs tests on multiple Python versions
2. Lint workflow checks code quality
3. Coverage report is generated
4. Results are shown in the PR

### Local CI Simulation

Run these before pushing to catch issues early:

```bash
# Full test suite
pytest tests/ -v --cov=src

# Linting
ruff check .
flake8 src/ tests/ main.py demo_workflow.py

# Both together
pytest tests/ -v --cov=src && ruff check . && flake8 src/ tests/
```

## 📝 Pull Request Guidelines

### Before Submitting a PR

- ✅ All tests pass locally
- ✅ No linting errors
- ✅ Code coverage maintained or improved
- ✅ Documentation updated if needed
- ✅ CHANGELOG updated (if applicable)

### PR Description Template

#### Testing Requirements

### What Changed

Brief description of changes

#### Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Other (describe)

#### Testing

- [ ] All tests pass
- [ ] New tests added
- [ ] Coverage maintained/improved

#### Checklist

- [ ] Code follows PEP 8 style
- [ ] Docstrings added/updated
- [ ] No linting errors
- [ ] README updated if needed

## 🐛 Reporting Bugs

### Bug Report Template

#### Description

Clear description of the bug

### Steps to Reproduce

1. Step 1
2. Step 2
3. ...

### Expected Behavior

What should happen

### Actual Behavior

What actually happens

### Environment

- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.12]
- Package version: [e.g., 1.0.0]

**Additional Context**
Any other relevant information

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check existing issues first
2. Provide clear use case
3. Explain expected behavior
4. Consider implementation approach

## 📚 Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

## ❓ Questions or Help?

- Open a [Discussion](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/discussions)
- File an [Issue](https://github.com/danielnovais-tech/Rural-Connectivity-Mapper-2026/issues)

## 📄 License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers this project.

---

Thank you for contributing to improving rural connectivity in Brazil! 🇧🇷

Together, we're helping to improve rural internet connectivity across Brazil and supporting Starlink's 2026 roadmap.
