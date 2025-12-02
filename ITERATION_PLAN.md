# GitHub Actions Dependency Grapher - Iteration Plan

## 🎯 Problem Statement

As a user of GitHub Actions, it is very difficult to quickly inventory and observe what workflows/actions are using from a Software Supply Chain perspective. You cannot manage what you cannot observe.

**Goal**: Create a tool that allows developers to quickly understand what dependencies are being used inside GitHub Action workflows.

**Scope (MVP)**: Single repository, single workflow - then iterate.

---

## 📊 What Developers Need to Know

### Primary Questions to Answer:
1. **What am I using?**
   - List all action dependencies with versions
   - Identify pinned vs unpinned versions
   - Show runner images being used

2. **Is it safe/current?**
   - Are versions pinned to SHA vs tags?
   - Are there known vulnerabilities?
   - Are versions outdated?

3. **Visualization**
   - Dependency graph/tree structure
   - Clear visual hierarchy (jobs → steps → actions)

---

## 🏗️ Technical Architecture

### High-Level Architecture
```
GitHub Events → GitHub App → Probot (ECS Fargate) → SNS/SQS FIFO → Lambda Processors → Data Store
                                     ↓
                              (Dumb Proxy)
```

### Technology Stack

#### Infrastructure (AWS)
- **Compute - Probot Server**: ECS Fargate (event proxy)
- **Compute - Event Processors**: AWS Lambda (business logic)
- **Messaging**: SNS + SQS FIFO (event queue)
- **Database**: TBD (DynamoDB, RDS, S3 + Athena)
- **IaC**: Terraform or OpenTofu (decision point - evaluate pros/cons during implementation)
- **Monitoring**: CloudWatch, X-Ray
- **Pre-existing**: VPC with public/private subnets, Route53 public hosted zone

#### Application Stack
- **GitHub Integration**: Probot framework (Node.js/TypeScript)
- **Event Processing**: Python or Node.js Lambda functions
- **YAML Parser**: PyYAML (Python) or js-yaml (Node.js)
- **Testing**: pytest (Python) or Jest (Node.js)
- **Type Safety**: TypeScript (Probot), mypy (Python Lambdas)

### Core Components
```
infrastructure/
├── probot-app/              # GitHub App (ECS Fargate)
│   ├── src/
│   │   ├── index.ts        # Probot app entry point
│   │   ├── webhooks/       # Webhook handlers (minimal logic)
│   │   └── sns/            # SNS publishing
│   ├── Dockerfile
│   └── package.json
│
├── event-processors/        # Lambda functions
│   ├── workflow-analyzer/  # Parse workflow files, extract dependencies
│   ├── deduplicator/       # Ensure idempotency
│   └── data-writer/        # Persist results to data store
│
├── messaging/
│   ├── sns-topics.yaml     # SNS topic definitions
│   └── sqs-queues.yaml     # SQS FIFO queue definitions
│
├── storage/
│   └── schema/             # Database schema/models
│
└── terraform/              # Terraform/OpenTofu infrastructure code
    ├── modules/
    │   ├── alb/                 # Application Load Balancer module
    │   ├── ecs-fargate/         # ECS Fargate service module
    │   ├── messaging/           # SNS/SQS module
    │   ├── lambda/              # Lambda functions module
    │   └── storage/             # DynamoDB module
    ├── environments/
    │   ├── dev/
    │   ├── staging/
    │   └── prod/
    ├── data.tf                  # Data sources (existing VPC, Route53)
    ├── main.tf                  # Root module
    ├── variables.tf             # Input variables
    ├── outputs.tf               # Output values
    └── versions.tf              # Provider versions
```

### Event Flow

1. **GitHub Event Trigger**
   - Events: `pull_request`, `push`, `workflow_run`, `workflow_dispatch`
   - Webhook sent to Probot app (ECS Fargate)

2. **Probot Proxy Layer** (Minimal Logic)
   - Validate webhook signature
   - Extract event metadata (repo, org, workflow path)
   - Publish to SNS topic
   - Return 200 OK to GitHub

3. **SNS → SQS FIFO**
   - SNS fans out to multiple SQS queues if needed
   - FIFO ensures ordered processing per workflow
   - Message deduplication via message group ID

