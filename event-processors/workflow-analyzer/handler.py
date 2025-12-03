"""
Lambda handler for workflow analysis.
"""
import base64
import json
import os
import sys
from datetime import datetime
from typing import Any

import requests

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import WorkflowEvent

from analyzer import WorkflowAnalyzer


class GitHubClient:
    """Client for fetching workflow files from GitHub."""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_workflow_content(self, owner: str, repo: str, path: str, ref: str) -> str:
        """
        Fetch workflow file content from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path to workflow file
            ref: Git reference (branch, tag, or commit SHA)

        Returns:
            Workflow file content as string
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}

        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # GitHub API returns content as base64
        content = base64.b64decode(data['content']).decode('utf-8')
        return content


def parse_sqs_event(record: dict[str, Any]) -> WorkflowEvent:
    """Parse SQS message to WorkflowEvent."""
    # SNS message is wrapped in SQS record
    body = json.loads(record['body'])

    # If it's from SNS, extract the Message
    if 'Message' in body:
        message = json.loads(body['Message'])
    else:
        message = body

    return WorkflowEvent(
        repository_owner=message['repository']['owner'],
        repository_name=message['repository']['name'],
        repository_full_name=message['repository']['fullName'],
        workflow_path=message['workflow']['path'],
        workflow_ref=message['workflow']['ref'],
        commit_sha=message['commit']['sha'],
        commit_message=message['commit']['message'],
        commit_author=message['commit']['author'],
        event_type=message['eventType'],
        timestamp=message['timestamp'],
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for processing workflow analysis events.

    Args:
        event: SQS event containing workflow information
        context: Lambda context

    Returns:
        Response with processed count
    """
    print(f"Received event with {len(event.get('Records', []))} records")

    # Get GitHub token from environment
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    github_client = GitHubClient(github_token)
    analyzer = WorkflowAnalyzer()

    processed_count = 0
    failed_count = 0

    for record in event.get('Records', []):
        try:
            # Parse event
            workflow_event = parse_sqs_event(record)
            print(f"Processing workflow: {workflow_event.workflow_path} "
                  f"from {workflow_event.repository_full_name}")

            # Fetch workflow content from GitHub
            workflow_content = github_client.get_workflow_content(
                owner=workflow_event.repository_owner,
                repo=workflow_event.repository_name,
                path=workflow_event.workflow_path,
                ref=workflow_event.commit_sha,
            )

            # Analyze workflow
            analysis_result = analyzer.analyze_workflow(workflow_content)

            # Add event metadata to result
            result = {
                'event': {
                    'repository': workflow_event.repository_full_name,
                    'workflow_path': workflow_event.workflow_path,
                    'commit_sha': workflow_event.commit_sha,
                    'commit_author': workflow_event.commit_author,
                    'event_type': workflow_event.event_type,
                    'timestamp': workflow_event.timestamp,
                },
                'analysis': analysis_result,
                'analyzed_at': datetime.utcnow().isoformat(),
            }

            # TODO: Store result in DynamoDB or other data store
            print(f"Analysis complete: {json.dumps(result, indent=2)}")

            processed_count += 1

        except Exception as e:
            print(f"Error processing record: {str(e)}")
            failed_count += 1
            # Continue processing other records
            continue

    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed_count,
            'failed': failed_count,
        }),
    }
