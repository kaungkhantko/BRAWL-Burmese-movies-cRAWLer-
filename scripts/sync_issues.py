#!/usr/bin/env python3
"""
GitHub Issues Sync Tool (GraphQL Project Sync Enabled)

Used by .github/workflows/sync-issues.yaml
Do not delete unless CI is updated accordingly

Syncs issues between a local YAML file and GitHub Projects.
Supports pulling project fields (Priority, Sprint, Size) from GitHub.

Requirements:
    pip install pyyaml requests python-dotenv gql rich
"""
from rich.console import Console
from rich.table import Table
import argparse
import os
import re
import sys
import yaml
import requests
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

load_dotenv()

# Configuration
YAML_PATH = "docs/issues.yaml"
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")
GITHUB_PROJECT_ID = os.environ.get("PROJECT_ID", "")
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
ISSUES_ENDPOINT = f"{API_BASE}/issues"

# Field mappings for GitHub Project
PROJECT_FIELD_MAP = {
    "priority": {
        "field_id": "PVTSSF_lAHOAmdo2s4A3zp6zgs4a8w",
        "options": {
            "P0": "79628723",
            "P1": "0a877460",
            "P2": "da944a9c"
        }
    },
    "size": {
        "field_id": "PVTSSF_lAHOAmdo2s4A3zp6zgs4a80",
        "options": {
            "XS": "911790be",
            "S": "b277fb01",
            "M": "86db8eb3",
            "L": "853c8207",
            "XL": "2d0801e2"
        }
    },
    "sprint": {
        "field_id": "PVTIF_lAHOAmdo2s4A3zp6zgs4a88",
        "options": {
            "Sprint 1": "381c7c80",
            "Sprint 2": "54cf5c95",
            "Sprint 3": "d2c335bc",
            "Sprint 4": "b6a8f1bb",
            "Sprint 5": "955c1297",
            "Sprint 6": "d6cfaec5",
            "Sprint 7": "ef7f5391",
            "Sprint 8": "9cbbc868",
            "Sprint 9": "e47be7ec",
            "Sprint 10": "dff6644e"
        }
    }
}

# GraphQL client setup
transport = RequestsHTTPTransport(
    url="https://api.github.com/graphql",
    headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
)
gql_client = Client(transport=transport, fetch_schema_from_transport=True)


def setup_api_headers() -> Dict[str, str]:
    """Set up headers for GitHub API requests."""
    if not GITHUB_TOKEN:
        print("Missing GITHUB_TOKEN")
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }


