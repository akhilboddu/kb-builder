# Contributing to Knowledge Base Builder

Thank you for considering contributing to Knowledge Base Builder! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful, inclusive, and constructive in your interactions with others.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:
- Check the issues list to see if the bug has already been reported
- Make sure you're using the latest version of the software
- Determine if the issue is in the code itself or in a dependency

When submitting a bug report, please include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Screenshots or logs if applicable
- Your environment (OS, Python version, dependencies)

### Suggesting Enhancements

When suggesting enhancements:
- Provide a clear description of the feature
- Explain why this enhancement would be useful
- Consider how it might affect other aspects of the project
- If possible, outline how the enhancement might be implemented

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write or update tests as necessary
5. Ensure your code passes all tests
6. Submit a pull request to the `main` branch

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/kb-builder.git
cd kb-builder
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run tests:
```bash
pytest
```

## Coding Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Write docstrings for all functions, classes, and modules
- Include type hints where appropriate
- Keep functions and methods small and focused
- Write tests for new functionality
- Update documentation as needed

## Commit Guidelines

- Use clear, descriptive commit messages
- Include the issue number in the commit message if applicable
- Make each commit a logical unit
- Keep commits focused on a single task

## Documentation

- Update the README.md file with new features or changes
- Add or update docstrings for any code you modify
- If adding new functionality, consider adding an example
- Update API documentation if you change any public interfaces

## Project Structure

Please respect the project's structure:
- `app/`: Main application code
  - `api/`: API routes
  - `core/`: Core functionality
  - `db/`: Database integration
  - `models/`: Data models
  - `services/`: Business logic
  - `utils/`: Utility functions
- `tests/`: Test suite
- `examples/`: Example scripts
- `docs/`: Documentation

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License. 