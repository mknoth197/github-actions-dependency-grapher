"""
Data models for workflow analysis.
"""
from dataclasses import dataclass
from typing import List, Literal, Optional
from datetime import datetime


@dataclass
class WorkflowEvent:
    """Represents a GitHub workflow event from SNS/SQS."""
    repository_owner: str
    repository_name: str
    repository_full_name: str
    workflow_path: str
    workflow_ref: str
    commit_sha: str
    commit_message: str
    commit_author: str
    event_type: str
    timestamp: str


@dataclass
class WorkflowDependency:
    """Represents a single dependency found in a workflow."""
    type: Literal['action', 'runner', 'container']
    name: str
    version: Optional[str]
    pinning_strategy: Literal['sha', 'tag', 'branch', 'unpinned']
    raw_reference: str


@dataclass
class WorkflowAnalysis:
    """Complete analysis result for a workflow."""
    event: WorkflowEvent
    dependencies: List[WorkflowDependency]
    workflow_name: Optional[str]
    jobs: List[str]
    total_steps: int
    analyzed_at: datetime
