#!/usr/bin/env python3
"""Generate config.yaml from environment variables for Railway deployment.

This script reads environment variables and generates the necessary configuration
files (config.yaml and agents.yaml) for the SGR Deep Research application.

Environment Variables:
    - LLM_API_KEY: OpenAI/OpenRouter API key
    - LLM_BASE_URL: API base URL (default: https://api.openai.com/v1)
    - LLM_MODEL: Model name (default: gpt-4o)
    - LLM_MAX_TOKENS: Max output tokens (default: 8000)
    - LLM_TEMPERATURE: Temperature (default: 0.4)
    - TAVILY_API_KEY: Tavily search API key
    - TAVILY_API_BASE_URL: Tavily API base URL (default: https://api.tavily.com)
"""

import os
import yaml
from pathlib import Path


def generate_config():
    """Generate config.yaml from environment variables."""
    
    config = {
        "llm": {
            "api_key": os.environ.get("LLM_API_KEY", ""),
            "base_url": os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
            "model": os.environ.get("LLM_MODEL", "gpt-4o"),
            "max_tokens": int(os.environ.get("LLM_MAX_TOKENS", "8000")),
            "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.4")),
        },
        "search": {
            "tavily_api_key": os.environ.get("TAVILY_API_KEY", ""),
            "tavily_api_base_url": os.environ.get("TAVILY_API_BASE_URL", "https://api.tavily.com"),
            "max_searches": int(os.environ.get("MAX_SEARCHES", "4")),
            "max_results": int(os.environ.get("MAX_RESULTS", "10")),
            "content_limit": int(os.environ.get("CONTENT_LIMIT", "1500")),
        },
        "execution": {
            "max_clarifications": int(os.environ.get("MAX_CLARIFICATIONS", "3")),
            "max_iterations": int(os.environ.get("MAX_ITERATIONS", "10")),
            "mcp_context_limit": int(os.environ.get("MCP_CONTEXT_LIMIT", "15000")),
            "logs_dir": os.environ.get("LOGS_DIR", "logs"),
            "reports_dir": os.environ.get("REPORTS_DIR", "reports"),
        },
        "agents": {},
    }

    # Remove empty API keys to avoid validation errors
    if not config["llm"]["api_key"]:
        del config["llm"]["api_key"]
    if not config["search"]["tavily_api_key"]:
        del config["search"]["tavily_api_key"]

    # Add proxy if provided
    if proxy := os.environ.get("LLM_PROXY"):
        config["llm"]["proxy"] = proxy

    return config


def main():
    config_path = Path("/app/config.yaml")
    
    # Check if config.yaml already exists
    if config_path.exists():
        print(f"Config file already exists at {config_path}")
        return

    config = generate_config()
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Generated config.yaml at {config_path}")


if __name__ == "__main__":
    main()

