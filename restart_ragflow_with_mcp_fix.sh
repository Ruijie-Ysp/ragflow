#!/bin/bash

# RAGFlow MCP Bug Fix - Restart Script
# This script restarts the RAGFlow server with the MCP bug fixes applied

set -e

echo "=========================================="
echo "RAGFlow MCP Bug Fix - Restart Script"
echo "=========================================="
echo ""

# Change to docker directory
cd "$(dirname "$0")/docker"

echo "📋 Step 1: Checking modified files..."
echo ""

# Check if the modified files exist
if [ ! -f "../api/utils/api_utils.py" ]; then
    echo "❌ Error: api/utils/api_utils.py not found!"
    exit 1
fi

if [ ! -f "../api/apps/mcp_server_app.py" ]; then
    echo "❌ Error: api/apps/mcp_server_app.py not found!"
    exit 1
fi

if [ ! -f "../rag/utils/mcp_tool_call_conn.py" ]; then
    echo "❌ Error: rag/utils/mcp_tool_call_conn.py not found!"
    exit 1
fi

echo "✅ Modified files found:"
echo "   - api/utils/api_utils.py"
echo "   - api/apps/mcp_server_app.py"
echo "   - rag/utils/mcp_tool_call_conn.py"
echo ""

echo "📋 Step 2: Checking Docker Compose configuration..."
echo ""

# Check if docker-compose.yml has the volume mounts
if grep -q "api/utils/api_utils.py:/ragflow/api/utils/api_utils.py" docker-compose.yml; then
    echo "✅ Volume mounts configured in docker-compose.yml"
else
    echo "❌ Error: Volume mounts not found in docker-compose.yml"
    echo "   Please ensure the following lines are in the volumes section:"
    echo "   - ../api/utils/api_utils.py:/ragflow/api/utils/api_utils.py"
    echo "   - ../api/apps/mcp_server_app.py:/ragflow/api/apps/mcp_server_app.py"
    exit 1
fi
echo ""

echo "📋 Step 3: Stopping RAGFlow server..."
echo ""

# Stop the ragflow-server container
docker compose stop ragflow-server

echo "✅ RAGFlow server stopped"
echo ""

echo "📋 Step 4: Starting RAGFlow server with bug fixes..."
echo ""

# Start the ragflow-server container
docker compose up -d ragflow-server

echo "✅ RAGFlow server started with MCP bug fixes"
echo ""

echo "📋 Step 5: Waiting for server to be ready..."
echo ""

# Wait for the server to be ready
sleep 5

echo "📋 Step 6: Checking server logs..."
echo ""

# Show the last 20 lines of logs
docker compose logs --tail=20 ragflow-server

echo ""
echo "=========================================="
echo "✅ RAGFlow server restarted successfully!"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo "   1. Wait for the server to fully start (check logs above)"
echo "   2. Test adding a BrowserOS MCP server"
echo "   3. Verify error messages are now clear and helpful"
echo ""
echo "📊 To view live logs, run:"
echo "   cd docker && docker compose logs -f ragflow-server"
echo ""
echo "🔍 To check if the fix is working:"
echo "   1. Stop BrowserOS MCP Server (if running)"
echo "   2. Try to add MCP server at http://127.0.0.1:9101/mcp"
echo "   3. You should see: 'Failed to get tools from MCP server...'"
echo "   4. Start BrowserOS MCP Server"
echo "   5. Try again - should succeed with 29 tools"
echo ""

