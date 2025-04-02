#!/usr/bin/env python
"""
Script to verify that API routes match the PLANNING.md file.
"""
import os
import sys
import re
from typing import List, Dict, Tuple

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Paths
PLANNING_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PLANNING.md')
API_ROUTES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'api', 'routes')
MAIN_APP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'main.py')

def extract_planned_routes_from_md() -> Dict[str, List[str]]:
    """Extract planned routes from PLANNING.md."""
    planned_routes = {
        'crawl': [],
        'documents': [],
        'knowledge_base': [],
        'other': []  # For routes that don't fit into the other categories
    }
    
    with open(PLANNING_PATH, 'r') as f:
        content = f.read()
    
    # Extract planned routes using regex
    sections = {
        'crawl': r'### Web Crawler Endpoints\n(.*?)(?=###)',
        'documents': r'### Document Processing Endpoints\n(.*?)(?=###)',
        'knowledge_base': r'### Knowledge Base Endpoints\n(.*?)(?=###)'
    }
    
    # First, collect all routes from all sections
    all_routes = []
    for section, pattern in sections.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            section_content = match.group(1)
            route_lines = [
                line.strip() for line in section_content.split('\n')
                if line.strip() and '`' in line
            ]
            
            for line in route_lines:
                # Extract route path from Markdown backticks
                route_match = re.search(r'`([^`]+)`', line)
                if route_match:
                    route = route_match.group(1)
                    
                    # Special case for /api/search which is defined directly in main.py
                    if route == 'GET /api/search':
                        planned_routes['other'].append(route)
                    else:
                        # Add to the appropriate category
                        if section == 'crawl':
                            planned_routes['crawl'].append(route)
                        elif section == 'documents':
                            planned_routes['documents'].append(route)
                        elif section == 'knowledge_base':
                            # Skip adding GET /api/search to knowledge_base as it's already added to 'other'
                            if route != 'GET /api/search':
                                planned_routes['knowledge_base'].append(route)
    
    return planned_routes

def extract_actual_routes_from_code() -> Dict[str, List[Tuple[str, str]]]:
    """Extract actual routes from FastAPI router definitions."""
    actual_routes = {
        'crawl': [],
        'documents': [],
        'knowledge_base': [],
        'other': []  # For routes defined directly in main.py
    }
    
    # Map route files to categories
    file_to_category = {
        'crawl.py': 'crawl',
        'documents.py': 'documents',
        'knowledge_base.py': 'knowledge_base'
    }
    
    # Extract route information from files
    for filename, category in file_to_category.items():
        file_path = os.path.join(API_ROUTES_DIR, filename)
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found")
            continue
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find all router decorators like @router.get("/path")
        route_matches = re.finditer(r'@router\.(get|post|put|delete)\("([^"]+)"', content)
        for match in route_matches:
            method = match.group(1).upper()
            path = match.group(2)
            actual_routes[category].append((method, path))
    
    # Check for routes directly defined in main.py
    with open(MAIN_APP_PATH, 'r') as f:
        main_content = f.read()
    
    # Find all main app routes like @app.get("/api/path")
    main_route_matches = re.finditer(r'@app\.(get|post|put|delete)\("(/api/[^"]+)"', main_content)
    for match in main_route_matches:
        method = match.group(1).upper()
        path = match.group(2)
        
        # Add all main app routes to 'other' category
        actual_routes['other'].append((method, path))
    
    return actual_routes

def extract_prefixes_from_main() -> Dict[str, str]:
    """Extract router prefixes from main.py."""
    prefixes = {
        'other': ''  # No prefix for routes defined directly in main.py
    }
    
    with open(MAIN_APP_PATH, 'r') as f:
        content = f.read()
    
    # Find lines like: app.include_router(router, prefix="/api/path")
    prefix_matches = re.finditer(r'app\.include_router\(([^,]+)\.router, prefix="([^"]+)"', content)
    for match in prefix_matches:
        router_name = match.group(1)
        prefix = match.group(2)
        prefixes[router_name] = prefix
    
    return prefixes

