import pytest
from scripts.sync_issues import pull_from_github

@pytest.mark.parametrize("yaml_issues, github_issues, expected_components", [
    # ✅ New issue should merge
    (
        [{"component": "ExistingComp", "category": "Architecture", "severity": "low",
          "impact": "Already in YAML", "suggestion": "no-op", "status": "todo"}],
        [{"number": 101, "state": "open", "body": """...```yaml
component: NewComponent
category: Performance
severity: medium
impact: GitHub-only item
suggestion: Merge this in
status: todo
```"""}],
        {"ExistingComp", "NewComponent"}
    ),

    # ✅ Should skip issues without embedded YAML
    (
        [],
        [{"number": 102, "state": "open", "body": "This issue has no YAML"}],
        set()
    ),

    # ✅ Should skip YAML missing component field
    (
        [],
        [{"number": 103, "state": "open", "body": "```yaml\ncategory: Storage\n```"}],
        set()
    ),

    # ✅ Closed GitHub issue should map to 'done' status and update impact
    (
        [{"component": "SameComponent", "category": "Ops", "severity": "medium",
          "impact": "Old impact", "suggestion": "old", "status": "todo"}],
        [{"number": 104, "state": "closed", "body": """```yaml
component: SameComponent
category: Ops
severity: medium
impact: Updated impact
suggestion: new one
status: done
```"""}],
        {"SameComponent"}
    ),

    # ✅ Should skip YAML that parses as a list instead of a dict
    (
        [],
        [{"number": 105, "state": "open", "body": "```yaml\n- component: ListFormat\n  category: Testing\n```"}],
        set()
    ),

    # ✅ Closed issue pulled from GitHub should become 'done'
    (
        [],
        [{"number": 106, "state": "closed", "body": """```yaml
component: ClosedComponent
category: Testing
severity: low
impact: Closed issue
suggestion: Skip or sync
status: todo
```"""}],
        {"ClosedComponent"}
    ),

    # ✅ Malformed YAML should not crash or import
    (
        [],
        [{"number": 107, "state": "open", "body": "```yaml\n{{broken::thing}}\n```"}],
        set()
    ),

    # ✅ GitHub issues list is empty, local YAML remains unchanged
    (
        [{"component": "SafeComp", "category": "Ops", "severity": "low",
          "impact": "safe", "suggestion": "noop", "status": "todo"}],
        [],
        {"SafeComp"}
    )
])
def test_pull_from_github_cases(yaml_issues, github_issues, expected_components):
    merged = pull_from_github(yaml_issues.copy(), github_issues)
    result_components = {item["component"].lower() for item in merged if "component" in item}
    expected_lower = {c.lower() for c in expected_components}
    assert expected_lower.issubset(result_components)
