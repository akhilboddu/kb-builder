#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Detect the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    # Activate the virtual environment
    source venv/bin/activate
fi

# Function to show usage
show_usage() {
    echo "Usage: ./run_tests.sh [test_type] [options]"
    echo ""
    echo "Test Types:"
    echo "  verify-api     - Verify API routes against PLANNING.md"
    echo "  test-crawl     - Test the crawl API (default URL: liorra.io)"
    echo "  test-component - Test components (text, crawler, document, vector, all)"
    echo "  search-kb      - Search the knowledge base directly"
    echo "  check-kb       - Verify liorra.io content in the knowledge base"
    echo ""
    echo "Options:"
    echo "  For verify-api: No options needed"
    echo "  For test-crawl: --url=URL --max-pages=N --max-depth=N --test=[all|start|status|invalid-url|invalid-id]"
    echo "  For test-component: component=[text|crawler|document|vector|all]"
    echo "  For search-kb: query=\"your search query\" --limit=N"
    echo "  For check-kb: No options needed"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh verify-api"
    echo "  ./run_tests.sh test-crawl --url=https://www.liorra.io --max-pages=10 --max-depth=2"
    echo "  ./run_tests.sh test-component component=text"
    echo "  ./run_tests.sh search-kb query=\"What is liorra about\" --limit=3"
    echo "  ./run_tests.sh check-kb"
}

# Default values
URL="https://www.liorra.io"
MAX_PAGES=10
MAX_DEPTH=2
TEST_TYPE="all"
COMPONENT="all"
SEARCH_QUERY=""
SEARCH_LIMIT=5

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

TEST_SCRIPT="$1"
shift

# Parse remaining options
for arg in "$@"; do
    case $arg in
        --url=*)
        URL="${arg#*=}"
        ;;
        --max-pages=*)
        MAX_PAGES="${arg#*=}"
        ;;
        --max-depth=*)
        MAX_DEPTH="${arg#*=}"
        ;;
        --test=*)
        TEST_TYPE="${arg#*=}"
        ;;
        component=*)
        COMPONENT="${arg#*=}"
        ;;
        query=*)
        SEARCH_QUERY="${arg#*=}"
        ;;
        --limit=*)
        SEARCH_LIMIT="${arg#*=}"
        ;;
        *)
        echo "Unknown option: $arg"
        show_usage
        exit 1
        ;;
    esac
done

# Make sure the API server is running
ensure_api_running() {
    # Basic check to see if API is responding
    echo "Checking if API server is running..."
    if curl -s -f "http://localhost:8000/api" > /dev/null; then
        echo "API server is running."
    else
        echo "API server is not running. Starting it in the background..."
        python -m uvicorn app.main:app --reload --port 8000 &
        API_PID=$!
        echo "API server started with PID $API_PID"
        # Give it a moment to start up
        sleep 3
    fi
}

# Run the tests based on TEST_SCRIPT
case $TEST_SCRIPT in
    verify-api)
        echo "Running API routes verification..."
        python scripts/verify_api_routes.py
        ;;
    test-crawl)
        ensure_api_running
        echo "Running crawl API tests with URL $URL..."
        python scripts/test_crawl_api.py --url="$URL" --max-pages="$MAX_PAGES" --max-depth="$MAX_DEPTH" --test="$TEST_TYPE"
        ;;
    test-component)
        echo "Running component tests for $COMPONENT..."
        python scripts/test_components.py "$COMPONENT"
        ;;
    search-kb)
        echo "Searching knowledge base for: $SEARCH_QUERY"
        if [ -z "$SEARCH_QUERY" ]; then
            echo "Error: You must provide a search query using query=\"your search query\""
            exit 1
        fi
        python scripts/search_kb.py "$SEARCH_QUERY" --limit="$SEARCH_LIMIT"
        ;;
    check-kb)
        echo "Checking knowledge base for liorra.io content..."
        python scripts/simple_kb_verify.py
        ;;
    *)
        echo "Unknown test script: $TEST_SCRIPT"
        show_usage
        exit 1
        ;;
esac

# Deactivate the virtual environment when done
deactivate 