import { Context } from 'probot';
import { SNSPublisher } from '../services/sns';
import type { WorkflowEvent } from '../types/events';

export async function handlePushEvent(context: Context<'push'>, snsPublisher: SNSPublisher) {
  const payload = context.payload;
  
  // Filter for changes to .github/workflows/ directory
  const workflowChanges = payload.commits?.some((commit) =>
    commit.added?.some((file) => file.startsWith('.github/workflows/')) ||
    commit.modified?.some((file) => file.startsWith('.github/workflows/')) ||
    commit.removed?.some((file) => file.startsWith('.github/workflows/'))
  );

  if (!workflowChanges) {
    context.log.info('No workflow changes detected, skipping');
    return;
  }

  // Extract all workflow files that were modified
  const workflowFiles = new Set<string>();
  payload.commits?.forEach((commit) => {
    commit.added?.filter((f) => f.startsWith('.github/workflows/')).forEach((f) => workflowFiles.add(f));
    commit.modified?.filter((f) => f.startsWith('.github/workflows/')).forEach((f) => workflowFiles.add(f));
  });

  context.log.info(`Found ${workflowFiles.size} workflow file(s) changed`);

  // Publish events for each workflow file
  for (const workflowPath of workflowFiles) {
    const event: WorkflowEvent = {
      repository: {
        owner: payload.repository.owner?.login || 'unknown',
        name: payload.repository.name,
        fullName: payload.repository.full_name,
      },
      workflow: {
        path: workflowPath,
        ref: payload.ref,
      },
      commit: {
        sha: payload.head_commit?.id || payload.after,
        message: payload.head_commit?.message || '',
        author: payload.head_commit?.author?.name || payload.pusher.name,
      },
      eventType: 'push',
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