def compare_routes(planned_routes, actual_routes, prefixes):
    """Compare planned routes with actual routes."""
    match_results = []
    missing_results = []
    extra_results = []
    
    # Map category names to router names in main.py
    category_to_router = {
        'crawl': 'crawl',
        'documents': 'documents',
        'knowledge_base': 'knowledge_base',
        'other': 'other'
    }
    
    for category, routes in planned_routes.items():
        router_name = category_to_router.get(category)
        prefix = prefixes.get(router_name, '')
        
        # Check if each planned route exists
        for planned_route in routes:
            # Extract HTTP method and path from planned route
            method_match = re.match(r'(GET|POST|PUT|DELETE)\s+(.+)', planned_route)
            if method_match:
                planned_method = method_match.group(1)
                planned_path = method_match.group(2)
                
                # For all categories except 'other', remove prefix from planned path if it's there
                # For 'other', we expect the full path in both planned and actual
                if category != 'other' and planned_path.startswith(prefix):
                    planned_path = planned_path[len(prefix):]
                
                # Check if this route exists in actual routes
                route_found = False
                
                # Check in the category's actual routes
                for actual_method, actual_path in actual_routes.get(category, []):
                    # Normalize paths to handle parameter differences
                    norm_planned = normalize_path(planned_path)
                    norm_actual = normalize_path(actual_path)
                    
                    # For 'other' routes, we expect full paths, so we need to check differently
                    if category == 'other':
                        if planned_method == actual_method and norm_planned == norm_actual:
                            match_results.append(f"✅ {planned_method} {actual_path}")
                            route_found = True
                            break
                    else:
                        if planned_method == actual_method and match_paths(norm_planned, norm_actual):
                            match_results.append(f"✅ {planned_method} {prefix}{actual_path}")
                            route_found = True
                            break
                
                if not route_found:
                    missing_results.append(f"❌ {planned_method} {planned_path} (MISSING)")
        
        # Check for extra routes
        for actual_method, actual_path in actual_routes.get(category, []):
            route_found = False
            for planned_route in planned_routes.get(category, []):
                method_match = re.match(r'(GET|POST|PUT|DELETE)\s+(.+)', planned_route)
                if method_match:
                    planned_method = method_match.group(1)
                    planned_path = method_match.group(2)
                    
                    # For all categories except 'other', remove prefix from planned path if it's there
                    if category != 'other' and planned_path.startswith(prefix):
                        planned_path = planned_path[len(prefix):]
                    
                    # Normalize paths
                    norm_planned = normalize_path(planned_path)
                    norm_actual = normalize_path(actual_path)
                    
                    # For 'other' routes, we expect full paths
                    if category == 'other':
                        if planned_method == actual_method and norm_planned == norm_actual:
                            route_found = True
                            break
                    else:
                        if planned_method == actual_method and match_paths(norm_planned, norm_actual):
                            route_found = True
                            break
            
            if not route_found:
                # Special case handling for /api/search
                if category == 'other' and actual_path == '/api/search':
                    # Check if it matches any other planned route
                    for other_cat, other_routes in planned_routes.items():
                        for other_route in other_routes:
                            method_match = re.match(r'(GET|POST|PUT|DELETE)\s+(.+)', other_route)
                            if method_match and method_match.group(1) == actual_method and method_match.group(2) == actual_path:
                                route_found = True
                                break
                        if route_found:
                            break
                
                if not route_found:
                    extra_results.append(f"➕ {actual_method} {actual_path if category == 'other' else prefix+actual_path} (EXTRA)")
    
    return match_results, missing_results, extra_results

def normalize_path(path):
    """Normalize path to handle parameter differences."""
    # Replace parameter placeholders like {id} or {job_id} with a generic param
    return re.sub(r'\{[^}]+\}', '{param}', path)

def match_paths(path1, path2):
    """Check if two normalized paths match."""
    # Split paths into segments
    segments1 = path1.strip('/').split('/')
    segments2 = path2.strip('/').split('/')
    
    if len(segments1) != len(segments2):
        return False
    
    for seg1, seg2 in zip(segments1, segments2):
        if seg1 != seg2 and seg1 != '{param}' and seg2 != '{param}':
            return False
    
    return True

def main():
    """Main function."""
    print("Verifying API routes against PLANNING.md...\n")
    
    # Extract information
    planned_routes = extract_planned_routes_from_md()
    actual_routes = extract_actual_routes_from_code()
    prefixes = extract_prefixes_from_main()
    
    # Compare routes
    match_results, missing_results, extra_results = compare_routes(
        planned_routes, actual_routes, prefixes
    )
    
    # Print results
    print("=== MATCHED ROUTES ===")
    for result in match_results:
        print(result)
    
    print("\n=== MISSING ROUTES ===")
    if missing_results:
        for result in missing_results:
            print(result)
    else:
        print("None! All planned routes are implemented.")
    
    print("\n=== EXTRA ROUTES ===")
    if extra_results:
        for result in extra_results:
            print(result)
    else:
        print("None! No extra routes found.")
    
    # Summary
    total_planned = sum(len(routes) for routes in planned_routes.values())
    total_matched = len(match_results)
    coverage = (total_matched / total_planned) * 100 if total_planned > 0 else 0
    
    print(f"\nSummary: {total_matched}/{total_planned} planned routes implemented ({coverage:.1f}%)")

if __name__ == "__main__":
    main() 