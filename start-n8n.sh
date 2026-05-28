#!/bin/bash
# LinkedIn Report Automation — n8n Starter
# Reads configuration from .env file

cd "$(dirname "$0")"

# Load .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in your credentials."
    exit 1
fi

# n8n required settings
export N8N_BLOCK_ENV_ACCESS_IN_NODE=false
export NODE_FUNCTION_ALLOW_BUILTIN="fs,path,child_process"
export N8N_RUNNERS_TASK_TIMEOUT=900
export NODES_EXCLUDE="[]"

echo "============================================"
echo "  LinkedIn Report Automation"
echo "============================================"
echo "  n8n UI:      http://localhost:${N8N_PORT:-5678}"
echo "  Report Form: http://localhost:${N8N_PORT:-5678}/webhook/linkedin-report-v2"
echo "============================================"
echo ""

n8n start
