# Using the KB-Builder with Virtual Environment

This document explains how to properly use the KB-Builder with Python virtual environments to ensure isolation and dependency management.

## Using the Run Script (Recommended)

We've created a convenient shell script that handles virtual environment activation automatically:

```bash
# Run the example script
./run_kb_builder.sh example

# Start the FastAPI application
./run_kb_builder.sh api

# Crawl a custom URL (like liorra.io)
./run_kb_builder.sh custom https://www.liorra.io
```

This script will:
1. Check if the virtual environment exists, and create it if needed
2. Activate the virtual environment
3. Run the requested operation
4. Deactivate the virtual environment when done

## Running Tests with Virtual Environment

We also provide a dedicated script for running tests in the virtual environment:

```bash
# Verify API routes match PLANNING.md
./run_tests.sh verify-api

# Test the crawl API with liorra.io
./run_tests.sh test-crawl --url=https://www.liorra.io --max-pages=10 --max-depth=2

# Test individual components
./run_tests.sh test-component component=crawler
./run_tests.sh test-component component=text
./run_tests.sh test-component component=vector
./run_tests.sh test-component component=all
```

The test script will:
1. Set up and activate the virtual environment
2. Start the API server if needed (for API tests)
3. Run the requested tests with appropriate parameters
4. Deactivate the virtual environment when finished

## Manual Virtual Environment Usage

If you prefer to manage the virtual environment manually:

```bash
# Create virtual environment (if not already created)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate   # On Linux/macOS
# venv\Scripts\activate    # On Windows

# Install dependencies (first time only)
pip install -r requirements.txt

# Now run Python commands
python examples/kb_builder_example.py
# OR
python -m uvicorn app.main:app --reload

# When finished, deactivate the environment
deactivate
```

## Running with `liorra.io` Example

To create a knowledge base for liorra.io:

```bash
# Using the kb_builder_example script
./run_kb_builder.sh custom https://www.liorra.io

# Using the test script to test the crawl API with liorra.io
./run_tests.sh test-crawl --url=https://www.liorra.io
```

## Troubleshooting

If you encounter a "command not found: python" error, make sure you:

1. Have activated the virtual environment first
2. Use `python3` instead of `python` if your system requires it
3. Use the run script which handles these differences automatically

The virtual environment ensures all dependencies are properly isolated and managed for the KB-Builder project. 