#!/usr/bin/env python3
"""
MSSQL MCP Server - A Model Context Protocol server for Microsoft SQL Server
Provides SQL query execution and table introspection capabilities via MCP
"""

import asyncio
import logging
import os
import re
import sys
from typing import Optional, Tuple, List, Dict, Any
from pyodbc import connect, Error as PyODBCError
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mssql_mcp_server")

# Version information
__version__ = "1.0.0"
__author__ = "MSSQL MCP Server Contributors"


class QueryPreprocessor:
    """Handles preprocessing of SQL queries to fix common issues"""
    
    @staticmethod
    def preprocess_query(query: str) -> str:
        """
        Preprocess SQL query to handle newlines and other formatting issues.
        
        - Preserves newlines within string literals
        - Replaces other newlines with spaces
        - Handles GO statements
        - Cleans up excessive whitespace
        
        Args:
            query: Raw SQL query string
            
        Returns:
            Preprocessed query string
        """
        if not query:
            return query
            
        # Remove leading/trailing whitespace
        query = query.strip()
        
        # Handle GO statements (SQL Server batch separator)
        if re.search(r'\bGO\b', query, re.IGNORECASE | re.MULTILINE):
            # Split by GO and return first batch with warning
            parts = re.split(r'\bGO\b', query, flags=re.IGNORECASE | re.MULTILINE)
            if len(parts) > 1:
                logger.warning("Query contains GO statements. Only executing first batch.")
                query = parts[0].strip()
        
        # Process the query character by character
        in_string = False
        in_comment = False
        in_multiline_comment = False
        result = []
        i = 0
        
        while i < len(query):
            # Handle multi-line comments
            if not in_string and i < len(query) - 1:
                if query[i:i+2] == '/*':
                    in_multiline_comment = True
                    result.append(query[i:i+2])
                    i += 2
                    continue
                elif query[i:i+2] == '*/' and in_multiline_comment:
                    in_multiline_comment = False
                    result.append(query[i:i+2])
                    i += 2
                    continue
            
            # Handle single-line comments
            if not in_string and not in_multiline_comment and i < len(query) - 1:
                if query[i:i+2] == '--':
                    in_comment = True
                    result.append(query[i:i+2])
                    i += 2
                    continue
            
            char = query[i]
            
            # Handle string literals
            if char == "'" and not in_comment and not in_multiline_comment:
                # Check for escaped quote
                if i + 1 < len(query) and query[i+1] == "'":
                    result.append("''")
                    i += 2
                    continue
                else:
                    in_string = not in_string
                    result.append(char)
            
            # Handle newlines
            elif char == '\n':
                if in_string or in_multiline_comment:
                    result.append(char)
                elif in_comment:
                    # End single-line comment
                    in_comment = False
                    result.append(char)
                else:
                    # Replace newline with space outside strings/comments
                    if result and result[-1] not in (' ', '\t'):
                        result.append(' ')
            
            # Handle carriage returns
            elif char == '\r':
                if in_string or in_multiline_comment:
                    result.append(char)
                # Skip carriage returns outside strings
            
            # Handle tabs
            elif char == '\t' and not in_string and not in_comment and not in_multiline_comment:
                # Replace tabs with spaces outside strings
                if result and result[-1] != ' ':
                    result.append(' ')
            
            else:
                result.append(char)
            
            i += 1
        
        processed_query = ''.join(result)
        
        # Clean up multiple spaces (but not in strings)
        if not in_string and not in_comment and not in_multiline_comment:
            processed_query = re.sub(r'[ ]{2,}', ' ', processed_query)
        
        return processed_query.strip()


