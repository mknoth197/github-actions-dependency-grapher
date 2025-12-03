# Workflow Analyzer Lambda

This Lambda function analyzes GitHub Actions workflow files to extract dependencies and metadata.

## Features

- Parses YAML workflow files
- Extracts action dependencies (with version/pinning analysis)
- Identifies runner images
- Detects container dependencies
- Classifies pinning strategies (SHA, tag, branch, unpinned)

## Local Development

### Prerequisites

- Python 3.12+
- pip

### Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_analyzer.py
```

### Linting and Type Checking

```bash
# Lint with ruff
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type check with mypy
mypy *.py
```

## Lambda Deployment

### Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token or App installation token (required)

### Package for Deployment

```bash
# Install dependencies to a package directory
pip install -r requirements.txt -t package/

# Copy source files
cp *.py package/
cp -r ../shared package/

# Create deployment package
cd package
zip -r ../lambda-function.zip .
cd ..
```

### Test Locally with SAM

```bash
# Install AWS SAM CLI first: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# Create a sample event
cat > event.json << 'EOF'
{
  "Records": [
    {
      "body": "{\"Message\": \"{\\\"repository\\\": {\\\"owner\\\": \\\"example\\\", \\\"name\\\": \\\"repo\\\", \\\"fullName\\\": \\\"example/repo\\\"}, \\\"workflow\\\": {\\\"path\\\": \\\".github/workflows/ci.yml\\\", \\\"ref\\\": \\\"refs/heads/main\\\"}, \\\"commit\\\": {\\\"sha\\\": \\\"abc123\\\", \\\"message\\\": \\\"test\\\", \\\"author\\\": \\\"user\\\"}, \\\"eventType\\\": \\\"push\\\", \\\"timestamp\\\": \\\"2024-01-01T00:00:00Z\\\"}\"}"
    }
  ]
}
EOF

# Invoke locally
sam local invoke WorkflowAnalyzerFunction --event event.json
```

## Architecture

### Input (SQS Event)

The function receives SQS messages containing GitHub workflow events. Messages are published by the Probot app via SNS and queued in SQS FIFO.

Example message structure:
```json
{
  "repository": {
    "owner": "example",
    "name": "repo",
    "fullName": "example/repo"
  },
  "workflow": {
    "path": ".github/workflows/ci.yml",
    "ref": "refs/heads/main"
  },
  "commit": {
    "sha": "abc123",
    "message": "test commit",
    "author": "user"
  },
  "eventType": "push",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Output

The function analyzes the workflow and produces structured output with:
- Workflow metadata (name, jobs, steps count)
- List of dependencies (actions, runners, containers)
- Pinning strategy classification
- Analysis timestamp

### Dependencies Extracted

1. **Actions** (from `uses:` statements)
   - Name and version
   - Pinning strategy: SHA (40-char hex), tag (semver), branch (main/master/etc), or unpinned

2. **Runners** (from `runs-on:`)
   - Runner image name (e.g., ubuntu-latest, windows-2022)

3. **Containers** (from `container:`)
   - Container image and tag
