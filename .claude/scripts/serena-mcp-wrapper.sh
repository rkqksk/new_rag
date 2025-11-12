#!/bin/bash

# Serena MCP Server Wrapper with proper Python environment
export PATH="/tmp/serena_env/bin:$PATH"
export PYTHONPATH="/tmp/serena_env/lib/python3.14/site-packages:$PYTHONPATH"

# Ensure python command is available
if ! command -v python &> /dev/null; then
    # Create python symlink if it doesn't exist
    if [ -f "/tmp/serena_env/bin/python3" ] && [ ! -f "/tmp/serena_env/bin/python" ]; then
        ln -s "/tmp/serena_env/bin/python3" "/tmp/serena_env/bin/python"
    fi
fi

# Run Serena MCP server with all arguments passed through
exec /tmp/serena_env/bin/serena-mcp-server "$@"