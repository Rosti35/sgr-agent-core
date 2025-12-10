#!/bin/sh
set -e

# Generate config.yaml from environment variables if it doesn't exist
if [ ! -f "/app/config.yaml" ]; then
    echo "Generating config.yaml from environment variables..."
    python3 /app/scripts/generate_config.py
fi

# Copy agents.yaml.example to agents.yaml if it doesn't exist
if [ ! -f "/app/agents.yaml" ]; then
    if [ -f "/app/agents.yaml.example" ]; then
        echo "Copying agents.yaml.example to agents.yaml..."
        cp /app/agents.yaml.example /app/agents.yaml
    fi
fi

# Create necessary directories
mkdir -p /app/logs /app/reports

# Set default port if not provided
APP_PORT="${PORT:-8010}"

# Start the application
exec python3 -m sgr_deep_research --port "$APP_PORT"

