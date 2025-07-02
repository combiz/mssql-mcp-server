#!/usr/bin/env python3
"""
Simple runner script for MSSQL MCP Server
This ensures the server runs correctly when called from MCP configuration
"""

if __name__ == "__main__":
    from mssql_mcp_server import main
    import asyncio
    asyncio.run(main())