4. **Lambda Event Processors**
   - **Workflow Analyzer Lambda**:
     - Fetch workflow file from GitHub
     - Parse YAML
     - Extract dependencies (actions, runners, containers)
     - Analyze version pinning
     - Publish results to next queue or data store
   
   - **Deduplicator Lambda** (Future):
     - Check if workflow already processed
     - Compare checksums/hashes
     - Skip if no changes detected
   
   - **Data Writer Lambda**:
     - Store dependency data
     - Update aggregate statistics
     - Trigger notifications if needed

5. **Data Storage** (TBD)
   - Store raw workflow dependency data
   - Store aggregated metrics
   - Enable querying by repo, org, time range

6. **Data Presentation** (Future)
   - GitHub App dashboard
   - PR comments with dependency diff
   - AWS native dashboard (QuickSight, CloudWatch)
   - Export to external tools

---

## 🎯 MVP Feature Set

### Event Processing Pipeline
- ✅ GitHub App receives webhook events (push, pull_request, workflow_run)
- ✅ Probot server validates and proxies events to SNS
- ✅ SQS FIFO queue receives events in order
- ✅ Lambda processor fetches workflow files from GitHub
- ✅ Extract all `uses:` statements (actions)
- ✅ Extract runner images (`runs-on`)
- ✅ Identify version pinning strategy (SHA, tag, branch)
- ✅ Store dependency data in persistent storage
- ✅ Basic error handling and retry logic

### Supply Chain Analysis
- ✅ Detect SHA pinning (40 character hex)
- ✅ Detect semantic version tags
- ✅ Detect branch references
- ✅ Flag unpinned versions as security risks
- ✅ Identify unique vs duplicate dependencies
- ✅ Track changes over time (workflow updates)

### Infrastructure
- ✅ Probot app deployed to ECS Fargate
- ✅ SNS topic for GitHub events
- ✅ SQS FIFO queue for ordered processing
- ✅ Lambda function for workflow analysis
- ✅ Data storage solution (DynamoDB or RDS)
- ✅ CloudWatch logging and monitoring
- ✅ Infrastructure as Code (CDK or Terraform)

### Known Unknowns (To Address Later)
- ❓ **Data Storage**: DynamoDB vs RDS vs S3+Athena vs combination
- ❓ **Idempotency**: Deduplication strategy (checksums, timestamps, event IDs)
- ❓ **Data Presentation**: GitHub dashboard, PR comments, AWS QuickSight, or custom UI
- ❓ **Scaling**: Lambda concurrency limits, SQS throughput requirements
- ❓ **Multi-tenancy**: Single vs multi-org support, data isolation

---

## 📋 Development Iterations

### Iteration 1: Research & Planning ✅
- [x] Define problem statement
- [x] Identify target user needs
- [x] Choose architecture (event-driven GitHub App)
- [x] Create iteration plan

### Iteration 2: Local Development Environment
**Goal**: Set up development environment for Probot and Lambda development

**Tasks**:
1. Initialize Probot app project
   - [ ] Use `create-probot-app` or manual setup
   - [ ] Configure TypeScript
   - [ ] Set up local development with smee.io (webhook proxy)
   - [ ] Create `.env.template` for local configuration

2. Initialize Lambda function project
   - [ ] Create Python or Node.js project structure
   - [ ] Set up local testing with SAM Local or LocalStack
   - [ ] Configure Python dependencies (PyYAML) or Node.js (js-yaml)

3. Create shared models/types
   - [ ] Define event payload types
   - [ ] Define workflow dependency models
   - [ ] Share types between Probot and Lambda (if both TypeScript)

4. Set up development tools
   - [ ] ESLint/Prettier for TypeScript
   - [ ] pytest/ruff for Python
   - [ ] Pre-commit hooks
   - [ ] Docker for local testing

**Test Cases**:
- [ ] Probot app starts locally
- [ ] Can receive test webhooks via smee.io
- [ ] Lambda can be invoked locally

**Success Criteria**:
- [ ] Can run Probot app locally and receive GitHub webhooks
- [ ] Can invoke Lambda functions locally
- [ ] Dependencies install cleanly
- [ ] TypeScript/Python type checking works

### Iteration 3: GitHub App Setup
**Goal**: Create and configure GitHub App with necessary permissions

