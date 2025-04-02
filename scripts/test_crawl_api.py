#!/usr/bin/env python
"""
Test script for KB Builder crawl API endpoints.
This script tests the crawl API endpoints in the running application.
"""

import os
import sys
import argparse
import requests
import json
import time
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Default settings
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def print_environment_info():
    """Print information about the environment and API configuration."""
    print("\n=== Environment Information ===")
    print(f"API Base URL: {API_BASE_URL}")
    
    # Check .env file for crawler configuration
    crawler_api = os.getenv("WEB_CRAWLER_API", "Not specified")
    print(f"Web Crawler API: {crawler_api}")
    
    max_pages_default = os.getenv("MAX_PAGES_DEFAULT", "Not specified")
    max_depth_default = os.getenv("MAX_DEPTH_DEFAULT", "Not specified")
    print(f"Default max pages: {max_pages_default}")
    print(f"Default max depth: {max_depth_default}")
    
    # Check API root endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/api")
        if response.status_code == 200:
            print("\nAPI Status: Available")
            info = response.json()
            print(f"API Version: {info.get('version', 'Unknown')}")
            print(f"API Message: {info.get('message', 'No message')}")
        else:
            print(f"\nAPI Status: Error ({response.status_code})")
    except Exception as e:
        print(f"\nAPI Status: Not available - {str(e)}")
    
    print("=" * 40 + "\n")

def test_start_crawl(url, max_pages=10, max_depth=2):
    """Test the POST /api/crawl endpoint to start a crawl job."""
    # Updated endpoint path based on API verification
    api_url = f"{API_BASE_URL}/api/crawl"
    
    print(f"Starting a crawl job for URL: {url}")
    payload = {
        "url": url,
        "max_pages": max_pages,
        "max_depth": max_depth
    }
    
    try:
        print(f"Request to: {api_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(api_url, json=payload)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Crawl job started successfully:")
            print(json.dumps(result, indent=2))
            return result.get("task_id")
        else:
            print(f"Failed to start crawl job")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error starting crawl job: {str(e)}")
        return None

def test_get_crawl_status(task_id):
    """Test the GET /api/crawl/{task_id} endpoint to check a crawl job status."""
    # Updated endpoint path based on API verification
    api_url = f"{API_BASE_URL}/api/crawl/{task_id}"
    
    print(f"Checking status for crawl job: {task_id}")
    
    try:
        response = requests.get(api_url)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Crawl job status:")
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"Failed to get crawl job status")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error checking crawl job: {str(e)}")
        return None

def test_invalid_url():
    """Test the API with an invalid URL."""
    # Updated endpoint path based on API verification
    api_url = f"{API_BASE_URL}/api/crawl"
    
    print("Testing with invalid URL")
    payload = {
        "url": "not-a-valid-url",
        "max_pages": 5,
        "max_depth": 2
    }
    
    try:
        response = requests.post(api_url, json=payload)
        print(f"Status code: {response.status_code}")
        print(response.text)
        return response.status_code
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_invalid_task_id():
    """Test getting status with an invalid task ID."""
    # Updated endpoint path based on API verification
    api_url = f"{API_BASE_URL}/api/crawl/nonexistent-task-id-12345"
    
    print("Testing with invalid task ID")
    
    try:
        response = requests.get(api_url)
        print(f"Status code: {response.status_code}")
        print(response.text)
        return response.status_code
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Test KB Builder crawl API endpoints")
    parser.add_argument("--url", default="https://www.liorra.io", help="URL to crawl")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to crawl")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum depth to crawl")
    parser.add_argument("--test", choices=["all", "start", "status", "invalid-url", "invalid-id"], 
                        default="all", help="Test to run")
    parser.add_argument("--task-id", help="Task ID for status check")
    
    args = parser.parse_args()
    
    # Print environment information
    print_environment_info()
    
    if args.test == "start" or args.test == "all":
        print("\n===== Testing Start Crawl =====")
        task_id = test_start_crawl(args.url, args.max_pages, args.max_depth)
        
        if task_id and args.test == "all":
            # Wait a moment and check the status
            print("\nWaiting 5 seconds before checking status...")
            time.sleep(5)
            test_get_crawl_status(task_id)
    
    if args.test == "status":
        if not args.task_id:
            print("Error: Must provide --task-id for status test")
        else:
            print("\n===== Testing Get Crawl Status =====")
            test_get_crawl_status(args.task_id)
    
    if args.test == "invalid-url" or args.test == "all":
        print("\n===== Testing Invalid URL =====")
        test_invalid_url()
    
    if args.test == "invalid-id" or args.test == "all":
        print("\n===== Testing Invalid Task ID =====")
        test_invalid_task_id()

if __name__ == "__main__":
    main() 