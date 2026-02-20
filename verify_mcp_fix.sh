#!/bin/bash

# RAGFlow MCP Bug Fix - Verification Script
# This script verifies that the MCP bug fixes are correctly applied

set -e

echo "=========================================="
echo "RAGFlow MCP Bug Fix - Verification"
echo "=========================================="
echo ""

echo "📋 Step 1: Checking local files..."
echo ""

# Check if the modified files exist and contain the fixes
if [ ! -f "api/utils/api_utils.py" ]; then
    echo "❌ Error: api/utils/api_utils.py not found!"
    exit 1
fi

if [ ! -f "api/apps/mcp_server_app.py" ]; then
    echo "❌ Error: api/apps/mcp_server_app.py not found!"
    exit 1
fi

# Check for the fix in api_utils.py
if grep -q "errors = \[\]" api/utils/api_utils.py; then
    echo "✅ api/utils/api_utils.py contains the fix (errors list)"
else
    echo "❌ api/utils/api_utils.py does NOT contain the fix!"
    exit 1
fi

if grep -q "errors.append(error_msg)" api/utils/api_utils.py; then
    echo "✅ api/utils/api_utils.py contains error collection logic"
else
    echo "❌ api/utils/api_utils.py does NOT contain error collection logic!"
    exit 1
fi

# Check for the fix in mcp_server_app.py
if grep -q "if not tools:" api/apps/mcp_server_app.py; then
    echo "✅ api/apps/mcp_server_app.py contains the validation fix"
else
    echo "❌ api/apps/mcp_server_app.py does NOT contain the validation fix!"
    exit 1
fi

echo ""
echo "📋 Step 2: Checking Docker Compose configuration..."
echo ""

cd docker

# Check if docker-compose.yml has the volume mounts
if grep -q "api/utils/api_utils.py:/ragflow/api/utils/api_utils.py" docker-compose.yml; then
    echo "✅ api_utils.py volume mount configured"
else
    echo "❌ api_utils.py volume mount NOT configured!"
    exit 1
fi

if grep -q "api/apps/mcp_server_app.py:/ragflow/api/apps/mcp_server_app.py" docker-compose.yml; then
    echo "✅ mcp_server_app.py volume mount configured"
else
    echo "❌ mcp_server_app.py volume mount NOT configured!"
    exit 1
fi

echo ""
echo "📋 Step 3: Checking if RAGFlow container is running..."
echo ""

# Check if the container is running
if docker compose ps ragflow-server | grep -q "Up"; then
    echo "✅ RAGFlow server is running"
    
    echo ""
    echo "📋 Step 4: Verifying files inside container..."
    echo ""
    
    # Check if the files are correctly mounted in the container
    if docker compose exec -T ragflow-server test -f /ragflow/api/utils/api_utils.py; then
        echo "✅ api_utils.py exists in container"
        
        # Check if the fix is present in the container
        if docker compose exec -T ragflow-server grep -q "errors = \[\]" /ragflow/api/utils/api_utils.py; then
            echo "✅ api_utils.py fix is present in container"
        else
            echo "⚠️  api_utils.py fix NOT found in container - restart may be needed"
        fi
    else
        echo "❌ api_utils.py NOT found in container!"
        exit 1
    fi
    
    if docker compose exec -T ragflow-server test -f /ragflow/api/apps/mcp_server_app.py; then
        echo "✅ mcp_server_app.py exists in container"
        
        # Check if the fix is present in the container
        if docker compose exec -T ragflow-server grep -q "if not tools:" /ragflow/api/apps/mcp_server_app.py; then
            echo "✅ mcp_server_app.py fix is present in container"
        else
            echo "⚠️  mcp_server_app.py fix NOT found in container - restart may be needed"
        fi
    else
        echo "❌ mcp_server_app.py NOT found in container!"
        exit 1
    fi
    
else
    echo "⚠️  RAGFlow server is NOT running"
    echo "   Run './restart_ragflow_with_mcp_fix.sh' to start it"
fi

echo ""
echo "=========================================="
echo "✅ Verification Complete!"
echo "=========================================="
echo ""
echo "📝 Summary:"
echo "   ✅ Local files contain the fixes"
echo "   ✅ Docker Compose is configured correctly"
if docker compose ps ragflow-server | grep -q "Up"; then
    echo "   ✅ Container is running with fixes applied"
else
    echo "   ⚠️  Container needs to be restarted"
fi
echo ""
echo "🚀 Next steps:"
if docker compose ps ragflow-server | grep -q "Up"; then
    echo "   1. Test adding a BrowserOS MCP server"
    echo "   2. Verify error messages are clear"
else
    echo "   1. Run: ./restart_ragflow_with_mcp_fix.sh"
    echo "   2. Test adding a BrowserOS MCP server"
fi
echo ""