**Tasks**:
1. Create GitHub App
   - [ ] Register app in GitHub
   - [ ] Configure webhook URL (will update with ECS endpoint later)
   - [ ] Set webhook secret
   - [ ] Download private key for authentication

2. Configure permissions
   - [ ] Repository permissions:
     - [ ] Contents: Read (to fetch workflow files)
     - [ ] Metadata: Read
     - [ ] Workflows: Read
   - [ ] Subscribe to events:
     - [ ] `push` (to `.github/workflows/`)
     - [ ] `pull_request`
     - [ ] `workflow_run` (optional, for run-time analysis)

3. Implement GitHub App authentication in Probot
   - [ ] Use private key for JWT authentication
   - [ ] Install app on test repository
   - [ ] Verify webhook delivery

**Test Cases**:
- [ ] App can authenticate with GitHub
- [ ] Webhooks are received for push events
- [ ] Can fetch workflow files via GitHub API

**Success Criteria**:
- [ ] GitHub App is registered and installed
- [ ] Probot app receives webhook events
- [ ] Can authenticate and call GitHub API

### Iteration 4: Probot Proxy Implementation
**Goal**: Build minimal Probot app that validates and forwards events to SNS

**Tasks**:
1. Implement webhook validation
   - [ ] Verify webhook signature from GitHub
   - [ ] Extract relevant event metadata
   - [ ] Filter for workflow-related events only

2. Create SNS publisher module
   - [ ] Configure AWS SDK
   - [ ] Format messages for SNS
   - [ ] Add error handling and retry logic
   - [ ] Log events for debugging

3. Implement event handlers
   - [ ] `push` events (check if `.github/workflows/**` changed)
   - [ ] `pull_request` events
   - [ ] Extract: repo, org, workflow path, commit SHA, event type

4. Add health check endpoint
   - [ ] `/health` or `/ping` for load balancer
   - [ ] Return app status and version

**Test Cases**:
- [ ] Webhook signature validation (valid and invalid)
- [ ] SNS publishing (success and failure scenarios)
- [ ] Event filtering (workflow vs non-workflow changes)
- [ ] Health check endpoint returns 200

**Success Criteria**:
- [ ] Probot validates GitHub webhooks
- [ ] Events are published to SNS topic
- [ ] Non-workflow events are filtered out
- [ ] Errors are logged but don't crash app

### Iteration 5: AWS Infrastructure (Messaging)
**Goal**: Set up SNS and SQS FIFO for event processing

**Decision Point**: Choose between Terraform vs OpenTofu
- **Terraform**: Industry standard, large community, HashiCorp support
- **OpenTofu**: Open-source fork, community-driven, license concerns addressed
- Evaluate based on: licensing, community support, feature parity, team familiarity

**Tasks**:
1. Set up Terraform/OpenTofu project structure
   - [ ] Initialize backend (S3 + DynamoDB for state locking)
   - [ ] Configure provider versions
   - [ ] Create module structure
   - [ ] Set up remote state

2. Create data sources for existing resources
   - [ ] Reference existing VPC by ID or tags
   - [ ] Reference existing Route53 hosted zone by domain
   - [ ] Query available subnets (public/private)

3. Create SNS topic for GitHub events
   - [ ] Topic name: `github-workflow-events`
   - [ ] Enable encryption (KMS)
   - [ ] Configure dead-letter queue
   - [ ] Add tags for resource management

4. Create SQS FIFO queue
   - [ ] Queue name: `workflow-analysis.fifo`
   - [ ] Content-based deduplication enabled
   - [ ] Message retention: 4 days
   - [ ] Visibility timeout: 5 minutes (for Lambda processing)
   - [ ] Configure dead-letter queue
   - [ ] Enable encryption

5. Subscribe SQS to SNS topic
   - [ ] Set up SNS → SQS subscription
   - [ ] Configure filter policy (if needed)
   - [ ] Add necessary queue policy for SNS

6. Set up IAM roles and policies
   - [ ] Probot ECS task role: Publish to SNS
   - [ ] Lambda execution role: Poll SQS, read workflow files from GitHub
   - [ ] Principle of least privilege
   - [ ] Use managed policies where appropriate

7. Create reusable modules
   - [ ] Messaging module (SNS/SQS)
   - [ ] Document module inputs/outputs
   - [ ] Add examples in module README

