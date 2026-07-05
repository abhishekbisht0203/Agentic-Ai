# OAuth Authentication Setup Guide

This guide explains how to set up Google and GitHub OAuth authentication for the AI Research Copilot application.

## Table of Contents

1. [Google OAuth Setup](#google-oauth-setup)
2. [GitHub OAuth Setup](#github-oauth-setup)
3. [Environment Variables](#environment-variables)
4. [Local Development](#local-development)
5. [Production Deployment](#production-deployment)

---

## Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top
3. Click "New Project"
4. Enter a project name (e.g., "AI Research Copilot")
5. Click "Create"

### Step 2: Enable Google+ API

1. In the Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API" or "People API"
3. Click on it and click "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" user type
   - Fill in the app name and email addresses
   - Add scopes: `email`, `profile`, `openid`
   - Add test users if in testing mode
4. For application type, select "Web application"
5. Add authorized redirect URIs:

   **For local development:**
   ```
   http://localhost:8000/api/v1/auth/google/callback
   ```

   **For production:**
   ```
   https://your-backend.onrender.com/api/v1/auth/google/callback
   ```

6. Click "Create"
7. Copy the Client ID and Client Secret

---

## GitHub OAuth Setup

### Step 1: Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in the application details:
   - **Application name:** AI Research Copilot
   - **Homepage URL:**
     - Local: `http://localhost:3000`
     - Production: `https://your-domain.com`
   - **Authorization callback URL:**
     - Local: `http://localhost:8000/api/v1/auth/github/callback`
     - Production: `https://your-backend.onrender.com/api/v1/auth/github/callback`

4. Click "Register application"
5. Copy the Client ID
6. Click "Generate a new client secret"
7. Copy the Client Secret (it will only be shown once!)

---

## Environment Variables

Add the following to your `.env` file:

```env
# Frontend & Backend URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback
```

---

## Redirect URLs Summary

### Local Development

| Provider | Redirect URL |
|----------|--------------|
| Google | `http://localhost:8000/api/v1/auth/google/callback` |
| GitHub | `http://localhost:8000/api/v1/auth/github/callback` |
| Frontend Callback | `http://localhost:3000/auth/callback` |

### Production

| Provider | Redirect URL |
|----------|--------------|
| Google | `https://your-backend.onrender.com/api/v1/auth/google/callback` |
| GitHub | `https://your-backend.onrender.com/api/v1/auth/github/callback` |
| Frontend Callback | `https://your-domain.com/auth/callback` |

---

## Local Development

### 1. Run Database Migration

```bash
cd ai-research-copilot/backend
alembic upgrade head
```

### 2. Start Backend

```bash
cd ai-research-copilot/backend
uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend

```bash
cd ai-research-copilot/frontend
npm run dev
```

### 4. Test OAuth

1. Open `http://localhost:3000/login`
2. Click "Continue with Google" or "Continue with GitHub"
3. Complete the OAuth flow
4. You should be redirected to the dashboard

---

## Production Deployment

### Backend (Render)

1. Go to your Render dashboard
2. Select your backend service
3. Go to "Environment" tab
4. Add the following environment variables:

```env
FRONTEND_URL=https://your-domain.vercel.app
BACKEND_URL=https://your-backend.onrender.com
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### Frontend (Vercel)

1. Go to your Vercel dashboard
2. Select your frontend project
3. Go to "Settings" > "Environment Variables"
4. Add:

```env
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api/v1
```

### Update OAuth Provider Settings

1. **Google Cloud Console:**
   - Go to "APIs & Services" > "Credentials"
   - Update your OAuth client with production redirect URIs
   - Add production URL to "Authorized JavaScript origins"

2. **GitHub:**
   - Go to "Settings" > "Developer settings" > "OAuth Apps"
   - Update the callback URL to your production backend URL
   - Update the homepage URL to your production frontend URL

---

## Troubleshooting

### Common Issues

1. **"redirect_uri_mismatch" error**
   - Ensure the redirect URI in your OAuth provider settings exactly matches the one in your environment variables
   - Check for trailing slashes

2. **"invalid_client" error**
   - Verify your client ID and secret are correct
   - Ensure the credentials are for the correct environment (dev/prod)

3. **OAuth callback fails silently**
   - Check backend logs for errors
   - Verify CORS settings allow your frontend domain
   - Ensure `FRONTEND_URL` is correctly set

4. **User not being created**
   - Check database connection
   - Verify migration was run: `alembic upgrade head`
   - Check for unique constraint violations

### Debug Mode

Enable debug mode in `.env`:

```env
APP_DEBUG=true
LOG_LEVEL=debug
```

Check backend logs for detailed error messages.

---

## Security Notes

1. **Never commit secrets** to version control
2. **Use environment variables** for all sensitive configuration
3. **Enable HTTPS** in production
4. **Rotate secrets** periodically
5. **Use different OAuth apps** for development and production
6. **Validate state parameter** to prevent CSRF attacks (implemented in the service)

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/google/login` | GET | Initiate Google OAuth flow |
| `/api/v1/auth/google/callback` | GET | Handle Google OAuth callback |
| `/api/v1/auth/github/login` | GET | Initiate GitHub OAuth flow |
| `/api/v1/auth/github/callback` | GET | Handle GitHub OAuth callback |

---

## Database Schema Changes

The following columns were added to the `users` table:

- `google_id`: VARCHAR(255), UNIQUE, NULLABLE
- `github_id`: VARCHAR(255), UNIQUE, NULLABLE

These columns allow users to link multiple OAuth providers to a single account.

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend logs for error details
3. Open an issue on the project repository
