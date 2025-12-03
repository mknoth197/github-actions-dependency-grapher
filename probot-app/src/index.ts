import { Probot } from 'probot';
import { SNSPublisher } from './services/sns';
import { handlePushEvent } from './webhooks/push';
import { handlePullRequestEvent } from './webhooks/pullRequest';

export default (app: Probot) => {
  const snsPublisher = new SNSPublisher();

  app.log.info('GitHub Actions Dependency Grapher Probot app loaded');

  // Push event handler
  app.on('push', async (context) => {
    try {
      await handlePushEvent(context, snsPublisher);
    } catch (error) {
      app.log.error('Error handling push event');
      app.log.error(error as Error);
    }
  });

  // Pull request event handler
  app.on('pull_request', async (context) => {
    try {
      await handlePullRequestEvent(context, snsPublisher);
    } catch (error) {
      app.log.error('Error handling pull_request event');
      app.log.error(error as Error);
    }
  });

  app.log.info('All webhook handlers registered');
};