**Test Cases**:
- [ ] Can publish message to SNS manually
- [ ] SQS receives messages from SNS
- [ ] Messages remain in queue until deleted
- [ ] DLQ receives failed messages

**Success Criteria**:
- [ ] SNS and SQS FIFO are deployed
- [ ] Messages flow from SNS → SQS
- [ ] IAM permissions are correctly configured
- [ ] Infrastructure is defined in code

### Iteration 6: Workflow Analyzer Lambda
**Goal**: Create Lambda function to parse workflows and extract dependencies

**Tasks**:
1. Implement SQS event handler
   - [ ] Parse SQS messages
   - [ ] Extract GitHub event details
   - [ ] Handle batch processing

2. Fetch workflow file from GitHub
   - [ ] Use GitHub API with app credentials
   - [ ] Handle file not found errors
   - [ ] Support both default and PR branches

3. Parse YAML workflow file
   - [ ] Use PyYAML or js-yaml
   - [ ] Handle malformed YAML gracefully
   - [ ] Extract jobs and steps

4. Extract dependencies
   - [ ] Parse `uses:` statements (actions)
   - [ ] Extract `runs-on:` (runner images)
   - [ ] Extract Docker container references
   - [ ] Parse version (SHA, tag, branch)

5. Analyze version pinning
   - [ ] Detect SHA pins (40 char hex)
   - [ ] Detect semver tags
   - [ ] Flag unpinned versions

6. Structure output data
   - [ ] Create JSON structure for storage
   - [ ] Include metadata: repo, commit, timestamp
   - [ ] Include dependency list with analysis

**Test Cases**:
- [ ] Parse valid workflow file (use `examples/main.yml`)
- [ ] Handle invalid YAML
- [ ] Handle missing workflow file
- [ ] Correctly identify all dependency types
- [ ] Correctly classify version types

**Success Criteria**:
- [ ] Lambda processes SQS messages
- [ ] Fetches workflow files from GitHub
- [ ] Extracts all dependencies correctly
- [ ] Returns structured JSON output
- [ ] Handles errors gracefully

### Iteration 7: Data Storage Layer
**Goal**: Decide on and implement data persistence

**Decision Points**:
- **DynamoDB**: Fast, serverless, good for key-value access
- **RDS (PostgreSQL)**: Relational, complex queries, ACID guarantees
- **S3 + Athena**: Cost-effective, good for analytics, batch queries
- **Hybrid**: DynamoDB for real-time + S3 for historical analysis

**Recommended Start**: DynamoDB (simpler for MVP)

**Tasks**:
1. Design data model
   - [ ] Table 1: `WorkflowDependencies`
     - [ ] PK: `repo#workflow_path`
     - [ ] SK: `commit_sha#timestamp`
     - [ ] Attributes: dependencies[], runners[], pinning_status, etc.
   
   - [ ] Table 2: `DependencyIndex` (GSI)
     - [ ] PK: `action_name` (e.g., `actions/checkout`)
     - [ ] SK: `repo#workflow_path`
     - [ ] For querying "who uses this action?"

2. Implement data writer Lambda (or extend analyzer)
   - [ ] Write to DynamoDB
   - [ ] Handle duplicates (idempotency)
   - [ ] Update GSI indexes

3. Implement deduplication logic
   - [ ] Calculate workflow file checksum
   - [ ] Store checksum in DynamoDB
   - [ ] Skip processing if checksum matches

4. Add error handling
   - [ ] Retry failed writes
   - [ ] Log errors to CloudWatch
   - [ ] Send to DLQ if max retries exceeded

**Test Cases**:
- [ ] Write new workflow analysis
- [ ] Update existing workflow (new commit)
- [ ] Duplicate event (same checksum)
- [ ] Failed writes are retried

**Success Criteria**:
- [ ] Data is persisted to chosen storage
- [ ] Deduplication prevents duplicate work
- [ ] Can query data by repo and workflow
- [ ] Idempotent processing (same event = same result)

### Iteration 8: Probot ECS Deployment
**Goal**: Deploy Probot app to ECS Fargate

**Tasks**:
1. Create Dockerfile for Probot app
   - [ ] Multi-stage build for optimization
   - [ ] Include Node.js runtime
   - [ ] Copy app code and dependencies
   - [ ] Expose port (3000)

