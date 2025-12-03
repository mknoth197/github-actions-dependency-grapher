# GitHub Actions Dependency Grapher

A comprehensive tool that allows developers to seamlessly understand their Software Supply Chain for GitHub Actions CI/CD workflows.

## 🎯 Problem Statement

As a user of GitHub Actions, it is very difficult to quickly inventory and observe what workflows/actions are being used from a Software Supply Chain perspective. You cannot manage what you cannot observe.

**Goal**: Create a tool that allows developers to quickly understand what dependencies are being used inside GitHub Action workflows.

## 📋 Status

Currently in **Iteration 2: Local Development Environment** of the [ITERATION_PLAN.md](ITERATION_PLAN.md).

### Completed
- ✅ Iteration 1: Research & Planning
- ✅ Probot app with TypeScript, webhook handlers, and SNS publisher
- ✅ Lambda workflow analyzer with Python and PyYAML
- 🔄 Iteration 2: Local Development Environment (in progress)

## 🏗️ Architecture Overview

This project implements an event-driven architecture using AWS services and GitHub Apps:

```
GitHub Events → Probot App (ECS Fargate) → SNS → SQS FIFO → Lambda → Data Store
```

### Components

1. **Probot App** (`probot-app/`)
   - GitHub App webhook receiver
   - Validates webhooks and filters workflow-related events
   - Publishes events to SNS for asynchronous processing
   - Built with TypeScript and Probot framework

2. **Workflow Analyzer Lambda** (`event-processors/workflow-analyzer/`)
   - Fetches workflow files from GitHub
   - Parses YAML to extract dependencies
   - Analyzes version pinning strategies (SHA, tag, branch, unpinned)
   - Identifies actions, runners, and container dependencies
   - Built with Python and PyYAML

3. **Infrastructure** (`infrastructure/`)
   - Terraform/OpenTofu IaC for AWS resources
   - SNS topics and SQS FIFO queues
   - ECS Fargate service for Probot app
   - Lambda functions for workflow analysis
   - DynamoDB for data storage (planned)

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.12+
- AWS Account (for deployment)
- GitHub App credentials (for testing)

### Local Development

#### Probot App

```bash
cd probot-app
npm install
npm run build
npm test
```

See [probot-app/README.md](probot-app/README.md) for detailed setup instructions.

#### Workflow Analyzer Lambda

```bash
cd event-processors/workflow-analyzer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

See [event-processors/workflow-analyzer/README.md](event-processors/workflow-analyzer/README.md) for detailed setup instructions.

## 📊 Features

### Current (MVP)
- Webhook event processing for push and pull_request events
- Workflow file parsing and dependency extraction
- Version pinning analysis (SHA, semantic version tags, branches)
- Runner image tracking
- Container dependency detection

### Planned
- Data storage in DynamoDB
- Multi-workflow and multi-repository support
- Security scanning integration
- Compliance reporting
- Data visualization dashboard
- PR comments with dependency diffs

## 📖 Documentation

- [ITERATION_PLAN.md](ITERATION_PLAN.md) - Complete development roadmap and architecture decisions
- [probot-app/README.md](probot-app/README.md) - Probot app documentation
- [event-processors/workflow-analyzer/README.md](event-processors/workflow-analyzer/README.md) - Lambda function documentation

## 🤝 Contributing

This project follows the iteration plan defined in [ITERATION_PLAN.md](ITERATION_PLAN.md). Contributions should align with the current iteration goals.

## 📝 License

ISC
