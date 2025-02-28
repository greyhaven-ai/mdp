"""
MCP (Model Context Protocol) module for MDP.

This module provides integration with the Model Context Protocol (MCP) ecosystem,
allowing MDP documents to be served and accessed through MCP-compatible clients.

The MCP integration enables LLMs (Large Language Models) to interact with MDP documents
through a standardized protocol, providing capabilities such as:

1. Document retrieval and manipulation
2. Context-aware search
3. Semantic understanding of document relationships
4. Structured metadata access

## LLM Integration

The MCP server implementation includes LLM-specific optimizations:

- Detailed tool descriptions with examples
- Consistent schema definitions for inputs and outputs
- Resource-based access pattern for document content
- System prompts that guide LLM behavior

Example LLM interaction flow:
1. LLM connects to MCP server (automatically or via user request)
2. LLM receives capabilities and tool descriptions
3. LLM can search documents, fetch context, and manipulate documents
4. The LLM responds to user with information from documents

## URI Structure

The module uses a consistent URI structure:

- `mdp://docs/{doc_id}` - Document content
- `mdp://docs/{doc_id}/metadata` - Document metadata
- `mdp://collections/list` - List all documents
- `mcp://api/metadata` - API documentation
- `mcp://api/tools/docs` - Tool documentation
"""

from .server import create_mcp_server
from .client import MCPClient, MCPClientSync
from .llm_docs import (
    get_server_documentation,
    get_tool_documentation,
    get_workflow_examples,
    get_documentation_markdown
)

__all__ = [
    # Server
    "create_mcp_server",
    
    # Clients
    "MCPClient",
    "MCPClientSync",
    
    # Documentation
    "get_server_documentation",
    "get_tool_documentation",
    "get_workflow_examples",
    "get_documentation_markdown"
] 