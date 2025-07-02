#!/usr/bin/env python3
"""
Setup script for MSSQL MCP Server
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    readme_path = os.path.join(here, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name='mssql-mcp-server-enhanced',
    version='1.0.0',
    author='MSSQL MCP Server Contributors',
    author_email='',
    description='A Model Context Protocol server for Microsoft SQL Server',
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/combiz/mssql-mcp-server',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Database',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
    install_requires=[
        'mcp>=0.1.0',
        'pyodbc>=4.0.0',
        'pydantic>=2.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'mssql-mcp-server=mssql_mcp_server.server:main',
        ],
        'mcp_servers': [
            'mssql=mssql_mcp_server.server:app',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/combiz/mssql-mcp-server/issues',
        'Source': 'https://github.com/combiz/mssql-mcp-server',
    },
)