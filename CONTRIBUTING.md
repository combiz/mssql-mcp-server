# Contributing to MSSQL MCP Server

We love your input! We want to make contributing to MSSQL MCP Server as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issue tracker](https://github.com/combiz/mssql-mcp-server/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/combiz/mssql-mcp-server/issues/new).

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/combiz/mssql-mcp-server.git
   cd mssql-mcp-server
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests:
   ```bash
   pytest
   ```

5. Check code style:
   ```bash
   black mssql_mcp_server
   flake8 mssql_mcp_server
   mypy mssql_mcp_server
   ```

## Code Style

- We use [Black](https://github.com/psf/black) for Python code formatting
- We use [flake8](https://flake8.pycqa.org/) for linting
- We use [mypy](http://mypy-lang.org/) for type checking
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add type hints where possible
- Document complex logic with comments

## Testing

- Write tests for new functionality
- Ensure all tests pass before submitting PR
- Aim for high test coverage
- Test edge cases and error conditions

## License

By contributing, you agree that your contributions will be licensed under its MIT License.