import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';
import type { WorkflowEvent } from '../types/events';

export class SNSPublisher {
  private client: SNSClient;
  private topicArn: string;

  constructor(topicArn?: string, region?: string) {
    this.topicArn = topicArn || process.env.SNS_TOPIC_ARN || '';
    this.client = new SNSClient({ region: region || process.env.AWS_REGION || 'us-east-1' });
  }

  async publishWorkflowEvent(event: WorkflowEvent): Promise<void> {
    if (!this.topicArn) {
      console.warn('SNS_TOPIC_ARN not configured, skipping SNS publish');
      return;
    }

    const messageGroupId = `${event.repository.fullName}-${event.workflow.path}`;

    try {
      const command = new PublishCommand({
        TopicArn: this.topicArn,
        Message: JSON.stringify(event),
        MessageGroupId: messageGroupId,
        MessageDeduplicationId: `${event.commit.sha}-${event.timestamp}`,
      });

      await this.client.send(command);
      console.log(`Published event to SNS for ${event.repository.fullName}/${event.workflow.path}`);
    } catch (error) {
      console.error('Failed to publish to SNS:', error);
      throw error;
    }
  }
}
