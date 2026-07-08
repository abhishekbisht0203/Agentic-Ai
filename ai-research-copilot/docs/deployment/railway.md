# Railway Deployment Guide

## Prerequisites

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

## Deploy Backend

### Option 1: Using Railway CLI

```bash
# Navigate to project directory
cd ai-research-copilot

# Initialize Railway project
railway init

# Link to your project
railway link

# Add environment variables
railway variables set APP_ENV=production
railway variables set LOG_LEVEL=info
railway variables set JWT_SECRET_KEY=$(openssl rand -hex 32)
railway variables set ENCRYPTION_KEY=$(openssl rand -hex 16)

# Deploy
railway up
```

### Option 2: Using GitHub Integration

1. Push code to GitHub
2. Go to [Railway Dashboard](https://railway.app/dashboard)
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Select your repository
6. Railway will auto-detect the Dockerfile and deploy

## Deploy MCP Server

### Option 1: Using Railway CLI

```bash
# Create a new service for MCP
railway service add mcp-server

# Set the Dockerfile
railway variables set RAILWAY_DOCKERFILE_PATH=docker/mcp/Dockerfile.railway

# Add environment variables
railway variables set MCP_PORT=8100
railway variables set MCP_SECRET_KEY=$(openssl rand -hex 32)
railway variables set MCP_RATE_LIMIT_ENABLED=true

# Deploy
railway up
```

### Option 2: Separate Project

```bash
# Create a new Railway project for MCP
railway init mcp-server

# Link and deploy
railway link
railway up
```

## Environment Variables

### Backend
| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment | `production` |
| `LOG_LEVEL` | Log level | `info` |
| `JWT_SECRET_KEY` | JWT secret | Auto-generated |
| `ENCRYPTION_KEY` | Encryption key | Auto-generated |
| `DATABASE_URL` | PostgreSQL URL | From Railway DB |
| `REDIS_URL` | Redis URL | From Railway Redis |

### MCP Server
| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_PORT` | Server port | `8100` |
| `MCP_SECRET_KEY` | MCP secret | Auto-generated |
| `MCP_RATE_LIMIT_ENABLED` | Rate limiting | `true` |
| `MCP_RATE_LIMIT_MAX_REQUESTS` | Max requests | `100` |
| `MCP_TIMEOUT` | Tool timeout | `30` |

## Services to Add

```bash
# PostgreSQL Database
railway add postgresql

# Redis Cache
railway add redis
```

## Verify Deployment

```bash
# Check service status
railway status

# View logs
railway logs

# Open in browser
railway open
```

## Domain Configuration

Railway provides a free `.up.railway.app` domain. To add a custom domain:

1. Go to Railway Dashboard
2. Select your service
3. Go to Settings → Networking
4. Add custom domain

## Troubleshooting

### Build Fails
- Check Dockerfile path in `railway.json`
- Ensure all dependencies are in `requirements.txt`

### Service Won't Start
- Check logs: `railway logs`
- Verify environment variables: `railway variables`

### Health Check Fails
- Ensure `/health` endpoint exists
- Check if port matches `PORT` environment variable
