from scripts.sync_issues import pull_from_github, extract_yaml_from_body

def test_merge_new_issue():
    yaml_issues = [
        {
            "component": "ExistingComp",
            "category": "Architecture",
            "severity": "low",
            "impact": "Already in YAML",
            "suggestion": "no-op",
            "status": "todo"
        }
    ]

    github_issues = [
        {
            "number": 101,
            "state": "open",
            "body": """---
... other text ...
```yaml
component: NewComponent
category: Performance
severity: medium
impact: GitHub-only item
suggestion: Merge this in
status: todo
```"""
        }
    ]

    merged = pull_from_github(yaml_issues.copy(), github_issues)
    components = [item["component"] for item in merged]
    assert "ExistingComp" in components
    assert "NewComponent" in components
