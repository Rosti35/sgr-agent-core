# SGR Deep Research Pipeline for Open WebUI

This pipeline connects Open WebUI to the SGR Deep Research Agent API, enabling streaming research capabilities.

## Installation

1. **Start the SGR Deep Research API server:**

```bash
cd /path/to/sgr-agent-core
python -m sgr_deep_research --port 8010
```

2. **Add the pipeline to Open WebUI:**

   - Go to Open WebUI Admin Panel → Settings → Pipelines
   - Click "Add Pipeline" and upload `sgr_deep_research_pipeline.py`
   - Or place the file in your Open WebUI pipelines directory

3. **Configure the pipeline:**

   After adding, click on the pipeline to configure:
   - `SGR_API_BASE_URL`: URL of your SGR API (default: `http://localhost:8010`)
   - `DEFAULT_MODEL`: Default agent to use (default: `sgr_tool_calling_agent`)
   - `REQUEST_TIMEOUT`: Timeout in seconds (default: 300)
   - `EMIT_TOOL_CALLS`: Show tool usage in output (default: true)

## Available Agents

The pipeline automatically fetches available agents from your SGR API. Common agents include:

| Agent | Description |
|-------|-------------|
| `sgr_tool_calling_agent` | Standard research agent with tool calling |
| `custom_research_agent` | Custom research with extended capabilities |
| `fast_research_agent` | Optimized for quick responses |
| `presentation_agent` | Creates HTML slides and PPTX presentations |

## Usage

Once configured, you can:

1. Select any SGR agent from the model dropdown in Open WebUI
2. Type your research query
3. Watch the agent perform web searches and generate reports in real-time

## Features

- **Streaming Responses**: Real-time output as the agent works
- **Tool Visibility**: See which tools the agent uses (web search, report creation, etc.)
- **Multiple Agents**: Choose different agents for different research styles
- **Clarification Support**: Agents can ask for clarification when needed

## Troubleshooting

### Connection refused
Ensure the SGR API server is running:
```bash
python -m sgr_deep_research --port 8010
```

### No models available
Check the API is reachable:
```bash
curl http://localhost:8010/v1/models
```

### Timeout errors
Increase `REQUEST_TIMEOUT` in pipeline settings. Research tasks can take several minutes.

## Docker Deployment

If running Open WebUI in Docker, use the host machine's IP or Docker network:

```yaml
# Example valve configuration for Docker
SGR_API_BASE_URL: "http://host.docker.internal:8010"  # macOS/Windows
# or
SGR_API_BASE_URL: "http://172.17.0.1:8010"  # Linux
```

