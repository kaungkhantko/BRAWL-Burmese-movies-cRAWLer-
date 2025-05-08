import yaml
import pytest

REQUIRED_FIELDS = ["component", "category", "severity", "impact", "suggestion", "status"]

def test_issues_yaml_structure():
    with open("docs/issues.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # If root is a list, treat it as issues
    if isinstance(data, list):
        issues = data
    elif isinstance(data, dict) and "Further Improvements" in data:
        issues = data["Further Improvements"]
    else:
        raise AssertionError("Unrecognized YAML structure in docs/issues.yaml")

    assert isinstance(issues, list), "Expected issues to be a list"

    for idx, issue in enumerate(issues):
        for field in REQUIRED_FIELDS:
            assert field in issue, f"Issue {idx} missing required field: {field}"
