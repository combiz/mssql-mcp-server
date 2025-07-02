"""
MSSQL MCP Server - A Model Context Protocol server for Microsoft SQL Server

This package provides a Model Context Protocol (MCP) server implementation
for Microsoft SQL Server, enabling AI assistants to interact with MSSQL databases
through a standardized interface.

Features:
- Execute SQL queries with proper error handling
- Browse database tables and schemas
- Handle multi-line queries correctly
- Support for both Windows and SQL authentication
- Configurable via environment variables
"""

from .server import __version__, __author__, main

__all__ = ['main', '__version__', '__author__']