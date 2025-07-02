#!/bin/bash
# Script to publish MSSQL MCP Server to PyPI

echo "Publishing MSSQL MCP Server to PyPI..."

# Test on TestPyPI first
echo "1. Upload to TestPyPI (optional):"
echo "   /opt/mssql_mcp/venv/bin/twine upload --repository testpypi dist/*"
echo ""

# Upload to PyPI
echo "2. Upload to PyPI:"
echo "   /opt/mssql_mcp/venv/bin/twine upload dist/*"
echo ""

echo "3. Or use API token directly:"
echo "   /opt/mssql_mcp/venv/bin/twine upload -u __token__ -p pypi-YOUR_TOKEN_HERE dist/*"
echo ""

echo "4. After publishing, install from PyPI:"
echo "   pip install mssql-mcp-server"