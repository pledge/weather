# Bash commands
- uv run pytest
- uvx ruff check
- uvx ruff format

# Tooling
- Always add dependencies using uv

# Code style
- Follow ruff formatting rules


# Workflow
- Format all python code using ruff after each task to ensure conformance
- Run the test suite. Prefer running only applicable tests.
- Update the .gitingore when new tools are added that generate caches and other files and directories that should not be added to version control.