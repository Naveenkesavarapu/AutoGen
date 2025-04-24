"""
Run script for MCP server.
"""
import os
import sys

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from mcp_server import start_server

if __name__ == '__main__':
    start_server() 