# Bash commands
- uv run pytest
- uv add
- uvx ruff check
- uvx ruff format

# Tooling
- Always add dependencies using uv

# Code style
- Follow ruff formatting rules

# Workflow
- Format all python code using ruff after each task to ensure conformance
- Create and update tests. Consider failure scenarios. Review missing coverage.
- Run the test suite. Prefer running only applicable tests.
- Update the .gitingore when new tools are added that generate caches and other files and directories that should not be added to version control.

# Version control
- Maintain the .gitignore file. Pay attention when adding new tools or libraries which may require updating it.
- CLAUDE.md should be version controlled
- .claude/settings.local.json must not be committed