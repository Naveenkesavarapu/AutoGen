"""
Run script for MCP server.
"""
import os
import sys
from pathlib import Path

# Add the parent directory (src) to Python path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from mcp_server.server import start_server

if __name__ == '__main__':
    print("Starting MCP server...")
    start_server() 