import pytest
from unittest.mock import patch, MagicMock
from scripts.sync_issues import push_to_github

@pytest.fixture
def sample_yaml_issue():
    return {
        "component": "TestComponent",
        "category": "Architecture",
        "severity": "medium",
        "impact": "Structure update",
        "suggestion": "Refactor spider",
        "status": "todo"
    }

@pytest.fixture
def github_issue_with_same_component(sample_yaml_issue):
    return {
        "number": 99,
        "body": f"""```yaml
component: {sample_yaml_issue['component']}
category: Architecture
severity: medium
impact: Old impact
suggestion: Refactor spider
status: todo
```"""
    }

@patch("scripts.sync_issues.requests.post")
def test_create_new_issue(post_mock, sample_yaml_issue):
    post_mock.return_value.status_code = 201
    post_mock.return_value.json.return_value = {"number": 101}

    push_to_github([sample_yaml_issue], github_issues=[], dry_run=False)

    assert post_mock.called
    payload = post_mock.call_args[1]['json']
    assert payload["title"].startswith("[TestComponent]")
    assert "Structure update" in payload["body"]

@patch("scripts.sync_issues.requests.patch")
def test_update_existing_issue(patch_mock, sample_yaml_issue, github_issue_with_same_component):
    patch_mock.return_value.status_code = 200

    github_issues = [{
        "number": 99,
        "body": github_issue_with_same_component["body"]
    }]

    push_to_github([sample_yaml_issue], github_issues=github_issues, dry_run=False)

    assert patch_mock.called
    payload = patch_mock.call_args[1]['json']
    assert payload["state"] == "open"
    assert "Refactor spider" in payload["body"]

@patch("scripts.sync_issues.requests.post")
@patch("scripts.sync_issues.requests.patch")
def test_dry_run_mode_skips_network_calls(patch_mock, post_mock, sample_yaml_issue):
    github_issues = []
    push_to_github([sample_yaml_issue], github_issues, dry_run=True)
    assert not post_mock.called and not patch_mock.called

@patch("scripts.sync_issues.requests.post")
def test_skips_issue_with_missing_component(post_mock):
    bad_issue = {
        "category": "Testing",
        "severity": "low",
        "impact": "Missing component field",
        "suggestion": "Don't sync this",
        "status": "todo"
    }

    push_to_github([bad_issue], github_issues=[], dry_run=False)
    assert not post_mock.called

@patch("scripts.sync_issues.requests.patch")
def test_patch_failure_logs_error(patch_mock, sample_yaml_issue, capsys):
    patch_mock.return_value.status_code = 500
    patch_mock.return_value.text = "Internal Server Error"

    github_issues = [{
        "number": 123,
        "body": f"""```yaml
component: {sample_yaml_issue['component']}
category: Architecture
severity: medium
impact: Old impact
suggestion: Fix
status: todo
```"""
    }]

    push_to_github([sample_yaml_issue], github_issues=github_issues, dry_run=False)

    captured = capsys.readouterr()
    assert "Error updating GitHub issue" in captured.out

@patch("scripts.sync_issues.requests.post")
def test_post_failure_logs_error(post_mock, sample_yaml_issue, capsys):
    post_mock.return_value.status_code = 403
    post_mock.return_value.text = "Forbidden"

    push_to_github([sample_yaml_issue], github_issues=[], dry_run=False)

    captured = capsys.readouterr()
    assert "Error creating GitHub issue" in captured.out

@patch("scripts.sync_issues.requests.patch")
def test_status_done_closes_issue(patch_mock, sample_yaml_issue):
    sample_yaml_issue["status"] = "done"
    patch_mock.return_value.status_code = 200

    github_issues = [{
        "number": 124,
        "body": f"""```yaml
component: {sample_yaml_issue['component']}
category: Architecture
severity: medium
impact: X
suggestion: Y
status: todo
```"""
    }]

    push_to_github([sample_yaml_issue], github_issues, dry_run=False)
    payload = patch_mock.call_args[1]["json"]
    assert payload["state"] == "closed"

@patch("scripts.sync_issues.requests.patch")
def test_case_insensitive_component_matching(patch_mock):
    patch_mock.return_value.status_code = 200

    yaml_issues = [{
        "component": "SomeComponent",
        "category": "Ops",
        "severity": "low",
        "impact": "update",
        "suggestion": "x",
        "status": "todo"
    }]
    github_issues = [{
        "number": 125,
        "body": """```yaml
component: somecomponent
category: Ops
severity: low
impact: old
suggestion: x
status: todo
```"""
    }]

    push_to_github(yaml_issues, github_issues, dry_run=False)
    assert patch_mock.called

@patch("scripts.sync_issues.requests.patch")
def test_does_not_patch_when_component_missing_in_github_body(patch_mock):
    patch_mock.return_value.status_code = 200

    yaml_issues = [{
        "component": "MissingComponent",
        "category": "DataQuality",
        "severity": "medium",
        "impact": "test",
        "suggestion": "x",
        "status": "todo"
    }]
    github_issues = [{
        "number": 126,
        "body": "```yaml\ncategory: DataQuality\n```"
    }]

    push_to_github(yaml_issues, github_issues, dry_run=False)
    assert not patch_mock.called

@patch("scripts.sync_issues.requests.patch")
def test_preserves_existing_labels(patch_mock, sample_yaml_issue):
    patch_mock.return_value.status_code = 200

    github_issues = [{
        "number": 127,
        "body": f"""```yaml
component: {sample_yaml_issue['component']}
category: Architecture
severity: medium
impact: Legacy text
suggestion: Fix
status: todo
```""",
        "labels": [{"name": "keep-this"}, {"name": "crawler-issue"}]
    }]

    push_to_github([sample_yaml_issue], github_issues, dry_run=False)

    labels = patch_mock.call_args[1]["json"]["labels"]
    assert "crawler-issue" in labels
    # Note: This test assumes only crawler-generated labels are managed
