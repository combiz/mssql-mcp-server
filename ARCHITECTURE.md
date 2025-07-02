# MSSQL MCP Server Architecture

## Overview

The MSSQL MCP Server is designed with a modular architecture that separates concerns and provides a clean, maintainable codebase. This document describes the key architectural decisions and components.

## Core Components

### 1. Query Preprocessing Engine (`QueryPreprocessor`)

The heart of our SQL handling system, this component ensures that queries are properly formatted before execution:

```
Raw Query → Preprocessor → Clean Query → Executor
```

**Key Features:**
- Multi-line query normalization
- Comment preservation in strings
- GO statement handling
- Smart whitespace management

### 2. Configuration Management (`DatabaseConfig`)

Centralized configuration handling with environment variable support:

```
Environment Variables → DatabaseConfig → Connection String
                     ↓
                Validation & Defaults
```

**Supported Configurations:**
- Dual authentication modes (Windows/SQL)
- Connection security settings
- Timeout and retry logic
- Multi-subnet failover support

### 3. SQL Execution Layer (`SQLExecutor`)

Handles the actual database interactions with proper error handling:

```
Query → Executor → Result Formatting → Response
           ↓
      Error Handler
```

**Features:**
- Connection pooling
- Transaction management
- Result set formatting
- Error categorization

## MCP Protocol Implementation

### Resource Model

Tables are exposed as MCP resources with two views:

1. **Schema View** (`mssql://database/schema.table/schema`)
   - Column definitions
   - Data types
   - Constraints
   - Primary keys

2. **Data View** (`mssql://database/schema.table/data`)
   - Sample data (configurable limit)
   - Formatted output
   - Row counts

### Tool Interface

Single tool exposed: `execute_sql`

```json
{
  "name": "execute_sql",
  "inputSchema": {
    "query": "string"
  }
}
```

## Security Architecture

### Authentication Flow

```
Client → MCP Server → SQL Server
   ↓         ↓            ↓
  Env    Validation   Auth Check
```

### Security Layers

1. **Connection Security**
   - TLS/SSL encryption
   - Certificate validation
   - Credential isolation

2. **Query Safety**
   - No query manipulation
   - Proper error messages
   - Audit logging capability

## Error Handling Strategy

### Error Categories

1. **Connection Errors**
   - Network issues
   - Authentication failures
   - Server availability

2. **Query Errors**
   - Syntax errors
   - Permission denied
   - Data violations

3. **System Errors**
   - Resource constraints
   - Timeout conditions
   - Internal failures

### Error Response Format

```python
{
  "success": False,
  "error": "Detailed error message",
  "category": "connection|query|system"
}
```

## Performance Considerations

### Connection Management
- Connection pooling by default
- Configurable timeout values
- Automatic retry logic

### Query Optimization
- Preprocessor reduces parsing overhead
- Efficient result streaming
- Memory-conscious data handling

## Extensibility Points

### 1. Custom Authenticators
Extend `DatabaseConfig` to support new authentication methods.

### 2. Query Middleware
Add preprocessing steps by extending `QueryPreprocessor`.

### 3. Result Formatters
Implement custom formatters for different output needs.

### 4. Resource Types
Add new resource types beyond tables (views, procedures, etc.).

## Deployment Architecture

### Standalone Mode
```
Python Process → MSSQL MCP Server → SQL Server
```

### MCP Client Integration
```
Claude/Cursor → MCP Protocol → MSSQL MCP Server → SQL Server
```

### Container Deployment
```
Docker Container
    ├── MSSQL MCP Server
    ├── ODBC Drivers
    └── Python Runtime
```

## Future Architecture Considerations

1. **Query Caching Layer**
   - Result caching for repeated queries
   - Cache invalidation strategies

2. **Multi-Database Support**
   - Connection multiplexing
   - Database context switching

3. **Advanced Security**
   - Row-level security integration
   - Query audit trails

4. **Performance Monitoring**
   - Query execution metrics
   - Connection pool statistics

This architecture provides a solid foundation for a production-ready MCP server while maintaining flexibility for future enhancements.