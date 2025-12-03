import { Context } from 'probot';
import { SNSPublisher } from '../services/sns';
import type { WorkflowEvent } from '../types/events';

export async function handlePullRequestEvent(
  context: Context<'pull_request'>,
  snsPublisher: SNSPublisher
) {
  const payload = context.payload;

  // Only process opened, synchronize, or reopened PRs
  if (!['opened', 'synchronize', 'reopened'].includes(payload.action)) {
    context.log.info(`Skipping PR action: ${payload.action}`);
    return;
  }

  // Get list of files changed in the PR
  const files = await context.octokit.rest.pulls.listFiles({
    owner: payload.repository.owner.login,
    repo: payload.repository.name,
    pull_number: payload.pull_request.number,
  });

  const workflowFiles = files.data
    .filter((file: { filename: string }) => file.filename.startsWith('.github/workflows/'))
    .map((file: { filename: string }) => file.filename);

  if (workflowFiles.length === 0) {
    context.log.info('No workflow changes detected in PR, skipping');
    return;
  }

  context.log.info(`Found ${workflowFiles.length} workflow file(s) changed in PR`);

  // Publish events for each workflow file
  for (const workflowPath of workflowFiles) {
    const event: WorkflowEvent = {
      repository: {
        owner: payload.repository.owner.login,
        name: payload.repository.name,
        fullName: payload.repository.full_name,
      },
      workflow: {
        path: workflowPath,
        ref: `refs/pull/${payload.pull_request.number}/head`,
      },
      commit: {
        sha: payload.pull_request.head.sha,
        message: payload.pull_request.title,
        author: payload.pull_request.user?.login || 'unknown',
      },
      eventType: 'pull_request',
      timestamp: new Date().toISOString(),
    };

    try {
      await snsPublisher.publishWorkflowEvent(event);
      context.log.info(`Published event for workflow: ${workflowPath}`);
    } catch (error) {
      context.log.error(`Failed to publish event for ${workflowPath}`);
      context.log.error(error as Error);
    }
  }
}
