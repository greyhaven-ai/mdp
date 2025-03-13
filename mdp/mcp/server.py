"""
MCP Server implementation for MDP using the official MCP SDK.

This module provides a server implementation that exposes MDP documents
through the Model Context Protocol (MCP).
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

from mcp.server import stdio
from mcp.server.fastmcp import FastMCP

from mdp.collection import Collection
from mdp.document import Document

# Create server instance
server = FastMCP("MDP Document Server")

# Initialize collection
collection = Collection(name="default")

@server.resource("mcp://api/metadata")
def get_api_metadata() -> str:
    """Get API metadata."""
    return json.dumps({
        "title": "MDP Document API",
        "description": "API for managing Markdown Data Pack (MDP) documents",
        "version": "1.0.0",
    })

@server.resource("mdp://docs/{doc_id}")
def read_document(doc_id: str) -> str:
    """Read a document by ID."""
    doc = collection.get_document(doc_id)
    if not doc:
        raise ValueError(f"Document not found: {doc_id}")
    return doc.to_text()

@server.resource("mdp://collections/list") 
def list_documents() -> str:
    """List all documents."""
    return json.dumps([doc.metadata for doc in collection.documents])

@server.tool()
def create_document(content: str) -> Dict[str, str]:
    """Create a new document."""
    doc = Document.from_text(content)
    if "uuid" not in doc.metadata:
        doc.generate_uuid()
    collection.add_document(doc)
    doc_id = doc.metadata['uuid']
    return {"doc_id": doc_id, "message": f"Document created: {doc_id}"}

@server.tool()
def update_document(doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Update a document by ID."""
    updated_doc = Document.from_text(content)
    if "uuid" in updated_doc.metadata and updated_doc.metadata["uuid"] != doc_id:
        raise ValueError("Document UUID cannot be changed")
    updated_doc.metadata["uuid"] = doc_id
    collection.update_document(updated_doc)
    return {"message": f"Document updated: {doc_id}"}

@server.tool()
def delete_document(doc_id: str) -> Dict[str, str]:
    """Delete a document by ID."""
    collection.remove_document(doc_id)
    return {"message": f"Document deleted: {doc_id}"}

@server.tool()
def search_documents(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search for documents matching a query."""
    results = []
    for doc in collection.documents:
        if query.lower() in doc.content.lower() or \
           any(query.lower() in str(v).lower() for v in doc.metadata.values()):
            results.append(doc.metadata)
    return results[:max_results]

@server.tool()
def fetch_context(query: str, doc_ids: Optional[List[str]] = None, max_results: int = 5) -> str:
    """Fetch document context for a query."""
    relevant_docs = []
    for doc in collection.documents:
        if query.lower() in doc.content.lower():
            relevant_docs.append(doc)
            
    if relevant_docs:
        context = "\n\n".join([
            f"# {doc.metadata.get('title', 'Untitled')}\n\n{doc.content}"
            for doc in relevant_docs[:max_results]
        ])
    else:
        context = "No relevant documents found."
    return context

async def run():
    """Run the MCP server using stdio transport."""
    async with stdio.stdio_server() as (read_stream, write_stream):
        async for message in read_stream:
            response = await server.process_message(message)
            await write_stream.send(response)

if __name__ == "__main__":
    asyncio.run(run()) 