class DatabaseConfig:
    """Handles database configuration from environment variables"""
    
    @staticmethod
    def get_config() -> Tuple[Dict[str, Any], str]:
        """
        Get database configuration from environment variables.
        
        Environment variables:
        - MSSQL_HOST or MSSQL_SERVER: Server hostname (default: localhost)
        - MSSQL_PORT: Server port (default: 1433)
        - MSSQL_USER: Username (required for non-trusted connections)
        - MSSQL_PASSWORD: Password (required for non-trusted connections)
        - MSSQL_DATABASE: Database name (required)
        - MSSQL_DRIVER: ODBC driver (default: ODBC Driver 17 for SQL Server)
        - MSSQL_TRUSTED_CONNECTION: Use Windows authentication (default: no)
        - MSSQL_TRUST_SERVER_CERTIFICATE: Trust server certificate (default: yes)
        - MSSQL_ENCRYPT: Encrypt connection (default: yes)
        - MSSQL_CONNECTION_TIMEOUT: Connection timeout in seconds (default: 30)
        - MSSQL_MULTI_SUBNET_FAILOVER: Enable multi-subnet failover (default: no)
        
        Returns:
            Tuple of (config dict, connection string)
        """
        # Get server from either MSSQL_HOST or MSSQL_SERVER
        server = os.getenv("MSSQL_HOST") or os.getenv("MSSQL_SERVER", "localhost")
        port = os.getenv("MSSQL_PORT", "1433")
        
        # Authentication
        user = os.getenv("MSSQL_USER")
        password = os.getenv("MSSQL_PASSWORD")
        trusted_connection = os.getenv("MSSQL_TRUSTED_CONNECTION", "no").lower() in ('yes', 'true', '1')
        
        # Database
        database = os.getenv("MSSQL_DATABASE")
        if not database:
            raise ValueError("MSSQL_DATABASE environment variable is required")
        
        # Driver configuration
        driver = os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server")
        
        # Connection options
        trust_cert = os.getenv("MSSQL_TRUST_SERVER_CERTIFICATE", "yes").lower() in ('yes', 'true', '1')
        encrypt = os.getenv("MSSQL_ENCRYPT", "yes").lower() in ('yes', 'true', '1')
        timeout = int(os.getenv("MSSQL_CONNECTION_TIMEOUT", "30"))
        multi_subnet = os.getenv("MSSQL_MULTI_SUBNET_FAILOVER", "no").lower() in ('yes', 'true', '1')
        
        # Validate configuration
        if not trusted_connection and not all([user, password]):
            raise ValueError(
                "MSSQL_USER and MSSQL_PASSWORD are required when not using trusted connection. "
                "Set MSSQL_TRUSTED_CONNECTION=yes for Windows authentication."
            )
        
        # Build configuration dictionary
        config = {
            "driver": driver,
            "server": server,
            "port": port,
            "database": database,
            "trusted_connection": trusted_connection,
            "trust_server_certificate": trust_cert,
            "encrypt": encrypt,
            "timeout": timeout,
            "multi_subnet_failover": multi_subnet
        }
        
        if not trusted_connection:
            config["user"] = user
            config["password"] = password
        
        # Build connection string
        conn_parts = [
            f"Driver={{{driver}}}",
            f"Server={server},{port}" if port != "1433" else f"Server={server}",
            f"Database={database}",
            f"TrustServerCertificate={'yes' if trust_cert else 'no'}",
            f"Encrypt={'yes' if encrypt else 'no'}",
            f"Connection Timeout={timeout}",
            f"MultiSubnetFailover={'yes' if multi_subnet else 'no'}"
        ]
        
        if trusted_connection:
            conn_parts.append("Trusted_Connection=yes")
        else:
            conn_parts.extend([
                f"UID={user}",
                f"PWD={password}"
            ])
        
        connection_string = ";".join(conn_parts) + ";"
        
        # Log configuration (without password)
        safe_config = config.copy()
        if "password" in safe_config:
            safe_config["password"] = "***"
        logger.info(f"Database configuration: {safe_config}")
        
        return config, connection_string


