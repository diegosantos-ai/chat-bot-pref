#!/usr/bin/env python3
""" Run the MCP server with dynamic project-specific configuration """
import asyncio
import hashlib
import logging
import os
import sys
from pathlib import Path

# This assumes the 'coder_mcp' package is available in the environment.
# If it's installed via pip, this should work. If it's a local package,
# adjustments to sys.path might be needed if not run from the project root.
try:
    from coder_mcp.server import main
except ImportError:
    print("Error: The 'coder_mcp' package is not installed or not in the Python path.", file=sys.stderr)
    print("Please ensure the required dependencies for Antigravity agents are installed.", file=sys.stderr)
    sys.exit(1)

def get_project_identifier(workspace_path: str) -> tuple[str, str]:
    """
    Generate a unique identifier for the project based on its path.
    Returns: (short_name, hash_id)
    """
    path = Path(workspace_path)
    # Get the project name from the last directory
    project_name = path.name.lower()
    # Clean the project name (remove special chars, limit length)
    clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)[:20]
    # Generate a short hash of the full path for uniqueness
    path_hash = hashlib.md5(str(path).encode(), usedforsecurity=False).hexdigest()[:8]
    return clean_name, path_hash

def setup_dynamic_redis_config():
    """
    Dynamically configure Redis isolation based on the project workspace.
    This allows multiple projects to use the same Redis instance without conflicts.
    """
    # Get workspace root from environment or current directory
    workspace_root = os.getenv("MCP_WORKSPACE_ROOT", str(Path.cwd()))

    # Generate project-specific identifiers
    project_name, project_hash = get_project_identifier(workspace_root)

    # Create a unique Redis namespace for vector storage
    # Format: projectname_hash:doc:
    vector_prefix = f"{project_name}_{project_hash}:doc:"
    vector_index = f"{project_name}_{project_hash}_vectors"

    # Set environment variables for the coder_mcp server to use
    os.environ["VECTOR_PREFIX"] = vector_prefix
    os.environ["REDIS_VECTOR_INDEX"] = vector_index

    # Log configuration to stderr to avoid interfering with the MCP's JSON-RPC protocol on stdout
    print("=== MCP Server: Dynamic Redis Configuration ===", file=sys.stderr)
    print(f"Project Workspace: {workspace_root}", file=sys.stderr)
    print(f"Project Name:      {project_name}", file=sys.stderr)
    print(f"Project Hash:      {project_hash}", file=sys.stderr)
    print(f"Redis Vector NS:   {vector_prefix}", file=sys.stderr)
    print(f"Redis Vector Index:  {vector_index}", file=sys.stderr)
    print("===========================================", file=sys.stderr)

if __name__ == "__main__":
    # Setup the dynamic environment configuration before starting the server
    setup_dynamic_redis_config()

    # Run the main asynchronous event loop for the server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down MCP server.", file=sys.stderr)
    except Exception as e:
        logging.basicConfig()
        logging.getLogger().exception("An unexpected error occurred in the MCP server")
        sys.exit(1)
