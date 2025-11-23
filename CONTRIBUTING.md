# Contributing to M365 Update Manager

Thank you for considering contributing to this project. This document outlines the process and guidelines for contributing.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- uv package manager
- Git

### Setting Up Your Development Environment

1. Clone the repository:
```bash
git clone https://github.com/david-crosby/m365-update-manager.git
cd m365-update-manager
```

2. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies:
```bash
uv sync --all-extras --dev
```

4. Install pre-commit hooks:
```bash
uv run pre-commit install
```

5. Copy the example environment file and configure:
```bash
cp .env.example .env
```

## Development Workflow

### Running Tests

Run the full test suite:
```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --cov=src --cov-report=term-missing
```

### Code Quality

Format code:
```bash
uv run ruff format .
```

Lint code:
```bash
uv run ruff check . --fix
```

Type checking:
```bash
uv run mypy src/
```

### Running the Application Locally

Check for updates:
```bash
uv run python check_updates.py --dry-run --verbose
```

Promote updates:
```bash
uv run python promote.py --dry-run --verbose
```

## Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - A new feature
- `fix:` - A bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, missing semicolons, etc.)
- `refactor:` - Code changes that neither fix bugs nor add features
- `perf:` - Performance improvements
- `test:` - Adding or updating tests
- `chore:` - Changes to build process or auxiliary tools

Examples:
```
feat(manifest): add support for version comparison
fix(azure): handle connection timeout errors
docs(readme): update installation instructions
```

## Pull Request Process

1. Create a new branch for your feature or fix:
```bash
git checkout -b feat/your-feature-name
```

2. Make your changes and commit them using conventional commit messages

3. Ensure all tests pass and code is properly formatted

4. Push your branch and create a pull request

5. Wait for review and address any feedback

## Code Style

- Use type hints for all function signatures
- Keep functions focused and under 50 lines when possible
- Comment to explain "why" not "how"
- Write docstrings for public functions and classes
- Follow PEP 8 style guide (enforced by ruff)
- Use British English in documentation and comments

## Testing Guidelines

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names that explain what is being tested
- Follow the Arrange-Act-Assert pattern
- Use fixtures for common test setup

## Questions or Problems?

Feel free to open an issue on GitHub if you have questions or encounter problems.