class SQLExecutor:
    """Handles SQL query execution"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.preprocessor = QueryPreprocessor()
    
    def execute_query(self, query: str) -> Tuple[bool, List[str], Optional[str]]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Tuple of (success, results, error_message)
        """
        try:
            # Preprocess the query
            original_query = query
            processed_query = self.preprocessor.preprocess_query(query)
            
            if original_query != processed_query:
                logger.debug(f"Query preprocessed. Original length: {len(original_query)}, "
                           f"Processed length: {len(processed_query)}")
            
            with connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    # Execute the query
                    cursor.execute(processed_query)
                    
                    # Handle different query types
                    query_upper = processed_query.strip().upper()
                    
                    # SELECT queries
                    if query_upper.startswith("SELECT") or query_upper.startswith("WITH"):
                        return self._handle_select_query(cursor)
                    
                    # SHOW TABLES (non-standard SQL Server)
                    elif query_upper == "SHOW TABLES":
                        return self._handle_show_tables(cursor, conn)
                    
                    # INSERT, UPDATE, DELETE, etc.
                    else:
                        conn.commit()
                        rows_affected = cursor.rowcount if cursor.rowcount >= 0 else 0
                        return True, [f"Query executed successfully. Rows affected: {rows_affected}"], None
                    
        except PyODBCError as e:
            error_msg = str(e)
            logger.error(f"Database error executing query: {error_msg}")
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, [], error_msg
    
    def _handle_select_query(self, cursor) -> Tuple[bool, List[str], Optional[str]]:
        """Handle SELECT query results"""
        try:
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Format results
            results = []
            if columns:
                # Header row
                results.append("|".join(columns))
                results.append("|".join(["-" * len(col) for col in columns]))
                
                # Data rows
                for row in rows:
                    formatted_row = []
                    for value in row:
                        if value is None:
                            formatted_row.append("NULL")
                        else:
                            formatted_row.append(str(value))
                    results.append("|".join(formatted_row))
            else:
                results.append("Query returned no columns")
            
            # Add row count
            results.append(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''} affected)")
            
            return True, results, None
            
        except Exception as e:
            return False, [], f"Error processing query results: {str(e)}"
    
    def _handle_show_tables(self, cursor, conn) -> Tuple[bool, List[str], Optional[str]]:
        """Handle SHOW TABLES command (MySQL compatibility)"""
        try:
            # Get database name
            db_config, _ = DatabaseConfig.get_config()
            database = db_config['database']
            
            # Execute SQL Server equivalent
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE' 
                  AND TABLE_CATALOG = ?
                ORDER BY TABLE_NAME
            """, database)
            
            tables = cursor.fetchall()
            
            # Format results
            results = [f"Tables_in_{database}"]
            results.append("-" * len(results[0]))
            results.extend([table[0] for table in tables])
            results.append(f"\n({len(tables)} table{'s' if len(tables) != 1 else ''})")
            
            return True, results, None
            
        except Exception as e:
            return False, [], f"Error listing tables: {str(e)}"


# Initialize MCP server
app = Server("mssql_mcp_server")


@app.list_resources()
async def list_resources() -> List[Resource]:
    """List MSSQL tables as resources."""
    try:
        config, connection_string = DatabaseConfig.get_config()
        database = config['database']
        
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                # Get all user tables
                cursor.execute("""
                    SELECT 
                        s.name AS schema_name,
                        t.name AS table_name,
                        t.create_date,
                        t.modify_date
                    FROM sys.tables t
                    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                    WHERE t.type = 'U'  -- User tables only
                    ORDER BY s.name, t.name
                """)
                
                tables = cursor.fetchall()
                logger.info(f"Found {len(tables)} tables in database '{database}'")
                
                resources = []
                for schema, table, created, modified in tables:
                    full_table_name = f"{schema}.{table}"
                    resources.append(
                        Resource(
                            uri=f"mssql://{database}/{full_table_name}/schema",
                            name=f"Schema: {full_table_name}",
                            mimeType="application/json",
                            description=f"Schema definition for table {full_table_name}"
                        )
                    )
                    resources.append(
                        Resource(
                            uri=f"mssql://{database}/{full_table_name}/data",
                            name=f"Data: {full_table_name}",
                            mimeType="text/plain",
                            description=f"Sample data from table {full_table_name} (limited to 100 rows)"
                        )
                    )
                
                return resources
                
    except Exception as e:
        logger.error(f"Failed to list resources: {str(e)}")
        return []


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read table schema or data."""
    uri_str = str(uri)
    logger.info(f"Reading resource: {uri_str}")
    
    if not uri_str.startswith("mssql://"):
        raise ValueError(f"Invalid URI scheme: {uri_str}")
    
    try:
        # Parse URI: mssql://database/schema.table/type
        parts = uri_str[8:].split('/')
        if len(parts) != 3:
            raise ValueError(f"Invalid URI format: {uri_str}")
        
        database, table_full, resource_type = parts
        
        # Split schema.table
        if '.' in table_full:
            schema, table = table_full.split('.', 1)
        else:
            schema = 'dbo'
            table = table_full
        
        config, connection_string = DatabaseConfig.get_config()
        
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                if resource_type == 'schema':
                    return await _read_table_schema(cursor, schema, table)
                elif resource_type == 'data':
                    return await _read_table_data(cursor, schema, table)
                else:
                    raise ValueError(f"Unknown resource type: {resource_type}")
                    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {str(e)}")
        raise RuntimeError(f"Error reading resource: {str(e)}")