2. Build and push Docker image
   - [ ] Create ECR repository
   - [ ] Build image locally
   - [ ] Push to ECR
   - [ ] Tag with version

3. Reference existing VPC and networking resources
   - [ ] Data source: Query existing VPC by ID or tags
   - [ ] Data source: Query public subnets (for ALB)
   - [ ] Data source: Query private subnets (for ECS)
   - [ ] Verify NAT Gateway exists for private subnet internet access

4. Create security groups
   - [ ] ALB security group:
     - [ ] Ingress: Allow 443 (HTTPS) from 0.0.0.0/0
     - [ ] Ingress: Allow 80 (HTTP) from 0.0.0.0/0
     - [ ] Egress: Allow traffic to ECS security group
   - [ ] ECS security group:
     - [ ] Ingress: Allow traffic from ALB security group only
     - [ ] Egress: Allow HTTPS to internet (for GitHub API calls)

5. Request SSL certificate in ACM
   - [ ] Request certificate for domain (e.g., `gha-webhook.yourdomain.com`)
   - [ ] Use DNS validation
   - [ ] Terraform/OpenTofu will output DNS validation records
   - [ ] Manually add validation records to Route53 (or automate)
   - [ ] Wait for certificate validation

6. Create Application Load Balancer
   - [ ] Deploy ALB in existing public subnets (across 2+ AZs)
   - [ ] HTTPS listener (port 443) with SSL certificate from ACM
   - [ ] HTTP listener (port 80) redirect to HTTPS
   - [ ] Target group for ECS Fargate service:
     - [ ] Protocol: HTTP, Port: 3000
     - [ ] Target type: IP (for Fargate)
     - [ ] Health check: `/health` or `/ping`
     - [ ] Deregistration delay: 30 seconds
   - [ ] Enable access logs (S3 bucket)

7. Configure Route53 record set
   - [ ] Data source: Query existing Route53 hosted zone by domain
   - [ ] Create A record (e.g., `gha-webhook.yourdomain.com`)
   - [ ] Type: Alias record pointing to ALB
   - [ ] Alias target: ALB DNS name
   - [ ] Routing policy: Simple
   - [ ] Verify DNS propagation

8. Create ECS resources
   - [ ] ECS Cluster (Fargate)
   - [ ] Task definition (CPU, memory, environment variables)
   - [ ] Service definition in private subnets
     - [ ] Desired count: 2 (for high availability)
     - [ ] Auto-scaling based on CPU/memory
     - [ ] Assign to private subnets
     - [ ] Register with ALB target group
   - [ ] Service discovery (optional, for internal DNS)

9. Configure secrets
   - [ ] Store GitHub App private key in AWS Secrets Manager
   - [ ] Store webhook secret in Secrets Manager
   - [ ] Reference secrets in task definition
   - [ ] Grant ECS task execution role access to secrets

10. Update GitHub App webhook URL
    - [ ] Point to custom domain (e.g., `https://gha-webhook.yourdomain.com/webhooks`)
    - [ ] Verify webhook delivery
    - [ ] Test with ping event from GitHub

11. Set up auto-scaling
    - [ ] Scale based on CPU utilization (> 70%) or request count
    - [ ] Min: 2 (for high availability), Max: 5 (for MVP)
    - [ ] Target tracking scaling policy

**Test Cases**:
- [ ] Docker image builds successfully
- [ ] Container runs locally
- [ ] Container runs in ECS (private subnets)
- [ ] Health check endpoint responds (ALB → ECS)
- [ ] Webhooks are received via custom domain
- [ ] HTTPS connection is secure (valid SSL)
- [ ] DNS resolves to ALB
- [ ] Tasks can reach internet via NAT Gateway
- [ ] Security groups properly restrict access

**Success Criteria**:
- [ ] Probot app is deployed to ECS Fargate in private subnets
- [ ] Accessible via custom domain over HTTPS (Route53 → ALB → ECS)
- [ ] Receives GitHub webhooks reliably
- [ ] Auto-scales under load (min 2, max 5 tasks)
- [ ] Secrets are managed securely
- [ ] Network architecture follows AWS best practices

### Iteration 9: End-to-End Testing
**Goal**: Test complete flow from GitHub event to data storage

