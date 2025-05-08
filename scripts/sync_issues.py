#!/usr/bin/env python3
"""
GitHub Issues Sync Tool

This script synchronizes between a local YAML file and GitHub issues.
It can perform bidirectional sync:
- Pull: Update local YAML with GitHub issues
- Push: Create/update GitHub issues from local YAML

Usage:
    python sync_issues.py --mode=pull  # Update local YAML from GitHub
    python sync_issues.py --mode=push  # Update GitHub from local YAML
    python sync_issues.py --mode=sync  # Bidirectional sync (default)

Requirements:
    pip install pyyaml requests
"""

import argparse
import os
import re
import sys
import yaml
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Configuration
YAML_PATH = "docs/issues.yaml"
# Support GitHub Actions default env (e.g. GITHUB_REPOSITORY=owner/repo)
if "GITHUB_REPOSITORY" in os.environ:
    REPO_OWNER, REPO_NAME = os.environ["GITHUB_REPOSITORY"].split("/")
else:
    REPO_OWNER = os.environ.get("GITHUB_OWNER", "")
    REPO_NAME = os.environ.get("GITHUB_REPO", "BRAWL-Burmese-movies-cRAWLer-")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # Your GitHub personal access token
ISSUE_LABEL = "crawler-issue"  # Label to identify issues managed by this script

# GitHub API endpoints
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
ISSUES_ENDPOINT = f"{API_BASE}/issues"

# Issue mapping between YAML and GitHub
SEVERITY_LABELS = {
    "high": "priority:high",
    "medium": "priority:medium",
    "low": "priority:low"
}

CATEGORY_LABELS = {
    "Architecture": "type:architecture",
    "Performance": "type:performance",
    "DataQuality": "type:data-quality",
    "Ops": "type:ops",
    "Testing": "type:testing",
    "Security": "type:security",
    "Dependency": "type:dependency",
    "Storage": "type:storage",
    "i18n": "type:i18n"
}

STATUS_MAPPING = {
    "todo": "open",
    "in_progress": "open",
    "done": "closed"
}

# Reverse mapping for GitHub to YAML
GITHUB_STATUS_TO_YAML = {
    "open": "todo",  # Default for open issues
    "closed": "done"
}

def setup_api_headers() -> Dict[str, str]:
    """Set up headers for GitHub API requests."""
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN environment variable not set.")
        print("You may encounter rate limiting or authentication issues.")
        return {"Accept": "application/vnd.github.v3+json"}
    
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }

def load_yaml_issues() -> Tuple[str, List[Dict[str, Any]]]:
    """Load issues from YAML file, whether it's a dict or a top-level list."""
    try:
        with open(YAML_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
            header = ""  # Skip extracting custom headers now
            data = yaml.safe_load(content)

            if isinstance(data, list):
                issues = data
            elif isinstance(data, dict):
                issues = data.get("Further Improvements", [])
            else:
                raise ValueError("Unrecognized YAML structure: expected list or dict")

            return header, issues
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return "", []

def save_yaml_issues(header: str, issues: List[Dict[str, Any]]) -> bool:
    """Save issues to YAML file."""
    try:
        # Create the full YAML content
        yaml_content = header
        
        # Convert issues to YAML format with proper indentation
        issues_yaml = yaml.dump({"Further Improvements": issues}, 
                               default_flow_style=False,
                               sort_keys=False,
                               indent=2,
                               width=120,
                               allow_unicode=True)
        
        # Remove the "Further Improvements:" line that yaml.dump adds
        issues_yaml = issues_yaml.replace("Further Improvements:", "").strip()
        
        # Add proper indentation to the YAML content
        yaml_content += issues_yaml
        
        # Write to file
        with open(YAML_PATH, 'w', encoding='utf-8') as file:
            file.write(yaml_content)
        return True
    except Exception as e:
        print(f"Error saving YAML file: {e}")
        return False

def fetch_github_issues() -> List[Dict[str, Any]]:
    """Fetch issues from GitHub."""
    headers = setup_api_headers()
    all_issues = []
    page = 1
    
    while True:
        params = {
            "state": "all",  # Get both open and closed issues
            "labels": ISSUE_LABEL,
            "per_page": 100,
            "page": page
        }
        
        response = requests.get(ISSUES_ENDPOINT, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching GitHub issues: {response.status_code}")
            print(response.text)
            break
        
        issues = response.json()
        if not issues:
            break
            
        all_issues.extend(issues)
        page += 1
        
        # Check if we've reached the last page
        if len(issues) < 100:
            break
    
    return all_issues

def create_github_issue(issue: Dict[str, Any], dry_run=False) -> Optional[Dict[str, Any]]:
    """Create a new issue on GitHub."""
    headers = setup_api_headers()
    
    # Prepare labels
    labels = [ISSUE_LABEL]
    if issue.get("severity") in SEVERITY_LABELS:
        labels.append(SEVERITY_LABELS[issue["severity"]])
    if issue.get("category") in CATEGORY_LABELS:
        labels.append(CATEGORY_LABELS[issue["category"]])
    
    # Create issue title
    title = f"[{issue['component']}] {issue['impact']}"
    
    # Create issue body
    body = f"""
**Component:** {issue['component']}
**Category:** {issue['category']}
**Severity:** {issue['severity']}

### Impact
{issue['impact']}

### Suggestion
{issue['suggestion']}

---
*This issue is managed by the issue sync tool. Please do not modify this section.*
```yaml
component: {issue['component']}
category: {issue['category']}
severity: {issue['severity']}
impact: {issue['impact']}
suggestion: {issue['suggestion']}
status: {issue['status']}
```
"""

    # Create the issue
    payload = {
        "title": title,
        "body": body,
        "labels": labels
    }

    if dry_run:
        print(f"[DRY-RUN] Would create GitHub issue: {title}")
        return None
    response = requests.post(ISSUES_ENDPOINT, headers=headers, json=payload)
    
    if response.status_code not in (201, 200):
        print(f"Error creating GitHub issue: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def update_github_issue(issue_number: int, issue: Dict[str, Any], github_issue: Dict[str, Any], dry_run=False) -> bool:
    """Update an existing GitHub issue."""
    headers = setup_api_headers()
    
    # Prepare labels
    labels = [ISSUE_LABEL]
    if issue.get("severity") in SEVERITY_LABELS:
        labels.append(SEVERITY_LABELS[issue["severity"]])
    if issue.get("category") in CATEGORY_LABELS:
        labels.append(CATEGORY_LABELS[issue["category"]])
    
    # Create issue title
    title = f"[{issue['component']}] {issue['impact']}"
    
    # Create issue body
    body = f"""
**Component:** {issue['component']}
**Category:** {issue['category']}
**Severity:** {issue['severity']}

### Impact
{issue['impact']}

### Suggestion
{issue['suggestion']}

---
*This issue is managed by the issue sync tool. Please do not modify this section.*
```yaml
component: {issue['component']}
category: {issue['category']}
severity: {issue['severity']}
impact: {issue['impact']}
suggestion: {issue['suggestion']}
status: {issue['status']}
```
"""
    
    # Update the issue
    payload = {
        "title": title,
        "body": body,
        "labels": labels,
        "state": STATUS_MAPPING.get(issue["status"], "open")
    }

    if dry_run:
        print(f"[DRY-RUN] Would update GitHub issue #{issue_number}: {title}")
        return True
    
    response = requests.patch(f"{ISSUES_ENDPOINT}/{issue_number}", headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error updating GitHub issue #{issue_number}: {response.status_code}")
        print(response.text)
        return False
    
    return True

def extract_yaml_from_body(body: str) -> Optional[Dict[str, Any]]:
    """Extract YAML data from GitHub issue body."""
    yaml_match = re.search(r'```yaml\n(.*?)\n```', body, re.DOTALL)
    if not yaml_match:
        return None
    
    yaml_text = yaml_match.group(1)
    try:
        return yaml.safe_load(yaml_text)
    except Exception as e:
        print(f"Error parsing YAML from issue body: {e}")
        return None

def push_to_github(yaml_issues: List[Dict[str, Any]], github_issues: List[Dict[str, Any]], dry_run = False) -> None:
    """Push local YAML issues to GitHub."""
    print("Pushing local issues to GitHub...")

    # Create a mapping of existing GitHub issues by component
    github_issues_map = {}
    for issue in github_issues:
        yaml_data = extract_yaml_from_body(issue["body"])
        if yaml_data and "component" in yaml_data:
            github_issues_map[yaml_data["component"]] = {
                "number": issue["number"],
                "data": issue
            }
    
    created = 0
    updated = 0
    skipped = 0
    
    # Process each YAML issue
    for issue in yaml_issues:
        component = issue.get("component")
        if not component:
            print(f"Skipping issue without component: {issue}")
            skipped += 1
            continue
        
        # Check if this issue already exists on GitHub
        if component in github_issues_map:
            # Update existing issue
            github_issue = github_issues_map[component]
            if update_github_issue(github_issue["number"], issue, github_issue["data"]):
                updated += 1
                print(f"Updated GitHub issue #{github_issue['number']}: {component}")
            else:
                skipped += 1
        else:
            # Create new issue
            new_issue = create_github_issue(issue)
            if new_issue:
                created += 1
                print(f"Created GitHub issue #{new_issue['number']}: {component}")
                # Add issue number to the local issue for future reference
                issue["github_issue"] = new_issue["number"]
            else:
                skipped += 1
    
    print(f"GitHub push complete: {created} created, {updated} updated, {skipped} skipped")

def pull_from_github(yaml_issues: List[Dict[str, Any]], github_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pull GitHub issues to local YAML."""
    print("Pulling GitHub issues to local YAML...")
    
    # Create a mapping of existing YAML issues by component
    yaml_issues_map = {issue["component"]: issue for issue in yaml_issues if "component" in issue}
    
    updated = 0
    added = 0
    
    # Process each GitHub issue
    for github_issue in github_issues:
        yaml_data = extract_yaml_from_body(github_issue["body"])
        if not yaml_data:
            print(f"[WARN] GitHub issue #{github_issue['number']} has no embedded YAML block")
            continue

        if "component" not in yaml_data:
            print(f"[WARN] GitHub issue #{github_issue['number']} YAML missing 'component' field")
            continue

        
        component = yaml_data["component"]
        
        # Update status based on GitHub issue state
        yaml_data["status"] = GITHUB_STATUS_TO_YAML.get(github_issue["state"], "todo")
        
        # If issue is marked as "in_progress" in YAML, preserve that status
        if component in yaml_issues_map and yaml_issues_map[component]["status"] == "in_progress":
            yaml_data["status"] = "in_progress"
        
        # Check if this issue already exists in YAML
        if component in yaml_issues_map:
            # Update existing issue
            yaml_issues_map[component].update(yaml_data)
            updated += 1
            print(f"Updated local issue: {component}")
        else:
            # Add new issue
            yaml_issues.append(yaml_data)
            yaml_issues_map[component] = yaml_data
            added += 1
            print(f"Added local issue: {component}")
    
    if added == 0 and updated == 0:
        print("✅ No new issues added. Everything is in sync.")
    else:
        print(f"✅ Pull summary: {added} added, {updated} updated")
    return yaml_issues

def main():
    parser = argparse.ArgumentParser(description="Sync between local YAML issues and GitHub issues")
    parser.add_argument(
        "--mode",
        choices=["pull", "push", "sync"],
        default="sync",
        help="Sync mode: pull (GitHub → YAML), push (YAML → GitHub), or sync (bidirectional)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without making changes"
    )

    args = parser.parse_args()
    
    # Check if GitHub token is set
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN environment variable not set.")
        print("Limited functionality will be available.")
    
    # Check if repo owner is set
    if not REPO_OWNER:
        print("Error: GITHUB_OWNER environment variable not set.")
        print("Please set your GitHub username or organization name.")
        sys.exit(1)
    
    # Load local YAML issues
    header, yaml_issues = load_yaml_issues()
    if not yaml_issues:
        print("No issues found in YAML file or file could not be loaded.")
        if args.mode == "pull":
            print("Continuing with pull operation...")
        else:
            sys.exit(1)
    
    # Fetch GitHub issues
    github_issues = fetch_github_issues()
    print(f"Fetched {len(github_issues)} issues from GitHub")
    
    # Perform sync based on mode
    if args.mode in ("push", "sync"):
        push_to_github(yaml_issues, github_issues, dry_run=args.dry_run)
    
    if args.mode in ("pull", "sync"):
        yaml_issues = pull_from_github(yaml_issues, github_issues)
        if save_yaml_issues(header, yaml_issues):
            print(f"Updated local YAML file: {YAML_PATH}")
        else:
            print("Failed to update local YAML file")
    
    print("Sync completed successfully!")

if __name__ == "__main__":
    main()