async def _read_table_schema(cursor, schema: str, table: str) -> str:
    """Read table schema information."""
    cursor.execute("""
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            CASE 
                WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES'
                ELSE 'NO'
            END AS IS_PRIMARY_KEY
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS ku
                ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY' 
                AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        ) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA 
            AND c.TABLE_NAME = pk.TABLE_NAME 
            AND c.COLUMN_NAME = pk.COLUMN_NAME
        WHERE c.TABLE_SCHEMA = ? AND c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
    """, schema, table)
    
    columns = cursor.fetchall()
    
    # Format schema information
    result = [f"Schema for {schema}.{table}:", "=" * 50, ""]
    result.append(f"{'Column':<30} {'Type':<20} {'Nullable':<10} {'PK':<5} {'Default':<20}")
    result.append("-" * 100)
    
    for col in columns:
        name, dtype, char_len, num_prec, num_scale, nullable, default, is_pk = col
        
        # Format data type
        if char_len:
            type_str = f"{dtype}({char_len})"
        elif num_prec and num_scale:
            type_str = f"{dtype}({num_prec},{num_scale})"
        elif num_prec:
            type_str = f"{dtype}({num_prec})"
        else:
            type_str = dtype
        
        # Format default
        default_str = str(default)[:20] if default else ""
        
        result.append(
            f"{name:<30} {type_str:<20} {nullable:<10} {is_pk:<5} {default_str:<20}"
        )
    
    return "\n".join(result)


async def _read_table_data(cursor, schema: str, table: str) -> str:
    """Read sample data from table."""
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table}]")
    total_rows = cursor.fetchone()[0]
    
    # Get sample data
    cursor.execute(f"SELECT TOP 100 * FROM [{schema}].[{table}]")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Format results
    result = [f"Sample data from {schema}.{table} (showing {len(rows)} of {total_rows} rows):", ""]
    
    if rows:
        # Create formatted table
        result.append("|".join(columns))
        result.append("|".join(["-" * len(col) for col in columns]))
        
        for row in rows:
            formatted_row = []
            for value in row:
                if value is None:
                    formatted_row.append("NULL")
                else:
                    str_value = str(value)
                    # Truncate long values
                    if len(str_value) > 50:
                        str_value = str_value[:47] + "..."
                    formatted_row.append(str_value)
            result.append("|".join(formatted_row))
    else:
        result.append("(No data)")
    
    return "\n".join(result)


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MSSQL tools."""
    return [
        Tool(
            name="execute_sql",
            description="Execute an SQL query on the MSSQL server",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Execute SQL commands."""
    logger.info(f"Calling tool: {name}")
    
    if name != "execute_sql":
        raise ValueError(f"Unknown tool: {name}")
    
    query = arguments.get("query")
    if not query:
        raise ValueError("Query parameter is required")
    
    # Log query info (truncated for security)
    query_preview = query[:100] + "..." if len(query) > 100 else query
    logger.info(f"Executing query: {query_preview}")
    
    try:
        config, connection_string = DatabaseConfig.get_config()
        executor = SQLExecutor(connection_string)
        
        success, results, error = executor.execute_query(query)
        
        if success:
            return [TextContent(type="text", text="\n".join(results))]
        else:
            return [TextContent(type="text", text=f"Error: {error}")]
            
    except Exception as e:
        logger.error(f"Error in call_tool: {str(e)}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point to run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    logger.info(f"Starting MSSQL MCP Server v{__version__}")
    
    try:
        # Validate configuration on startup
        config, connection_string = DatabaseConfig.get_config()
        logger.info(f"Connecting to {config['server']}:{config['port']}/{config['database']}")
        
        # Test connection
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                logger.info(f"Connected to SQL Server: {version.split('\\n')[0]}")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        sys.exit(1)
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except Exception as e:
            logger.error(f"Server error: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(main())