**Tasks**:
1. Create test repository with workflows
   - [ ] Include various workflow patterns
   - [ ] Different action versions (SHA, tag, branch)
   - [ ] Multiple jobs and steps

2. Trigger events and verify flow
   - [ ] Push commit to test repo
   - [ ] Verify webhook received by Probot
   - [ ] Verify message in SNS/SQS
   - [ ] Verify Lambda processes message
   - [ ] Verify data written to storage

3. Test error scenarios
   - [ ] Invalid YAML in workflow
   - [ ] Missing workflow file
   - [ ] Network failures
   - [ ] DLQ message handling

4. Performance testing
   - [ ] Measure end-to-end latency
   - [ ] Test concurrent events
   - [ ] Monitor Lambda cold starts
   - [ ] Check SQS queue depth under load

5. Set up monitoring and alerts
   - [ ] CloudWatch dashboards
   - [ ] Alarms for errors, latency, DLQ messages
   - [ ] X-Ray tracing for debugging

**Test Cases**:
- [ ] Happy path (valid workflow)
- [ ] Invalid YAML
- [ ] Large workflow files
- [ ] High event volume
- [ ] Network errors

**Success Criteria**:
- [ ] Complete flow works end-to-end
- [ ] Errors are handled gracefully
- [ ] Performance meets requirements (< 30s end-to-end)
- [ ] Monitoring shows system health

### Iteration 10: Documentation & Deployment Automation
**Goal**: Document system and automate deployments

**Tasks**:
1. Update README.md
   - [ ] Architecture diagram
   - [ ] Setup instructions
   - [ ] Deployment guide
   - [ ] Configuration options

2. Create infrastructure deployment guide
   - [ ] Terraform/OpenTofu commands
   - [ ] Required AWS permissions
   - [ ] Environment variables
   - [ ] GitHub App setup steps

3. Add code documentation
   - [ ] Document Probot webhook handlers
   - [ ] Document Lambda functions
   - [ ] Document data models
   - [ ] Add inline comments for complex logic

4. Create CI/CD pipeline
   - [ ] GitHub Actions workflow for:
     - [ ] Linting and type checking
     - [ ] Running tests
     - [ ] Building Docker images
     - [ ] Deploying to AWS (dev/prod)
   - [ ] Automated testing before deployment

5. Create runbook
   - [ ] Common issues and solutions
   - [ ] How to monitor system
   - [ ] How to troubleshoot errors
   - [ ] How to scale resources

**Success Criteria**:
- [ ] Documentation is complete and clear
- [ ] New developers can set up locally
- [ ] Deployments are automated
- [ ] Runbook covers common scenarios

---

## 🚀 Future Iterations (Post-MVP)

### Data Presentation Layer
**Options to Explore**:
1. **GitHub App Dashboard**
   - Hosted UI within GitHub
   - Show dependency trends over time
   - Compare across repositories

2. **PR Comments**
   - Auto-comment when dependencies change
   - Show diff of added/removed actions
   - Flag new unpinned versions

3. **AWS Native Dashboard**
   - AWS QuickSight for analytics
   - CloudWatch dashboard for metrics
   - S3 + Athena for ad-hoc queries

4. **Custom Web UI**
   - React/Next.js dashboard
   - Real-time updates via WebSockets
   - Export reports (PDF, CSV)

5. **Slack/Teams Integration**
   - Notify on new unpinned dependencies
   - Weekly summary reports
   - Alert on vulnerable actions

### Multi-Workflow Support
- Scan entire `.github/workflows/` directory per repo
- Aggregate dependencies across all workflows
- Identify duplicate dependencies across workflows
- Repo-level dependency summary

### Multi-Repository Support
- Accept GitHub organization name
- Scan all repositories in org
- Generate org-wide dependency report
- Compare dependencies across teams

### Security Intelligence
- Integrate with GitHub Advisory Database
- Check for known vulnerabilities in actions
- Suggest version updates
- Security scoring per repo/org

### Advanced Dependency Analysis
- Detect transitive dependencies (composite actions)
- Analyze Docker images used in workflows
- Track runner image versions
- Detect deprecated actions

### Compliance & Governance
- Define allowed/denied action lists
- Enforce SHA pinning policies
- Generate compliance reports
- Alert on policy violations

