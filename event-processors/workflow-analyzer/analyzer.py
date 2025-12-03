"""
Workflow analyzer module for parsing GitHub Actions workflows.
"""
import os
import re
import sys
from typing import Any

import yaml

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import WorkflowDependency


class WorkflowAnalyzer:
    """Analyzes GitHub Actions workflow YAML files to extract dependencies."""

    SHA_PATTERN = re.compile(r'^[a-f0-9]{40}$')
    SEMVER_PATTERN = re.compile(r'^v?\d+\.\d+\.\d+')

    def analyze_workflow(self, workflow_content: str) -> dict[str, Any]:
        """
        Parse workflow YAML and extract dependencies.

        Args:
            workflow_content: Raw YAML content of the workflow file

        Returns:
            Dictionary containing workflow metadata and dependencies
        """
        try:
            workflow = yaml.safe_load(workflow_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}") from e

        if not isinstance(workflow, dict):
            raise ValueError("Workflow must be a YAML dictionary")

        dependencies = []
        jobs_list = []
        total_steps = 0

        workflow_name = workflow.get('name')
        jobs = workflow.get('jobs', {})

        for job_name, job_config in jobs.items():
            if not isinstance(job_config, dict):
                continue

            jobs_list.append(job_name)

            # Extract runner information
            runs_on = job_config.get('runs-on')
            if runs_on:
                runner_deps = self._extract_runner_dependencies(runs_on)
                dependencies.extend(runner_deps)

            # Extract container information
            container = job_config.get('container')
            if container:
                container_deps = self._extract_container_dependencies(container)
                dependencies.extend(container_deps)

            # Extract action dependencies from steps
            steps = job_config.get('steps', [])
            total_steps += len(steps)

            for step in steps:
                if not isinstance(step, dict):
                    continue

                uses = step.get('uses')
                if uses:
                    action_dep = self._extract_action_dependency(uses)
                    if action_dep:
                        dependencies.append(action_dep)

        return {
            'workflow_name': workflow_name,
            'jobs': jobs_list,
            'total_steps': total_steps,
            'dependencies': [self._dependency_to_dict(d) for d in dependencies],
        }

    def _extract_action_dependency(self, uses: str) -> WorkflowDependency | None:
        """Extract action dependency from 'uses' statement."""
        if not uses or not isinstance(uses, str):
            return None

        # Handle docker:// references
        if uses.startswith('docker://'):
            container_image = uses[9:]  # Remove 'docker://'
            return WorkflowDependency(
                type='container',
                name=container_image.split(':')[0] if ':' in container_image else container_image,
                version=container_image.split(':')[1] if ':' in container_image else None,
                pinning_strategy='tag' if ':' in container_image else 'unpinned',
                raw_reference=uses,
            )

        # Handle local actions (./) and relative paths
        if uses.startswith('./') or uses.startswith('../'):
            return None  # Skip local actions for now

        # Parse action reference (e.g., "actions/checkout@v3")
        parts = uses.split('@')
        if len(parts) != 2:
            return WorkflowDependency(
                type='action',
                name=uses,
                version=None,
                pinning_strategy='unpinned',
                raw_reference=uses,
            )

        action_name, version_ref = parts
        pinning_strategy = self._determine_pinning_strategy(version_ref)

        return WorkflowDependency(
            type='action',
            name=action_name,
            version=version_ref,
            pinning_strategy=pinning_strategy,
            raw_reference=uses,
        )

    def _extract_runner_dependencies(self, runs_on: Any) -> list[WorkflowDependency]:
        """Extract runner dependencies from runs-on specification."""
        runners = []

        if isinstance(runs_on, str):
            runners = [runs_on]
        elif isinstance(runs_on, list):
            runners = [r for r in runs_on if isinstance(r, str)]

        dependencies = []
        for runner in runners:
            dependencies.append(WorkflowDependency(
                type='runner',
                name=runner,
                version=None,
                pinning_strategy='unpinned',
                raw_reference=runner,
            ))

        return dependencies

    def _extract_container_dependencies(self, container: Any) -> list[WorkflowDependency]:
        """Extract container dependencies."""
        dependencies = []

        if isinstance(container, str):
            # Simple string: "ubuntu:20.04"
            image_parts = container.split(':')
            dependencies.append(WorkflowDependency(
                type='container',
                name=image_parts[0],
                version=image_parts[1] if len(image_parts) > 1 else None,
                pinning_strategy='tag' if len(image_parts) > 1 else 'unpinned',
                raw_reference=container,
            ))
        elif isinstance(container, dict):
            # Complex container definition
            image = container.get('image')
            if image and isinstance(image, str):
                image_parts = image.split(':')
                dependencies.append(WorkflowDependency(
                    type='container',
                    name=image_parts[0],
                    version=image_parts[1] if len(image_parts) > 1 else None,
                    pinning_strategy='tag' if len(image_parts) > 1 else 'unpinned',
                    raw_reference=image,
                ))

        return dependencies

    def _determine_pinning_strategy(self, version_ref: str) -> str:
        """Determine the pinning strategy based on version reference."""
        if self.SHA_PATTERN.match(version_ref):
            return 'sha'
        elif self.SEMVER_PATTERN.match(version_ref):
            return 'tag'
        elif version_ref in ['main', 'master', 'develop', 'dev']:
            return 'branch'
        else:
            # Could be a tag or branch, default to tag
            return 'tag'

    def _dependency_to_dict(self, dep: WorkflowDependency) -> dict[str, Any]:
        """Convert WorkflowDependency to dictionary."""
        return {
            'type': dep.type,
            'name': dep.name,
            'version': dep.version,
            'pinning_strategy': dep.pinning_strategy,
            'raw_reference': dep.raw_reference,
        }
