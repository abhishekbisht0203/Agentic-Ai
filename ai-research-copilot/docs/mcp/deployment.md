# MCP Server Deployment Guide

## Overview

The MCP (Model Context Protocol) server provides tool execution capabilities for the AI Research Copilot. It runs as a separate microservice and exposes tools via JSON-RPC.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Frontend     │────▶│      Nginx      │────▶│   MCP Server    │
│   (Next.js)     │     │  (Reverse Proxy)│     │  (FastAPI)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │   Backend API   │
                        │   (FastAPI)     │
                        └─────────────────┘
```

## Available Tools

| Tool | Category | Auth Required | Description |
|------|----------|---------------|-------------|
| `calculator` | calculation | No | Safe math expression evaluator |
| `web_search` | search | No | Web search (stub) |
| `weather` | data | No | Weather lookup (stub) |
| `read_file` | filesystem | Yes | Read file contents |
| `write_file` | filesystem | Yes | Write file contents |
| `python_executor` | execution | Yes | Execute Python code |

## Deployment

### Using Docker Compose (Recommended)

1. **Configure environment variables** in `.env`:
   ```bash
   # MCP Server
   MCP_PORT=8100
   MCP_SECRET_KEY=<your-secret-key>
   MCP_RATE_LIMIT_ENABLED=true
   MCP_RATE_LIMIT_MAX_REQUESTS=100
   ```

2. **Start the MCP server**:
   ```bash
   docker-compose up -d mcp-server
   ```

3. **Verify the service**:
   ```bash
   curl http://localhost:8100/health
   ```

### Standalone Deployment

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   uvicorn app.mcp.server.main:app --host 0.0.0.0 --port 8100 --workers 4
   ```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | `8100` | Server port |
| `MCP_SECRET_KEY` | - | JWT secret key |
| `MCP_RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `MCP_RATE_LIMIT_MAX_REQUESTS` | `100` | Max requests per window |
| `MCP_RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window |
| `MCP_TIMEOUT` | `30` | Default tool timeout |
| `MCP_MAX_RETRIES` | `3` | Max retry attempts |

### Configuration File

The MCP server configuration is stored in `config/mcp/mcp.json`. This file defines:

- Server settings (host, port, CORS)
- Tool configurations (enabled, timeouts, auth requirements)
- Security settings (authentication, authorization, rate limiting)
- Monitoring settings (metrics, logging, tracing)

## API Endpoints

### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 123.45,
  "tools_registered": 6
}
```

### List Tools
```bash
GET /tools
```

Response:
```json
{
  "tools": [
    {
      "name": "calculator",
      "description": "Evaluate a mathematical expression",
      "parameters": {...},
      "category": "calculation",
      "requires_auth": false
    }
  ]
}
```

### Execute Tool (JSON-RPC)
```bash
POST /
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "calculator",
    "arguments": {
      "expression": "2 + 2"
    }
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "4"
      }
    ],
    "isError": false
  }
}
```

## Security

### Authentication

MCP tools that require authentication use JWT tokens. Include the token in the request:

```bash
POST /
Content-Type: application/json
Authorization: Bearer <jwt-token>

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "file_path": "/app/uploads/document.txt"
    }
  }
}
```

### Rate Limiting

Rate limiting is enabled by default. Limits are applied per IP address:

- Default: 100 requests per 60 seconds
- `python_executor`: 10 requests per 60 seconds
- `web_search`: 20 requests per 60 seconds

## Monitoring

### Metrics

Prometheus metrics are available at `/metrics` (internal network only).

### Logging

Logs are written to `/app/logs/mcp.log` in JSON format. Configure log level with `MCP_LOG_LEVEL`.

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure the MCP server is running and port 8100 is exposed.

2. **Authentication errors**: Verify JWT token is valid and not expired.

3. **Rate limit exceeded**: Wait for the rate limit window to reset or increase limits in configuration.

4. **Tool execution timeout**: Increase timeout in `config/mcp/mcp.json` or check tool implementation.

### Debug Mode

Enable debug logging:
```bash
MCP_LOG_LEVEL=debug docker-compose up mcp-server
```