### Historical Analysis
- Track dependency changes over time
- Identify when vulnerabilities were introduced
- Show adoption rate of new action versions
- Generate trend reports

### Performance Optimizations
- Cache workflow files (avoid re-fetching)
- Batch process multiple events
- Parallel Lambda execution
- Optimize DynamoDB queries

### Developer Experience
- CLI tool for local testing (optional)
- GitHub Action to run in CI
- VS Code extension for in-editor visibility
- Pre-commit hooks for policy enforcement

---

## 🎯 Success Metrics

### MVP Success (Iterations 1-10)
- ✅ Terraform vs OpenTofu decision made and documented
- ✅ GitHub App installed on 1+ test repositories
- ✅ Probot receives and processes webhook events via custom domain
- ✅ End-to-end latency < 30 seconds (event → storage)
- ✅ Lambda processes workflows without errors
- ✅ Data is stored and queryable
- ✅ System is idempotent (duplicate events handled)
- ✅ Infrastructure deployed via IaC (Terraform/OpenTofu)
- ✅ Infrastructure leverages existing VPC and Route53 zone
- ✅ CloudWatch monitoring configured

### Post-MVP Success
- 10+ repositories using the app
- 100+ workflows analyzed
- 1000+ dependencies tracked
- < 1% error rate in processing
- Data presentation layer launched
- Positive feedback from 5+ developers

### Production Readiness
- Multi-org support
- 99.9% uptime
- Security scanning integrated
- Compliance reports available
- Self-service onboarding

---

## 📝 Notes for GitHub Copilot Agent

### Architecture Decisions Rationale

**Why Probot as "Dumb Proxy"?**
- GitHub webhooks require quick 200 OK response (< 10s)
- Complex processing (fetching files, parsing YAML) takes longer
- Decoupling via messaging allows retry logic and error isolation
- ECS Fargate provides persistent service for webhook receiver

**Why SNS → SQS FIFO?**
- SNS allows fan-out to multiple consumers (future extensibility)
- FIFO ensures ordered processing per workflow (prevents race conditions)
- Content-based deduplication prevents duplicate processing
- Dead-letter queues for failed messages

**Why Lambda for Processing?**
- Pay-per-invocation (cost-effective for sporadic events)
- Auto-scales to match event volume
- Stateless design simplifies deployment
- Can switch to ECS/Fargate if Lambda limits become issue

**Data Storage Considerations**:
- **DynamoDB**: Best for MVP - fast, serverless, simple key-value access
  - Good for: Real-time queries, individual workflow lookups
  - Limit: Complex analytics queries
  
- **RDS (PostgreSQL)**: Consider if complex relational queries needed
  - Good for: Joins, aggregations, ACID transactions
  - Limit: More expensive, requires connection pooling
  
- **S3 + Athena**: Best for historical analytics
  - Good for: Large-scale queries, data lake, cost-effective storage
  - Limit: Higher latency, not for real-time

- **Recommendation**: Start with DynamoDB, add S3 archival later

### Code Style Preferences

**TypeScript (Probot)**
- Use strict mode
- Prefer interfaces over types for objects
- Use async/await over promises
- Handle errors with try/catch
- Use ESLint + Prettier

**Python (Lambda)**
- Use type hints everywhere
- Prefer dataclasses for models
- Use pathlib for file operations
- Handle errors explicitly (no bare excepts)
- Use ruff for linting

**Infrastructure (Terraform/OpenTofu)**
- Use descriptive resource names with consistent naming convention
- Tag all resources (project, environment, owner, managed-by=terraform)
- Enable encryption by default (KMS for SNS/SQS, encryption at rest for storage)
- Use AWS Secrets Manager for secrets (reference in Terraform)
- Document all configuration decisions in comments and README
- Use data sources for existing resources (VPC, Route53)
- Pin provider versions for reproducibility
- Use remote state with locking (S3 + DynamoDB)
- Structure: modules for reusability, environments for env-specific config

### Testing Approach

**Probot Testing**
- Use `probot/testing` for webhook testing
- Mock GitHub API calls
- Test webhook signature validation
- Test SNS publishing (use AWS SDK mock)

**Lambda Testing**
- Use pytest or Jest
- Mock SQS events
- Mock GitHub API calls
- Test YAML parsing edge cases
- Test idempotency logic

