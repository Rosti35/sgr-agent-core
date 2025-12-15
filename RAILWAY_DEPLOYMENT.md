# Deploying SGR Deep Research on Railway

This guide explains how to deploy SGR Deep Research on [Railway](https://railway.app).

## Architecture

The application consists of two services:

1. **Backend** - Python FastAPI server (`sgr_deep_research`)
2. **Frontend** - Vue.js SPA served by Nginx (`sgr-deep-research-frontend`)

## Quick Start

### Option 1: Deploy via Railway Dashboard (Recommended)

1. **Create a new Railway project**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure Backend Service**
   - Railway will auto-detect the root `Dockerfile`
   - Go to "Settings" → "Variables" and add:
   
   ```
   LLM_API_KEY=your-openai-api-key
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-4o
   TAVILY_API_KEY=your-tavily-api-key
   ```

3. **Add Frontend Service**
   - Click "New" → "Service" → "GitHub Repo"
   - Select the same repository
   - Go to "Settings" → "Build" and set:
     - **Root Directory**: `sgr-deep-research-frontend`
     - **Dockerfile Path**: `Dockerfile`
   - Add variable:
   
   ```
   VITE_API_BASE_URL=https://your-backend-service.railway.app
   ```

4. **Generate Domains**
   - For each service, go to "Settings" → "Networking"
   - Click "Generate Domain" to get a public URL

### Option 2: Deploy via Railway CLI

1. **Install Railway CLI**

   ```bash
   npm install -g @railway/cli
   # or
   brew install railway
   ```

2. **Login and initialize**

   ```bash
   railway login
   railway init
   ```

3. **Deploy Backend**

   ```bash
   # From project root
   railway up
   
   # Set environment variables
   railway variables set LLM_API_KEY=your-key
   railway variables set LLM_BASE_URL=https://api.openai.com/v1
   railway variables set LLM_MODEL=gpt-4o
   railway variables set TAVILY_API_KEY=your-tavily-key
   ```

4. **Deploy Frontend**

   ```bash
   cd sgr-deep-research-frontend
   railway service create frontend
   railway up
   
   # Set the API URL to your backend
   railway variables set VITE_API_BASE_URL=https://your-backend.railway.app
   ```

## Environment Variables

### Backend Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_API_KEY` | Yes | - | OpenAI/OpenRouter API key |
| `LLM_BASE_URL` | No | `https://api.openai.com/v1` | LLM API base URL |
| `LLM_MODEL` | No | `gpt-4o` | Model name |
| `LLM_MAX_TOKENS` | No | `8000` | Max output tokens |
| `LLM_TEMPERATURE` | No | `0.4` | Temperature (0.0-1.0) |
| `TAVILY_API_KEY` | Yes* | - | Tavily search API key |
| `MAX_ITERATIONS` | No | `10` | Max agent iterations |
| `PORT` | No | `8010` | Server port (Railway sets this) |

*Required for web search features

### Frontend Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | Yes | - | Backend API URL |
| `VITE_APP_ENV` | No | `production` | Environment name |

## Using Railway's Internal Networking

For service-to-service communication, use Railway's internal networking:

1. Get your backend's internal URL from Railway dashboard (e.g., `backend.railway.internal`)
2. Set frontend's `VITE_API_BASE_URL` to the **public** backend URL (since it's called from browser)

## Health Checks

The backend exposes a `/health` endpoint that Railway uses for health checks. This is configured in `railway.toml`.

## Persistent Storage (Optional)

If you need to persist logs and reports:

1. Go to your backend service
2. Click "New" → "Volume"
3. Set mount path to `/app/logs` or `/app/reports`

## Troubleshooting

### Backend not starting

Check the logs in Railway dashboard. Common issues:

- Missing `LLM_API_KEY` - Set the environment variable
- Config file not generated - Check if `scripts/generate_config.py` ran successfully

### Frontend can't reach backend

- Ensure `VITE_API_BASE_URL` is set to the correct backend URL
- Make sure the backend has a public domain generated
- Check CORS settings if requests are blocked

### Build failures

- Ensure `uv.lock` is committed to your repository
- Check if all required files are present

## Costs

Railway offers:
- **Free tier**: $5 credit/month
- **Hobby tier**: $5/month with more resources
- **Pro tier**: Usage-based pricing

Monitor your usage in the Railway dashboard to avoid unexpected charges.

## Support

- [Railway Documentation](https://docs.railway.app)
- [SGR Deep Research Issues](https://github.com/vakovalskii/sgr-deep-research/issues)




