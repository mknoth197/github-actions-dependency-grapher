export interface WorkflowEvent {
  repository: {
    owner: string;
    name: string;
    fullName: string;
  };
  workflow: {
    path: string;
    ref: string;
  };
  commit: {
    sha: string;
    message: string;
    author: string;
  };
  eventType: string;
  timestamp: string;
}

export interface WorkflowDependency {
  type: 'action' | 'runner' | 'container';
  name: string;
  version?: string;
  pinningStrategy: 'sha' | 'tag' | 'branch' | 'unpinned';
  rawReference: string;
}

export interface WorkflowAnalysis {
  event: WorkflowEvent;
  dependencies: WorkflowDependency[];
  metadata: {
    workflowName?: string;
    jobs: string[];
    totalSteps: number;
  };
}