**Integration Testing**
- Use LocalStack for AWS services
- End-to-end test with real GitHub webhooks (test repo)
- Test error scenarios (network failures, timeouts)

### Security Best Practices

1. **GitHub App Authentication**
   - Store private key in AWS Secrets Manager
   - Rotate keys periodically
   - Use short-lived JWT tokens

2. **Webhook Validation**
   - Always validate signature before processing
   - Use constant-time comparison for secrets
   - Log failed validations

3. **AWS IAM**
   - Principle of least privilege
   - Separate roles for dev/prod
   - No hardcoded credentials

4. **Data Storage**
   - Encrypt at rest (use AWS KMS)
   - Encrypt in transit (use TLS)
   - Sanitize user inputs

### Monitoring & Observability

**CloudWatch Metrics to Track**:
- Probot: Request count, latency, errors
- Lambda: Invocations, duration, errors, throttles
- SQS: Messages sent, received, deleted, age
- DynamoDB: Read/write capacity, throttles

**CloudWatch Alarms**:
- Probot 5xx errors > 5 in 5 minutes
- Lambda errors > 10 in 5 minutes
- SQS DLQ message count > 0
- Lambda duration > 4 minutes (near timeout)

**X-Ray Tracing**:
- Enable on Lambda functions
- Trace GitHub API calls
- Trace DynamoDB operations
- Identify bottlenecks

### Idempotency Strategy

**Options**:
1. **Content-based deduplication (Recommended for MVP)**
   - Calculate SHA-256 of workflow file content
   - Store hash in DynamoDB
   - Skip processing if hash unchanged
   - Pros: Simple, reliable
   - Cons: Doesn't detect if same content pushed twice

2. **Event-based deduplication**
   - Use GitHub event delivery ID
   - Store processed event IDs in DynamoDB (TTL 7 days)
   - Pros: Detects duplicate webhooks
   - Cons: More storage

3. **Hybrid approach**
   - Use event ID for webhook deduplication (Probot layer)
   - Use content hash for workflow deduplication (Lambda layer)
   - Best of both worlds

### Scaling Considerations

**Current MVP Assumptions**:
- < 100 events/day per repository
- < 10 workflows per repository
- < 100 repositories total
- < 10 KB average workflow file size

**Scaling Triggers** (when to optimize):
- > 1000 events/day: Consider batch processing
- > 100 repositories: Add multi-tenancy isolation
- Lambda cold starts > 2s: Consider provisioned concurrency
- DynamoDB throttling: Adjust capacity or add caching

**Cost Optimization**:
- Use Lambda ARM64 for 20% cost savings
- Set appropriate Lambda memory (1024 MB good start)
- Use S3 for archival (cheaper than DynamoDB)
- Set DynamoDB TTL for old data

### File Naming Conventions

**Probot Project**:
- `src/index.ts` - Entry point
- `src/webhooks/push.ts` - Push event handler
- `src/services/sns.ts` - SNS publishing service
- `src/types/events.ts` - Event type definitions
- `test/webhooks/push.test.ts` - Tests

**Infrastructure**:
- `terraform/data.tf` - Data sources for existing VPC, subnets, Route53 zone
- `terraform/modules/alb/` - Application Load Balancer module
- `terraform/modules/ecs-fargate/` - ECS Fargate service module  
- `terraform/modules/messaging/` - SNS/SQS module
- `terraform/modules/lambda/` - Lambda functions module
- `terraform/modules/storage/` - DynamoDB module
- `terraform/environments/dev/` - Dev environment configuration
- `terraform/environments/prod/` - Prod environment configuration

### Git Workflow

- Create feature branches for each iteration
- Use conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
- PR template with checklist (tests, docs, IaC)
- Protect main branch (require reviews)
- Tag releases with semantic versioning
- Separate branches for dev/staging/prod infrastructure

### Environment Management

**Environments**:
- `local` - Developer machine (smee.io, LocalStack)
- `dev` - AWS dev account (test workflows)
- `staging` - AWS staging account (pre-production)
- `prod` - AWS prod account (customer-facing)

**Configuration**:
- Use environment variables for config
- Never commit secrets to git
- Use AWS Secrets Manager for sensitive data
- Document all required env vars in README