def load_yaml_issues() -> List[Dict[str, Any]]:
    """Load issues from the YAML file."""
    try:
        with open(YAML_PATH, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading YAML: {e}")
        return []


def save_yaml_issues(issues: List[Dict[str, Any]]) -> bool:
    """Save issues to the YAML file."""
    try:
        with open(YAML_PATH, 'w', encoding='utf-8') as file:
            yaml.dump(issues, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error saving YAML: {e}")
        return False


def fetch_github_issues() -> List[Dict[str, Any]]:
    """Fetch all issues from GitHub using the REST API."""
    headers = setup_api_headers()
    all_issues, page = [], 1
    skipped_prs = 0
    
    while True:
        params = {"state": "all", "per_page": 100, "page": page}
        r = requests.get(ISSUES_ENDPOINT, headers=headers, params=params)
        
        if r.status_code != 200:
            print(f"GitHub API error: {r.status_code}")
            break
            
        batch = r.json()
        if not batch:
            break
        
        # Filter out pull requests at fetch time
        for item in batch:
            if "pull_request" in item:
                skipped_prs += 1
                continue
            all_issues.append(item)
        
        if len(batch) < 100:
            break
            
        page += 1
    
    if skipped_prs > 0:
        print(f"Skipped {skipped_prs} pull requests during fetch")
        
    return all_issues


def extract_yaml_from_body(body: Optional[str]) -> Optional[Dict[str, Any]]:
    """Extract YAML block from issue body."""
    if not isinstance(body, str):
        return None
        
    match = re.search(r'```yaml\n(.*?)\n```', body, re.DOTALL)
    if not match:
        return None
        
    try:
        return yaml.safe_load(match.group(1))
    except Exception as e:
        print(f"YAML parse error: {e}")
        return None


def update_project_field(issue_node_id: str, field: str, value: str):
    """Update a field value for an issue in the GitHub Project."""
    field_data = PROJECT_FIELD_MAP.get(field.lower())
    if not field_data:
        print(f"[WARN] Field '{field}' not found in PROJECT_FIELD_MAP")
        return
    
    option_id = field_data["options"].get(value)
    if not option_id:
        print(f"[WARN] Value '{value}' not found in options for field '{field}'")
        return
    
    # Different mutation for iteration fields (Sprint)
    if field.lower() == "sprint":
        mutation = gql("""
        mutation($input: UpdateProjectV2ItemFieldValueInput!) {
          updateProjectV2ItemFieldValue(input: $input) {
            projectV2Item { id }
          }
        }
        """)
        input = {
            "projectId": GITHUB_PROJECT_ID,
            "itemId": issue_node_id,
            "fieldId": field_data["field_id"],
            "value": {"iterationId": option_id}
        }
    else:
        # For single select fields (Priority, Size)
        mutation = gql("""
        mutation($input: UpdateProjectV2ItemFieldValueInput!) {
          updateProjectV2ItemFieldValue(input: $input) {
            projectV2Item { id }
          }
        }
        """)
        input = {
            "projectId": GITHUB_PROJECT_ID,
            "itemId": issue_node_id,
            "fieldId": field_data["field_id"],
            "value": {"singleSelectOptionId": option_id}
        }
    
    try:
        gql_client.execute(mutation, variable_values={"input": input})
    except Exception as e:
        print(f"[ERROR] Failed to update {field}={value} for item {issue_node_id}: {e}")


def create_github_issue(issue: Dict[str, Any], dry_run=False) -> Optional[Dict[str, Any]]:
    """Create a new issue on GitHub."""
    headers = setup_api_headers()
    payload = {
        "title": issue["title"],
        "body": issue["description"]
    }
    
    if dry_run:
        print(f"[DRY-RUN] Would create: {issue['title']}")
        return None
        
    r = requests.post(ISSUES_ENDPOINT, headers=headers, json=payload)
    return r.json() if r.status_code in (200, 201) else None


def update_github_issue(number: int, issue: Dict[str, Any], gh_issue: Dict[str, Any], dry_run=False) -> bool:
    """Update an existing issue on GitHub."""
    headers = setup_api_headers()
    
    # Set state based on issue status (default to "open" if not specified)
    state = issue.get("status", "open")
    
    payload = {
        "title": issue["title"],
        "body": issue["description"],
        "state": state
    }
    
    if dry_run:
        status_msg = f" (Status: {state})" if state != gh_issue.get("state") else ""
        print(f"[DRY-RUN] Would update #{number}: {issue['title']}{status_msg}")
        return True
        
    r = requests.patch(f"{ISSUES_ENDPOINT}/{number}", headers=headers, json=payload)
    return r.status_code == 200


def add_issue_to_project(issue_node_id: str):
    """Add an issue to the GitHub Project."""
    mutation = gql("""
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {
        projectId: $projectId
        contentId: $contentId
      }) {
        item { id }
      }
    }
    """)
    
    try:
        gql_client.execute(mutation, variable_values={
            "projectId": GITHUB_PROJECT_ID,
            "contentId": issue_node_id
        })
    except Exception as e:
        print(f"[ERROR] Failed to add issue to project: {e}")


def get_project_item_id(issue_node_id: str) -> Optional[str]:
    """Get the project item ID for an issue."""
    query = gql("""
    query($issueId: ID!) {
      node(id: $issueId) {
        ... on Issue {
          projectItems(first: 10) {
            nodes {
              id
              project {
                id
              }
            }
          }
        }
      }
    }
    """)
    
    try:
        result = gql_client.execute(query, variable_values={"issueId": issue_node_id})
        for item in result["node"]["projectItems"]["nodes"]:
            if item["project"]["id"] == GITHUB_PROJECT_ID:
                return item["id"]
    except Exception as e:
        print(f"[ERROR] Failed to get project item ID: {e}")
        
    return None


def print_issue_table(issues: List[Dict[str, Any]]):
    """Print a formatted table of issues."""
    console = Console()
    table = Table(show_lines=True)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Title", style="bold", no_wrap=True)
    table.add_column("Status", style="bright_green")
    table.add_column("Priority", style="magenta")
    table.add_column("Sprint", style="green")
    table.add_column("Size", style="yellow")

    for issue in issues:
        # Set status style based on open/closed
        status = issue.get("status", "open")
        status_style = "bright_green" if status == "open" else "red"
        
        table.add_row(
            str(issue.get("github_issue", "?")),
            issue.get("title", "[no title]"),
            f"[{status_style}]{status}[/{status_style}]",
            issue.get("priority", "-"),
            issue.get("sprint", "-"),
            issue.get("size", "-")
        )

    console.print(table)


def fetch_project_items() -> List[Dict[str, Any]]:
    """Fetch all items from the GitHub Project."""
    if not GITHUB_PROJECT_ID:
        print("[WARN] GITHUB_PROJECT_ID not set, skipping project field retrieval")
        return []
    
    query = gql("""
    query($projectId: ID!, $first: Int!, $after: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: $first, after: $after) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              content {
                ... on Issue {
                  number
                  title
                  body
                  id
                  state
                  __typename
                }
                ... on DraftIssue {
                  title
                  body
                  id
                  __typename
                }
              }
              fieldValues(first: 20) {
                nodes {
                  __typename
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    field {
                      ... on ProjectV2Field {
                        name
                      }
                    }
                    name
                  }
                  ... on ProjectV2ItemFieldIterationValue {
                    field {
                      ... on ProjectV2IterationField {
                        name
                      }
                    }
                    title
                  }
                }
              }
            }
          }
        }
      }
    }
    """)

    items = []
    after = None
    
    try:
        while True:
            variables = {
                "projectId": GITHUB_PROJECT_ID,
                "first": 50,
                "after": after
            }
            
            result = gql_client.execute(query, variable_values=variables)
            page = result["node"]["items"]
            items.extend(page["nodes"])
            
            if not page["pageInfo"]["hasNextPage"]:
                break
                
            after = page["pageInfo"]["endCursor"]
    except Exception as e:
        print(f"[ERROR] Failed to fetch project items: {e}")
        
    return items


def parse_project_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse project items to extract issue data and field values."""
    parsed = []
    
    for item in items:
        content = item.get("content")
        if not content:
            continue
            
        # Handle both Issue and DraftIssue types
        content_type = content.get("__typename")
        if content_type == "Issue":
            number = content["number"]
            issue = {
                "github_issue": number,
                "title": content.get("title", ""),
                "description": content.get("body") or "[no description]",
                "status": content.get("state", "open")  # Add status field (open/closed)
            }
        elif content_type == "DraftIssue":
            # Skip draft issues as they don't have a number yet
            continue
        else:
            # Skip other content types
            continue
            
        # Process field values (priority, sprint, size)
        for fv in item.get("fieldValues", {}).get("nodes", []):
            # Get the field type
            field_type = fv.get("__typename")
            
            # Handle SingleSelectValue fields (Priority, Size)
            if field_type == "ProjectV2ItemFieldSingleSelectValue":
                value = fv.get("name")
                if not value:
                    continue
                    
                # Try to determine which field this is based on the value
                if value in ["P0", "P1", "P2"]:
                    issue["priority"] = value
                elif value in ["XS", "S", "M", "L", "XL"]:
                    issue["size"] = value
                    
            # Handle IterationValue fields (Sprint)
            elif field_type == "ProjectV2ItemFieldIterationValue":
                field_obj = fv.get("field", {})
                field_name = field_obj.get("name", "").lower() if field_obj else ""
                
                if field_name == "sprint":
                    value = fv.get("title")
                    if value:
                        issue["sprint"] = value
                
        parsed.append(issue)
        
    return parsed


def pull_from_github(yaml_issues: List[Dict[str, Any]], gh_issues: List[Dict[str, Any]], dry_run=False) -> List[Dict[str, Any]]:
    """Pull issues from GitHub to local YAML."""
    print("Pulling GitHub issues to local YAML...")

    # Fetch project items with field values
    project_items = fetch_project_items()
    project_issues = parse_project_items(project_items)
    
    # Create a map of GitHub issue number to project fields
    project_fields_map = {str(issue["github_issue"]): issue for issue in project_issues}
    
    # Create a map of existing YAML issues
    yaml_issues_map = {str(i.get("github_issue")): i for i in yaml_issues if "github_issue" in i}
    updated_issues = yaml_issues.copy()
    added = 0
    updated = 0
    status_changed = 0

    # Process all GitHub issues (pull requests already filtered out in fetch_github_issues)
    for gh_issue in gh_issues:
        gh_id = str(gh_issue["number"])
        
        # Get project fields for this issue
        project_fields = project_fields_map.get(gh_id, {})
        
        # Extract YAML from issue body
        yaml_data = extract_yaml_from_body(gh_issue.get("body", ""))
        
        # Create or update issue
        if gh_id in yaml_issues_map:
            # Update existing issue
            yaml_issue = yaml_issues_map[gh_id]
            
            # Preserve fields that exist in YAML but not in GitHub
            preserved_fields = {}
            for field, value in yaml_issue.items():
                if field not in ("title", "description", "github_issue", "status"):
                    preserved_fields[field] = value
            
            # Update with GitHub data
            yaml_issue["title"] = gh_issue.get("title", f"Issue #{gh_id}")
            yaml_issue["description"] = gh_issue.get("body", "") or "[no description]"
            
            # Update issue status (open/closed)
            old_status = yaml_issue.get("status", "open")
            new_status = gh_issue["state"]
            if old_status != new_status:
                yaml_issue["status"] = new_status
                status_changed += 1
            
            # Update with project fields
            for field in ("priority", "sprint", "size"):
                if field in project_fields:
                    yaml_issue[field] = project_fields[field]
            
            # Update with YAML data from issue body
            if isinstance(yaml_data, dict):
                for field, value in yaml_data.items():
                    yaml_issue[field] = value
            
            # Restore preserved fields that weren't in project fields or YAML data
            for field, value in preserved_fields.items():
                if field not in project_fields and field not in ("priority", "sprint", "size") and (not yaml_data or field not in yaml_data):
                    yaml_issue[field] = value
                    
            updated += 1
        else:
            # Create new issue
            new_issue = {
                "github_issue": int(gh_id),
                "title": gh_issue.get("title", f"Issue #{gh_id}"),
                "description": gh_issue.get("body", "") or "[no description]",
                "status": gh_issue["state"]  # Add status field (open/closed)
            }
            
            # Add project fields
            for field in ("priority", "sprint", "size"):
                if field in project_fields:
                    new_issue[field] = project_fields[field]
            
            # Add YAML data from issue body
            if isinstance(yaml_data, dict):
                for field, value in yaml_data.items():
                    new_issue[field] = value
                    
            updated_issues.append(new_issue)
            added += 1

    print(f"Pull summary: {added} added, {updated} updated, {status_changed} status changes")
    
    # Save changes if not in dry run mode
    if not dry_run:
        if save_yaml_issues(updated_issues):
            print(f"Updated local YAML file: {YAML_PATH}")
        else:
            print("Failed to update local YAML file")
    else:
        print("Dry run: not saving changes to YAML file.")
        
    return updated_issues


def push_to_github(issues: List[Dict[str, Any]], github_issues=None, gh_issues=None, dry_run=False):
    """Push issues from local YAML to GitHub."""
    print("🔁 Syncing issues to GitHub...")

    # Handle both parameter names for backward compatibility
    if github_issues is not None and gh_issues is None:
        gh_issues = github_issues
    elif gh_issues is None:
        gh_issues = []

    gh_map = {}

    # Build a map of GitHub issues by issue number (pull requests already filtered out in fetch_github_issues)
    for gh_issue in gh_issues:
        gh_id = str(gh_issue["number"])
        gh_map[gh_id] = gh_issue

    created = 0
    updated = 0
    skipped = 0
    
    # Process each issue in the YAML file
    for issue in issues:
        # Skip issues without component field
        if "component" not in issue:
            skipped += 1
            continue
            
        # Create title from component if not present
        if "title" not in issue:
            issue["title"] = f"[{issue['component']}] {issue.get('impact', 'Issue')}"
            
        # Create description from YAML fields if not present
        if "description" not in issue:
            yaml_block = yaml.dump(
                {k: v for k, v in issue.items() if k not in ["github_issue", "title", "description"]},
                default_flow_style=False
            )
            issue["description"] = f"```yaml\n{yaml_block}```"

        # Check if this issue matches an existing GitHub issue by component
        gh_entry = None
        gh_id = str(issue.get("github_issue", ""))
        
        if gh_id and gh_id in gh_map:
            # Direct match by issue number
            gh_entry = gh_map[gh_id]
        else:
            # Try to match by component in the body
            for gh_issue in gh_issues:
                body = gh_issue.get("body", "")
                yaml_data = extract_yaml_from_body(body)
                if yaml_data and "component" in yaml_data:
                    if yaml_data["component"].lower() == issue["component"].lower():
                        gh_entry = gh_issue
                        break

        node_id = None

        if gh_entry:
            # Update existing issue
            try:
                # Preserve existing labels if any
                labels = []
                if "labels" in gh_entry:
                    labels = [label["name"] for label in gh_entry["labels"] if isinstance(label, dict) and "name" in label]
                
                # Set state based on status
                state = "closed" if issue.get("status", "").lower() == "done" else "open"
                
                # Update the issue
                if dry_run:
                    print(f"[DRY-RUN] Would update issue #{gh_entry['number']}: {issue['title']}")
                else:
                    headers = setup_api_headers()
                    payload = {
                        "title": issue["title"],
                        "body": issue["description"],
                        "state": state
                    }
                    
                    # Include labels if they exist
                    if labels:
                        payload["labels"] = labels
                    
                    r = requests.patch(
                        f"{ISSUES_ENDPOINT}/{gh_entry['number']}", 
                        headers=headers, 
                        json=payload
                    )
                    
                    if r.status_code != 200:
                        print(f"Error updating GitHub issue #{gh_entry['number']}: {r.text}")
                    
                node_id = gh_entry.get("node_id")
                updated += 1
            except Exception as e:
                print(f"Error updating issue: {e}")
        else:
            # Create new issue
            try:
                if dry_run:
                    print(f"[DRY-RUN] Would create new issue: {issue['title']}")
                else:
                    headers = setup_api_headers()
                    payload = {
                        "title": issue["title"],
                        "body": issue["description"]
                    }
                    
                    r = requests.post(ISSUES_ENDPOINT, headers=headers, json=payload)
                    
                    if r.status_code in (200, 201):
                        new_issue = r.json()
                        issue["github_issue"] = new_issue["number"]
                        node_id = new_issue.get("node_id")
                    else:
                        print(f"Error creating GitHub issue: {r.text}")
                
                created += 1
            except Exception as e:
                print(f"Error creating issue: {e}")
    
    print(f"Push summary: {created} created, {updated} updated, {skipped} skipped")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Sync GitHub issues with local YAML file")
    parser.add_argument("--mode", choices=["push", "pull", "sync"], default="sync",
                      help="Sync mode: push (YAML to GitHub), pull (GitHub to YAML), or sync (both)")
    parser.add_argument("--dry-run", action="store_true", help="Don't make any changes, just show what would happen")
    parser.add_argument("--debug", action="store_true", help="Print debug information")
    parser.add_argument("--project-id", help="Override the GITHUB_PROJECT_ID environment variable")
    args = parser.parse_args()

    # Override environment variables if provided as arguments
    global GITHUB_PROJECT_ID
    if args.project_id:
        GITHUB_PROJECT_ID = args.project_id
        print(f"Using project ID from command line: {GITHUB_PROJECT_ID}")

    # Debug information
    if args.debug:
        print("Environment variables:")
        print(f"GITHUB_PROJECT_ID: {GITHUB_PROJECT_ID or 'Not set'}")
        print(f"REPO_OWNER: {REPO_OWNER or 'Not set'}")
        print(f"REPO_NAME: {REPO_NAME or 'Not set'}")
        print("\nProject field map:")
        for field, data in PROJECT_FIELD_MAP.items():
            print(f"  {field}: {data['field_id']}")
            print(f"    Options: {data['options']}")
        
    # Check required environment variables
    if not all([GITHUB_TOKEN, GITHUB_PROJECT_ID, REPO_OWNER, REPO_NAME]):
        print("Missing environment variables. Set GH_TOKEN, PROJECT_ID, REPO_OWNER, and REPO_NAME.")
        print("You can also use --project-id to override the PROJECT_ID environment variable.")
        sys.exit(1)

    # Load issues from YAML
    yaml_issues = load_yaml_issues()
    if not yaml_issues and args.mode != "pull":
        print("No YAML issues found.")
        sys.exit(1)

    # Fetch issues from GitHub
    gh_issues = fetch_github_issues()
    print(f"Fetched {len(gh_issues)} GitHub issues")

    # Perform the requested operation
    if args.mode in ("push", "sync"):
        push_to_github(yaml_issues, gh_issues, dry_run=args.dry_run)

    if args.mode in ("pull", "sync"):
        yaml_issues = pull_from_github(yaml_issues, gh_issues, dry_run=args.dry_run)
        print_issue_table(yaml_issues)

    print("Sync complete")


if __name__ == "__main__":
    main()