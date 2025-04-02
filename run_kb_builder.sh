#!/bin/bash

# KB-Builder run script
# This script handles virtual environment activation and runs the requested operation

# Function to ensure virtual environment is activated
ensure_venv() {
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
        
        # Install dependencies if needed
        pip install -r requirements.txt
    fi
}

# Function to run the API server
run_api() {
    echo "Starting FastAPI server..."
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to run the example script
run_example() {
    echo "Running example script..."
    python3 examples/kb_builder_example.py
}

# Function to run with custom URL
run_custom() {
    if [ -z "$1" ]; then
        echo "Error: URL is required for custom mode"
        echo "Usage: ./run_kb_builder.sh custom <url>"
        exit 1
    fi
    
    echo "Running KB Builder with custom URL: $1"
    python3 scripts/test_crawl_api.py --url="$1"
}

# Main script logic
MODE=$1

# Ensure virtual environment is activated
ensure_venv

# Run the requested operation
case $MODE in
    "api")
        run_api
        ;;
    "example")
        run_example
        ;;
    "custom")
        run_custom $2
        ;;
    *)
        echo "Usage: ./run_kb_builder.sh [api|example|custom <url>]"
        echo "  api     - Start the FastAPI application"
        echo "  example - Run the example script"
        echo "  custom  - Crawl a custom URL (e.g., ./run_kb_builder.sh custom https://www.liorra.io)"
        exit 1
        ;;
esac

# Deactivate the virtual environment if we activated it
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi 