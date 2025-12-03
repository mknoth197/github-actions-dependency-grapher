# Probot App - GitHub Actions Dependency Grapher

This is the GitHub App component that receives webhook events from GitHub and publishes them to SNS for further processing.

## Architecture

The Probot app acts as a "dumb proxy" - it:
1. Receives GitHub webhook events (push, pull_request)
2. Validates webhook signatures
3. Filters for workflow-related changes (`.github/workflows/`)
4. Publishes events to AWS SNS for asynchronous processing
5. Returns 200 OK quickly to GitHub

## Local Development

### Prerequisites

- Node.js 18+ 
- npm
- GitHub App credentials (for testing)

### Setup

1. Install dependencies:
```bash
npm install
```

2. Copy the environment template:
```bash
cp .env.template .env
```

3. Configure your `.env` file with GitHub App credentials:
   - `APP_ID`: Your GitHub App ID
   - `WEBHOOK_SECRET`: Your webhook secret
   - `PRIVATE_KEY_PATH`: Path to your private key file

4. (Optional) For local webhook testing, use smee.io:
```bash
npm install -g smee-client
smee -u https://smee.io/your-unique-url -t http://localhost:3000/
```

### Development Commands

```bash
# Build TypeScript
npm run build

# Start the app (requires built files)
npm start

# Development mode with auto-reload
npm run dev

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run typecheck
```

### Testing Locally

1. Start the app:
```bash
npm run dev
```

2. The app will be available at `http://localhost:3000`

3. Health check endpoint: `http://localhost:3000/health`

4. Configure your GitHub App webhook URL to point to your smee.io URL or ngrok tunnel

## Docker

Build the Docker image:
```bash
docker build -t probot-app .
```

Run the container:
```bash
docker run -p 3000:3000 \
  -e APP_ID=your-app-id \
  -e WEBHOOK_SECRET=your-secret \
  -e PRIVATE_KEY_PATH=/secrets/private-key.pem \
  -v /path/to/private-key.pem:/secrets/private-key.pem \
  probot-app
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `APP_ID` | GitHub App ID | Yes |
| `WEBHOOK_SECRET` | GitHub webhook secret | Yes |
| `PRIVATE_KEY_PATH` | Path to GitHub App private key | Yes |
| `SNS_TOPIC_ARN` | AWS SNS topic ARN for publishing events | No (for local dev) |
| `AWS_REGION` | AWS region | No (default: us-east-1) |
| `LOG_LEVEL` | Logging level (debug, info, warn, error) | No (default: info) |
| `PORT` | Port to run the server | No (default: 3000) |
| `WEBHOOK_PROXY_URL` | smee.io URL for local development | No |

## Endpoints

- `GET /health` - Health check endpoint
- `GET /ping` - Simple ping endpoint
- `POST /` - GitHub webhook receiver (handled by Probot)

## Deployment

This app is designed to be deployed to AWS ECS Fargate. See the infrastructure documentation for deployment instructions.
