"""
Tests for workflow analyzer.
"""
import os
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer import WorkflowAnalyzer


@pytest.fixture
def analyzer():
    return WorkflowAnalyzer()


def test_analyze_simple_workflow(analyzer):
    """Test analyzing a simple workflow."""
    workflow_yaml = """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
"""
    result = analyzer.analyze_workflow(workflow_yaml)

    assert result['workflow_name'] == 'CI'
    assert 'test' in result['jobs']
    assert result['total_steps'] == 2
    assert len(result['dependencies']) == 3  # 1 runner + 2 actions


def test_extract_action_with_sha(analyzer):
    """Test extracting action with SHA pinning."""
    uses = "actions/checkout@8e5e7e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e"
    dep = analyzer._extract_action_dependency(uses)

    assert dep is not None
    assert dep.type == 'action'
    assert dep.name == 'actions/checkout'
    assert dep.pinning_strategy == 'sha'


def test_extract_action_with_tag(analyzer):
    """Test extracting action with tag pinning."""
    uses = "actions/checkout@v3"
    dep = analyzer._extract_action_dependency(uses)

    assert dep is not None
    assert dep.type == 'action'
    assert dep.name == 'actions/checkout'
    assert dep.version == 'v3'
    assert dep.pinning_strategy == 'tag'


def test_extract_action_with_branch(analyzer):
    """Test extracting action with branch reference."""
    uses = "actions/checkout@main"
    dep = analyzer._extract_action_dependency(uses)

    assert dep is not None
    assert dep.type == 'action'
    assert dep.pinning_strategy == 'branch'


def test_extract_docker_action(analyzer):
    """Test extracting docker:// action."""
    uses = "docker://alpine:3.14"
    dep = analyzer._extract_action_dependency(uses)

    assert dep is not None
    assert dep.type == 'container'
    assert dep.name == 'alpine'
    assert dep.version == '3.14'


def test_extract_runner_dependencies(analyzer):
    """Test extracting runner dependencies."""
    # String runner
    deps = analyzer._extract_runner_dependencies("ubuntu-latest")
    assert len(deps) == 1
    assert deps[0].type == 'runner'
    assert deps[0].name == 'ubuntu-latest'

    # List of runners
    deps = analyzer._extract_runner_dependencies(["ubuntu-latest", "windows-latest"])
    assert len(deps) == 2


def test_invalid_yaml(analyzer):
    """Test handling invalid YAML."""
    with pytest.raises(ValueError, match="Invalid YAML"):
        analyzer.analyze_workflow("invalid: yaml: content:")


def test_complex_workflow(analyzer):
    """Test analyzing a complex workflow with multiple jobs."""
    workflow_yaml = """
name: Complex CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    container: node:18
    steps:
      - uses: actions/checkout@2541b1294d2704b0964813337f33b291d3f8596b
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install

  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm test

  lint:
    runs-on: [ubuntu-latest, self-hosted]
    steps:
      - uses: actions/checkout@main
"""
    result = analyzer.analyze_workflow(workflow_yaml)

    assert result['workflow_name'] == 'Complex CI'
    assert len(result['jobs']) == 3
    assert 'build' in result['jobs']
    assert 'test' in result['jobs']
    assert 'lint' in result['jobs']

    # Check dependencies
    deps = result['dependencies']

    # Find SHA pinned action
    sha_actions = [d for d in deps if d.get('pinning_strategy') == 'sha']
    assert len(sha_actions) > 0

    # Find branch reference
    branch_actions = [d for d in deps if d.get('pinning_strategy') == 'branch']
    assert len(branch_actions) > 0

    # Find container
    containers = [d for d in deps if d.get('type') == 'container']
    assert len(containers) > 0


def test_skip_local_actions(analyzer):
    """Test that local actions are skipped."""
    uses_local = "./local-action"
    dep = analyzer._extract_action_dependency(uses_local)
    assert dep is None


def test_unpinned_action(analyzer):
    """Test extracting unpinned action."""
    uses = "actions/checkout"
    dep = analyzer._extract_action_dependency(uses)

    assert dep is not None
    assert dep.pinning_strategy == 'unpinned'
    assert dep.version is None
