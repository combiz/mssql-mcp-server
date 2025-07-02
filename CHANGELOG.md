# Changelog

All notable changes to the MSSQL MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-02

### Added
- Initial release of MSSQL MCP Server
- Full Model Context Protocol (MCP) implementation for SQL Server
- Advanced query preprocessing with multi-line support
- Comprehensive environment variable configuration
- Support for both Windows and SQL authentication
- Table schema introspection capabilities
- Sample data viewing with pagination
- Connection pooling and timeout management
- Detailed error messages and logging
- Support for SQL Server 2016+ and Azure SQL Database

### Features
- **Query Preprocessing Engine**: Handles complex multi-line queries, comments, and GO statements
- **Dual Authentication**: Seamless support for both Windows and SQL authentication modes
- **Resource Management**: Browse tables as MCP resources with schema and data views
- **Security First**: Connection encryption, certificate validation, and secure credential handling
- **Developer Friendly**: Comprehensive logging, error messages, and debugging support

### Technical Details
- Built on MCP protocol for AI assistant integration
- Uses pyodbc for robust SQL Server connectivity
- Implements connection pooling for performance
- Full Python 3.8+ compatibility
- Type hints throughout the codebase