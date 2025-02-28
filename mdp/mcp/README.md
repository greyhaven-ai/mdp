# Model Context Protocol (MCP) Module

This module provides integration between MDP and the Model Context Protocol (MCP) ecosystem. It allows you to:

1. Run an MCP server that serves MDP documents
2. Connect to MCP servers to retrieve and manipulate documents
3. Fetch relevant context for AI models

## Overview

The MCP module includes two implementations:

1. **Official MCP SDK Integration** - Leverages the official [MCP Python SDK](https://github.com/model-context-protocol/mcp-python) for full compatibility with the MCP ecosystem
2. **Legacy Custom Implementation** - Original implementation (maintained for backward compatibility)

## Resource URI Structure

The MCP implementation uses the following URI structure for resources:

```
mdp://docs/{doc_id}                 # Document content
mdp://docs/{doc_id}/metadata        # Document metadata
mdp://collections/list               # List all documents
```

This aligns with the MDP URI format used in the core library: `mdp://organization/project/path`.

## Using the Official MCP SDK Integration

### Server-Side Usage

```python
from mdp.mcp.server_mcp import create_mcp_server

# Create and start an MCP server with a title
server = create_mcp_server("My Document Server") 
server.run()
```

The server provides the following capabilities:
- Document storage and retrieval
- Document search
- Context fetching
- Document metadata access

### Client-Side Usage

#### Asynchronous Client

```python
import asyncio
from mdp.document import Document
from mdp.mcp.client_mcp import MCPClient

async def main():
    # Create an async client
    # Pass the path to a server file or URL
    async with MCPClient("http://localhost:8000") as client:
        # Create a document
        doc = Document(
            content="This is a sample document.",
            metadata={"title": "Sample Document", "tags": ["example"]}
        )
        
        # Create a document
        result = await client.create_document(doc)
        doc_id = result.split(": ")[1]
        
        # Read a document
        doc = await client.read_document(doc_id)
        
        # Update a document
        doc.content += "\nAdditional content."
        result = await client.update_document(doc_id, doc)
        
        # Search documents
        results = await client.search_documents("sample")
        
        # Fetch context
        context = await client.fetch_context("sample document")
        
        # Delete a document
        result = await client.delete_document(doc_id)
        
        # List documents
        docs = await client.list_documents()

asyncio.run(main())
```

#### Synchronous Client

```python
from mdp.document import Document
from mdp.mcp.client_mcp import MCPClientSync

# Create a sync client
with MCPClientSync("http://localhost:8000") as client:
    # Create a document
    doc = Document(
        content="This is a sample document.",
        metadata={"title": "Sample Document", "tags": ["example"]}
    )
    
    # Create a document
    result = client.create_document(doc)
    doc_id = result.split(": ")[1]
    
    # Read a document
    doc = client.read_document(doc_id)
    
    # Update a document
    doc.content += "\nAdditional content."
    result = client.update_document(doc_id, doc)
    
    # Search documents
    results = client.search_documents("sample")
    
    # Fetch context
    context = client.fetch_context("sample document")
    
    # Delete a document
    result = client.delete_document(doc_id)
    
    # List documents
    docs = client.list_documents()
```

## Running the Example

The module includes a comprehensive example that demonstrates both server and client functionality:

```bash
# Run the server
python -m mdp.mcp.example_official_mcp --mode server

# In a separate terminal:
# Run the async client example
python -m mdp.mcp.example_official_mcp --mode async

# Or run the sync client example
python -m mdp.mcp.example_official_mcp --mode sync
```

## Legacy Implementation

For backward compatibility, the original custom implementation is still available:

```python
from mdp.mcp import MCPServer, MCPClient

# Start a server
server = MCPServer(port=8080)
server.start()

# Connect a client
client = MCPClient(host="localhost", port=8080)
# Use client methods...
```

## LLM Integration

The MCP server is designed to work seamlessly with Large Language Models (LLMs) like Claude, GPT-4, and others. The implementation provides LLM-friendly features:

### Self-Documenting API

The MCP server exposes its API documentation through standard endpoints:
- `mcp://api/metadata` - Basic API information
- `mcp://api/tools/docs` - Documentation for all available tools
- `mcp://api/tools/{tool_name}/docs` - Documentation for a specific tool

### Tool Descriptions and Examples

Each endpoint includes:
- Detailed descriptions of its purpose
- JSON Schema for inputs and outputs
- Usage examples

### Example LLM Interaction

When an LLM connects to the MCP server, it can retrieve capabilities and documentation:

```
LLM: What tools are available for working with documents?

MCP Server: I have several tools available for working with MDP documents:

1. create_document - Create a new MDP document
2. update_document - Update an existing document
3. delete_document - Delete a document by ID
4. search_documents - Search for documents by content or metadata
5. fetch_context - Get relevant document content based on a query

Would you like details about any specific tool?

LLM: How do I create a new document?

MCP Server: To create a new document, use the create_document tool with this format:

Input:
- content: The document content in MDP format (YAML frontmatter + markdown)

Example:
create_document(content="---
title: Example Document
tags: [example, documentation]
---

This is an example document.")

Output:
- doc_id: The UUID of the created document
- message: Confirmation message

LLM: Please create a document about machine learning.

MCP Server: I'll create that document for you.

[Calls create_document with appropriate content]

Document created successfully! The document ID is: 123e4567-e89b-12d3-a456-426614174000
```

### Integrating With Your LLM Application

To integrate an LLM with the MCP server:

1. Start the MCP server:
   ```python
   from mdp.mcp.server_mcp import create_mcp_server
   
   server = create_mcp_server("Document Server")
   server.run()
   ```

2. In your LLM application, register the MCP tools:
   ```python
   from mdp.mcp.client_mcp import MCPClientSync
   
   # Initialize client
   client = MCPClientSync("http://localhost:8000")
   
   # Register MCP functions with your LLM framework
   # The exact implementation depends on your LLM integration
   ```

3. When users ask to retrieve or manipulate documents, the LLM can use the appropriate MCP tools to fulfill their requests. 