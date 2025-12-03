import { SNSPublisher } from '../sns';
import type { WorkflowEvent } from '../../types/events';

describe('SNSPublisher', () => {
  let publisher: SNSPublisher;

  beforeEach(() => {
    // Initialize without actual AWS credentials for unit testing
    publisher = new SNSPublisher('arn:aws:sns:us-east-1:123456789012:test-topic', 'us-east-1');
  });

  it('should create instance with correct configuration', () => {
    expect(publisher).toBeDefined();
  });

  it('should handle missing topic ARN gracefully', async () => {
    const publisherNoTopic = new SNSPublisher('', 'us-east-1');
    const event: WorkflowEvent = {
      repository: {
        owner: 'testowner',
        name: 'testrepo',
        fullName: 'testowner/testrepo',
      },
      workflow: {
        path: '.github/workflows/test.yml',
        ref: 'refs/heads/main',
      },
      commit: {
        sha: 'abc123',
        message: 'test commit',
        author: 'testuser',
      },
      eventType: 'push',
      timestamp: new Date().toISOString(),
    };

    await expect(publisherNoTopic.publishWorkflowEvent(event)).resolves.toBeUndefined();
  });
});
