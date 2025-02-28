"""
MCP Server implementation for MDP using the official MCP SDK.

This module provides a server implementation that exposes MDP documents
through the Model Context Protocol (MCP).
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from fastmcp import FastMCP, MCPChunk, MCPContext
from pydantic import BaseModel, Field, create_model

from ..collection import Collection
from ..document import Document
from .llm_docs import get_server_documentation, get_tool_documentation, get_workflow_examples, get_documentation_markdown

# Schema imports for API documentation
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                          "docs", "specification", "mdp_schema.json")

def load_schema():
    """Load the MDP schema for API documentation."""
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, 'r') as f:
            return json.load(f)
    return {}

# Load schema for documentation
MDP_SCHEMA = load_schema()

# Define input/output models for MCP tools
class CreateDocumentInput(BaseModel):
    """Input model for document creation."""
    content: str = Field(..., description="The document content in MDP format")

class CreateDocumentOutput(BaseModel):
    """Output model for document creation."""
    doc_id: str = Field(..., description="The UUID of the created document")
    message: str = Field(..., description="Status message")

class UpdateDocumentInput(BaseModel):
    """Input model for document update."""
    doc_id: str = Field(..., description="Document ID to update")
    content: str = Field(..., description="The updated document content in MDP format")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")

class DocumentResponse(BaseModel):
    """Response model for document operations."""
    message: str = Field(..., description="Status message")
    
class SearchQuery(BaseModel):
    """Input model for search queries."""
    query: str = Field(..., description="Search term")
    max_results: int = Field(10, description="Maximum number of results to return")

class ContextQuery(BaseModel):
    """Input model for context queries."""
    query: str = Field(..., description="The query to fetch context for")
    doc_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to search within")
    max_results: int = Field(5, description="Maximum number of results to return")


class MDPContext:
    """Context for the MDP MCP server."""
    
    def __init__(self, collection: Collection):
        """
        Initialize with a document collection.
        
        Args:
            collection: The collection of documents to serve
        """
        self.collection = collection


@asynccontextmanager
async def mdp_lifespan(server: FastMCP) -> AsyncIterator[MDPContext]:
    """
    Manage the lifecycle of the MDP MCP server.
    
    This context manager initializes the document collection when the server
    starts and cleans up resources when it stops.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        The MDPContext instance with the initialized collection
    """
    # Initialize document collection
    collection = Collection()
    
    # Yield the context to the server
    yield MDPContext(collection=collection)
    
    # Cleanup on server shutdown


def create_mcp_server(name: str = "MDP Document Server") -> FastMCP:
    """
    Create and configure an MCP server for MDP.
    
    Args:
        name: The name of the server
        
    Returns:
        A configured FastMCP server instance
    """
    # Create a new MCP server
    server = FastMCP(name=name, lifespan=mdp_lifespan)
    
    # Add API metadata
    server.api_metadata = {
        "title": "MDP Document API",
        "description": "API for managing Markdown Data Pack (MDP) documents",
        "version": "1.0.0",
        "documentation_url": "https://github.com/greyhaven-ai/mdp",
        "schemas": {
            "Document": MDP_SCHEMA
        }
    }
    
    # Add documentation endpoints for LLMs
    @server.resource(
        path="mcp://api/metadata",
        description="Get API metadata and documentation",
        examples=[{
            "path": "mcp://api/metadata",
            "result": json.dumps(server.api_metadata)
        }]
    )
    async def get_api_metadata(ctx: MCPContext) -> str:
        """
        Get API metadata.
        
        Args:
            ctx: The MCP context
            
        Returns:
            API metadata as JSON
        """
        return json.dumps(server.api_metadata)
    
    @server.resource(
        path="mcp://api/tools/docs",
        description="Get documentation for all tools",
        examples=[{
            "path": "mcp://api/tools/docs",
            "result": "# MDP Document Server\n\nThis MCP server provides access to MDP documents..."
        }]
    )
    async def get_tools_documentation(ctx: MCPContext) -> str:
        """
        Get documentation for all tools.
        
        Args:
            ctx: The MCP context
            
        Returns:
            Tool documentation in markdown format
        """
        return get_documentation_markdown()
    
    @server.resource(
        path="mcp://api/tools/{tool_name}/docs",
        description="Get documentation for a specific tool",
        examples=[{
            "path": "mcp://api/tools/create_document/docs",
            "result": "### create_document\n\nCreate a new MDP document\n\n**Input:**\n..."
        }]
    )
    async def get_tool_documentation(ctx: MCPContext, tool_name: str) -> str:
        """
        Get documentation for a specific tool.
        
        Args:
            ctx: The MCP context
            tool_name: Name of the tool to get docs for
            
        Returns:
            Tool documentation in markdown format
        """
        tool_doc = get_tool_documentation(tool_name)
        if not tool_doc:
            return f"Documentation not found for tool: {tool_name}"
            
        doc = [f"### {tool_name}\n"]
        doc.append(f"{tool_doc['description']}\n")
        
        doc.append("**Input:**\n")
        doc.append("```json\n")
        doc.append(json.dumps(tool_doc["input_schema"], indent=2))
        doc.append("\n```\n")
        
        doc.append("**Output:**\n")
        doc.append("```json\n")
        doc.append(json.dumps(tool_doc["output_schema"], indent=2))
        doc.append("\n```\n")
        
        doc.append("**Example:**\n")
        if tool_doc["examples"]:
            example = tool_doc["examples"][0]
            doc.append("Input:\n")
            doc.append("```json\n")
            doc.append(json.dumps(example["input"], indent=2))
            doc.append("\n```\n")
            doc.append("Output:\n")
            doc.append("```json\n")
            doc.append(json.dumps(example["output"], indent=2))
            doc.append("\n```\n")
        
        return "\n".join(doc)
    
    @server.resource(
        path="mcp://api/examples",
        description="Get examples of LLM interactions with the API",
        examples=[{
            "path": "mcp://api/examples",
            "result": "# Example Workflows\n\n## Creating and retrieving a document\n..."
        }]
    )
    async def get_workflow_examples(ctx: MCPContext) -> str:
        """
        Get examples of LLM workflows.
        
        Args:
            ctx: The MCP context
            
        Returns:
            Workflow examples in markdown format
        """
        examples = get_workflow_examples()
        
        doc = ["# Example Workflows\n"]
        
        for example in examples:
            doc.append(f"## {example['title']}\n")
            
            for i, step in enumerate(example['steps']):
                doc.append(f"### Step {i+1}\n")
                doc.append(f"**User:** {step['user']}\n\n")
                
                if 'llm_thought' in step:
                    doc.append(f"**LLM Thought:** {step['llm_thought']}\n\n")
                
                if 'llm_action' in step:
                    doc.append(f"**Action:** {step['llm_action']}\n\n")
                    doc.append("**Input:**\n")
                    doc.append("```json\n")
                    doc.append(json.dumps(step['llm_action_input'], indent=2))
                    doc.append("\n```\n\n")
                    
                if 'llm_actions' in step:
                    doc.append("**Actions:**\n\n")
                    for action in step['llm_actions']:
                        doc.append(f"- {action['action']}\n")
                        doc.append("  Input:\n")
                        doc.append("  ```json\n")
                        doc.append("  " + json.dumps(action['input'], indent=2).replace("\n", "\n  "))
                        doc.append("\n  ```\n\n")
                
                if 'action_result' in step:
                    doc.append("**Result:**\n")
                    doc.append("```json\n")
                    doc.append(json.dumps(step['action_result'], indent=2))
                    doc.append("\n```\n\n")
                
                doc.append(f"**LLM Response:** {step['llm_response']}\n\n")
                doc.append("---\n\n")
        
        return "\n".join(doc)
    
    # Register document management endpoints with enhanced documentation
    @server.tool(
        name="create_document",
        description="Create a new MDP document",
        input_schema=CreateDocumentInput,
        output_schema=CreateDocumentOutput,
        examples=[{
            "input": {"content": "---\ntitle: Example Document\ntags: [example, documentation]\n---\n\nThis is an example document."},
            "output": {"doc_id": "123e4567-e89b-12d3-a456-426614174000", "message": "Document created: 123e4567-e89b-12d3-a456-426614174000"}
        }]
    )
    async def create_document(ctx: MCPContext, content: str) -> Dict[str, str]:
        """
        Create a new document.
        
        Args:
            ctx: The MCP context
            text: The document content in MDP format
            
        Returns:
            A success message with the document ID
        """
        mdp_ctx: MDPContext = ctx.request_context.lifespan_context
        
        # Parse MDP content
        doc = Document.from_text(content)
        
        # Generate UUID if not present
        if "uuid" not in doc.metadata:
            doc.generate_uuid()
            
        # Add to collection
        mdp_ctx.collection.add_document(doc)
        
        doc_id = doc.metadata['uuid']
        return {"doc_id": doc_id, "message": f"Document created: {doc_id}"}
    
    @server.resource(
        path="mdp://docs/{doc_id}",
        description="Get the content of a document by ID",
        examples=[{
            "path": "mdp://docs/123e4567-e89b-12d3-a456-426614174000",
            "result": "---\ntitle: Example Document\nuuid: 123e4567-e89b-12d3-a456-426614174000\n---\n\nThis is an example document."
        }]
    )
    async def read_document(ctx: MCPContext, doc_id: str) -> str:
        """
        Read a document by ID.
        
        Args:
            ctx: The MCP context
            doc_id: The document ID
            
        Returns:
            The document content in MDP format
        """
        mdp_ctx: MDPContext = ctx.request_context.lifespan_context
        
        # Find document in collection
        doc = mdp_ctx.collection.get_document(doc_id)
        if not doc:
            raise ValueError(f"Document not found: {doc_id}")
            
        # Return as MDP text
        return doc.to_text()
    
    @server.tool(
        name="update_document",
        description="Update an existing MDP document",
        input_schema=UpdateDocumentInput,
        output_schema=DocumentResponse,
        examples=[{
            "input": {
                "doc_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "---\ntitle: Updated Document\ntags: [example, updated]\n---\n\nThis document has been updated."
            },
            "output": {"message": "Document updated: 123e4567-e89b-12d3-a456-426614174000"}
        }]
    )
    async def update_document(ctx: MCPContext, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Update a document by ID.
        
        Args:
            ctx: The MCP context
            doc_id: The document ID
            text: The updated document content in MDP format
            
        Returns:
            A success message
        """
        mdp_ctx: MDPContext = ctx.request_context.lifespan_context
        
        # Parse MDP content
        updated_doc = Document.from_text(content)
        
        # Ensure the UUID matches
        if "uuid" in updated_doc.metadata and updated_doc.metadata["uuid"] != doc_id:
            raise ValueError("Document UUID cannot be changed")
            
        updated_doc.metadata["uuid"] = doc_id
        
        # Update in collection
        mdp_ctx.collection.update_document(updated_doc)
        
        return {"message": f"Document updated: {doc_id}"}
    
    @server.tool(
        name="delete_document",
        description="Delete an MDP document by ID",
        input_schema={"type": "object", "properties": {"doc_id": {"type": "string", "description": "ID of the document to delete"}}},
        output_schema=DocumentResponse,
        examples=[{
            "input": {"doc_id": "123e4567-e89b-12d3-a456-426614174000"},
            "output": {"message": "Document deleted: 123e4567-e89b-12d3-a456-426614174000"}
        }]
    )
    async def delete_document(ctx: MCPContext, doc_id: str) -> Dict[str, str]:
        """
        Delete a document by ID.
        
        Args:
            ctx: The MCP context
            doc_id: The document ID
            
        Returns:
            A success message
        """
        mdp_ctx: MDPContext = ctx.request_context.lifespan_context
        
        # Remove from collection
        mdp_ctx.collection.remove_document(doc_id)
        
        return {"message": f"Document deleted: {doc_id}"}
    
    @server.resource(
        path="mdp://collections/list",
        description="List all documents in the collection",
        examples=[{
            "path": "mdp://collections/list",
            "result": "[{\"title\": \"Example Document\", \"uuid\": \"123e4567-e89b-12d3-a456-426614174000\"}]"
        }]
    )
    async def list_documents(ctx: MCPContext) -> str:
        """
        List all documents.
        
        Args:
            ctx: The MCP context
            
        Returns:
            A list of document metadata
        """
        mdp_ctx: MDPContext = ctx.request_context.lifespan_context
        
        # Get all documents in the collection
        docs = mdp_ctx.collection.documents
        
        # Return metadata for each document
        return json.dumps([doc.metadata for doc in docs])
    
    @server.tool(
        name="search_documents",
        description="Search for documents matching a query string",
        input_schema=SearchQuery,
        output_schema={"type": "array", "items": {"$ref": "#/components/schemas/DocumentInfo"}},
        examples=[{
            "input": {"query": "example", "max_results": 5},
            "output": [{"title": "Example Document", "uuid": "123e4567-e89b-12d3-a456-426614174000"}]
        }]
    )
    async def search_documents(ctx: MCPContext, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents matching a query.
        
        Args:
            ctx: The MCP context
            query: The search query
            
        Returns:
            A list of matching document metadata
        """
        mdp_ctx: MDPContext = ctx.request_context.lifespan_context
        
        # Simple search implementation
        results = []
        for doc in mdp_ctx.collection.documents:
            if query.lower() in doc.content.lower() or \
               any(query.lower() in str(v).lower() for v in doc.metadata.values()):
                results.append(doc.metadata)
                
        return results[:max_results]
    
    @server.tool(
        name="fetch_context",
        description="Fetch relevant document context based on a query",
        input_schema=ContextQuery,
        output_schema={"type": "string", "description": "Relevant document content that matches the query"},
        examples=[{
            "input": {"query": "example documentation", "max_results": 3},
            "output": "# Example Document\n\nThis is an example document that explains documentation."
        }]
    )
    async def fetch_context(ctx: MCPContext, query: str, doc_ids: Optional[List[str]] = None, max_results: int = 5) -> MCPChunk:
        """
        Fetch document context for a query.
        
        Args:
            ctx: The MCP context
            query: The query to fetch context for
            
        Returns:
            Relevant document chunks as context
        """
        mdp_ctx: MDPContext = ctx.request_context.lifespan_context
        
        # Find relevant documents (simple implementation)
        relevant_docs = []
        for doc in mdp_ctx.collection.documents:
            if query.lower() in doc.content.lower():
                relevant_docs.append(doc)
                
        # Construct context from relevant documents
        if relevant_docs:
            context = "\n\n".join([
                f"# {doc.metadata.get('title', 'Untitled')}\n\n{doc.content}"
                for doc in relevant_docs[:max_results]  # Limit to top max_results matches
            ])
        else:
            context = "No relevant documents found."
            
        return MCPChunk(content=context)
    
    # Update system prompt to use our LLM-friendly documentation
    server.set_system_prompt(f"""
{get_server_documentation()}

Available tools:
1. create_document - Create a new document from MDP formatted text
   Example: create_document(content="---\\ntitle: New Document\\n---\\n\\nDocument content")

2. update_document - Update an existing document
   Example: update_document(doc_id="123e4567-e89b-12d3-a456-426614174000", content="---\\ntitle: Updated Doc\\n---\\n\\nNew content")

3. delete_document - Delete a document by ID
   Example: delete_document(doc_id="123e4567-e89b-12d3-a456-426614174000")

4. search_documents - Search for documents by query string
   Example: search_documents(query="important topic", max_results=5)

5. fetch_context - Get relevant document content for a query
   Example: fetch_context(query="how to implement feature X", max_results=3)

Available resources:
- mdp://docs/{doc_id} - Get document content
- mdp://docs/{doc_id}/metadata - Get document metadata
- mdp://collections/list - List all documents
- mcp://api/metadata - Get API metadata
- mcp://api/tools/docs - Get documentation for all tools
- mcp://api/tools/{tool_name}/docs - Get documentation for a specific tool
- mcp://api/examples - Get examples of LLM interactions with the API
""")
    
    return server


# For backward compatibility
mdp_mcp_server = create_mcp_server

if __name__ == "__main__":
    # When run directly, start the server
    mdp_mcp_server.run() 