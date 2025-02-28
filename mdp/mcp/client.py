"""
MCP Client implementation for MDP using the official MCP SDK.

This module provides client functionality for interacting with MCP servers
to perform document operations.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.models import StdioServerParameters

from ..document import Document


class MCPClient:
    """
    Client for interacting with MDP MCP servers.
    
    This class provides methods for performing document operations using
    the Model Context Protocol.
    """
    
    def __init__(
        self,
        server_path: str,
        server_args: Optional[List[str]] = None,
        server_env: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the MCP client.
        
        Args:
            server_path: Path to the MCP server script
            server_args: Optional arguments to pass to the server
            server_env: Optional environment variables for the server
        """
        self.server_parameters = StdioServerParameters(
            command="python",
            args=[server_path] + (server_args or []),
            env=server_env
        )
        self.session = None
        self._api_metadata = None
    
    async def __aenter__(self):
        """
        Start the client session.
        
        Returns:
            The client instance
        """
        read_stream, write_stream = await stdio_client(self.server_parameters).__aenter__()
        self.session = await ClientSession(read_stream, write_stream).__aenter__()
        await self.session.initialize()
        
        # Fetch server API documentation if available
        try:
            self._api_metadata = await self.get_api_metadata()
        except Exception:
            self._api_metadata = None
            
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Close the client session.
        """
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
            self.session = None
    
    async def get_api_metadata(self) -> Dict[str, Any]:
        """
        Get API metadata from the server.
        
        Returns:
            API metadata including documentation
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
            
        # Try to fetch API metadata using MCP convention
        try:
            metadata_str, _ = await self.session.read_resource("mcp://api/metadata")
            return json.loads(metadata_str)
        except Exception:
            # If not available, return empty metadata
            return {}
    
    async def get_tool_documentation(self, tool_name: Optional[str] = None) -> str:
        """
        Get documentation for tools available on the server.
        
        Args:
            tool_name: Optional name of specific tool to get docs for
            
        Returns:
            Documentation in markdown format
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
            
        try:
            if tool_name:
                doc_str, _ = await self.session.read_resource(f"mcp://api/tools/{tool_name}/docs")
            else:
                doc_str, _ = await self.session.read_resource("mcp://api/tools/docs")
            return doc_str
        except Exception as e:
            return f"Documentation not available: {str(e)}"
    
    async def create_document(self, document: Document) -> Dict[str, str]:
        """
        Create a new document.
        
        This method creates a new MDP document on the server and returns
        information about the created document including its unique ID.
        
        Args:
            document: The document to create
            
        Returns:
            Response from the server containing doc_id and status message
            
        Example:
            ```python
            doc = Document(
                content="This is a sample document.",
                metadata={"title": "Sample Document", "tags": ["example"]}
            )
            result = await client.create_document(doc)
            doc_id = result["doc_id"]
            ```
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        result = await self.session.call_tool(
            "create_document",
            arguments={
                "content": document.content,
                "metadata": document.metadata
            }
        )
        
        # Handle different return types for backward compatibility
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            # Parse legacy format: "Document created: {uuid}"
            parts = result.split(": ", 1)
            if len(parts) == 2:
                return {"doc_id": parts[1], "message": result}
            return {"message": result}
        
        return {"message": str(result)}
    
    async def read_document(self, document_id: str) -> Document:
        """
        Read a document by ID.
        
        This method retrieves a document from the server by its unique ID.
        It returns a complete Document object with content and metadata.
        
        Args:
            document_id: ID of the document to read
            
        Returns:
            The document
            
        Example:
            ```python
            doc = await client.read_document("123e4567-e89b-12d3-a456-426614174000")
            print(f"Title: {doc.metadata.get('title')}")
            print(f"Content: {doc.content}")
            ```
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        # Get document content
        content, _ = await self.session.read_resource(f"mdp://docs/{document_id}")
        
        # Get document metadata
        metadata_str, _ = await self.session.read_resource(f"mdp://docs/{document_id}/metadata")
        
        # Parse metadata from string or JSON
        metadata = {}
        if metadata_str.strip().startswith("{"):
            # Try to parse as JSON
            try:
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                # Fall back to line parsing
                metadata = self._parse_metadata_from_text(metadata_str)
        else:
            metadata = self._parse_metadata_from_text(metadata_str)
        
        return Document(content=content, metadata=metadata)
    
    def _parse_metadata_from_text(self, text: str) -> Dict[str, Any]:
        """
        Parse metadata from text format.
        
        Args:
            text: Metadata text in key: value format
            
        Returns:
            Parsed metadata dictionary
        """
        metadata = {}
        for line in text.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(":", 1)
            if len(parts) == 2:
                key, value = parts
                metadata[key.strip()] = value.strip()
        return metadata
    
    async def update_document(self, document_id: str, document: Document) -> Dict[str, str]:
        """
        Update a document.
        
        This method updates an existing document on the server with new
        content and/or metadata.
        
        Args:
            document_id: ID of the document to update
            document: The updated document
            
        Returns:
            Response from the server
            
        Example:
            ```python
            doc = await client.read_document("123e4567-e89b-12d3-a456-426614174000")
            doc.content += "\nAdditional content."
            doc.metadata["status"] = "updated"
            result = await client.update_document("123e4567-e89b-12d3-a456-426614174000", doc)
            ```
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        result = await self.session.call_tool(
            "update_document",
            arguments={
                "doc_id": document_id,
                "content": document.content,
                "metadata": document.metadata
            }
        )
        
        # Handle different return types for backward compatibility
        if isinstance(result, dict):
            return result
        return {"message": str(result)}
    
    async def delete_document(self, document_id: str) -> Dict[str, str]:
        """
        Delete a document.
        
        This method permanently removes a document from the server.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            Response from the server
            
        Example:
            ```python
            result = await client.delete_document("123e4567-e89b-12d3-a456-426614174000")
            print(result["message"]) # "Document deleted: 123e4567-e89b-12d3-a456-426614174000"
            ```
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        result = await self.session.call_tool(
            "delete_document",
            arguments={
                "doc_id": document_id
            }
        )
        
        # Handle different return types for backward compatibility
        if isinstance(result, dict):
            return result
        return {"message": str(result)}
    
    async def search_documents(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for documents.
        
        This method searches the document collection for documents that match
        the specified query string. The search covers both content and metadata.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of document metadata matching the query
            
        Example:
            ```python
            results = await client.search_documents("important topic", max_results=5)
            for doc in results:
                print(f"Found: {doc.get('title')} ({doc.get('uuid')})")
            ```
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        result = await self.session.call_tool(
            "search_documents",
            arguments={
                "query": query,
                "max_results": max_results
            }
        )
        
        # Handle different return types
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return [{"message": result}]
        
        return [{"message": str(result)}]
    
    async def fetch_context(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        max_results: int = 5
    ) -> str:
        """
        Fetch context for a query.
        
        This method retrieves relevant document content that matches the query.
        It's especially useful for AI applications that need contextual information.
        
        Args:
            query: The query to fetch context for
            document_ids: Optional list of document IDs to search within
            max_results: Maximum number of results to return
            
        Returns:
            Context from relevant documents
            
        Example:
            ```python
            context = await client.fetch_context("how to implement feature X", max_results=3)
            print(context) # Returns content from documents that match the query
            ```
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        args = {
            "query": query,
            "max_results": max_results
        }
        
        if document_ids:
            args["doc_ids"] = document_ids
        
        result = await self.session.call_tool(
            "fetch_context",
            arguments=args
        )
        
        return result
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents.
        
        This method retrieves a list of all documents in the collection.
        Each document is represented by its metadata.
        
        Returns:
            List of document metadata
            
        Example:
            ```python
            docs = await client.list_documents()
            print(f"Found {len(docs)} documents:")
            for doc in docs:
                print(f"- {doc.get('title')} ({doc.get('uuid')})")
            ```
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        content, _ = await self.session.read_resource("mdp://collections/list")
        
        # Try to parse as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If not JSON, return as list with single item
            return [{"content": content}]


# Synchronous wrapper for easier usage
class MCPClientSync:
    """
    Synchronous wrapper around the async MCP client.
    
    This class provides a synchronous interface to the async client,
    making it easier to use in non-async code.
    """
    
    def __init__(
        self,
        server_path: str,
        server_args: Optional[List[str]] = None,
        server_env: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the sync client.
        
        Args:
            server_path: Path to the MCP server script
            server_args: Optional arguments to pass to the server
            server_env: Optional environment variables for the server
        """
        self.client = MCPClient(server_path, server_args, server_env)
        self._loop = None
    
    def _ensure_loop(self):
        """Ensure we have an event loop."""
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
    
    def __enter__(self):
        """Start the client session."""
        self._ensure_loop()
        self._enter_future = asyncio.run_coroutine_threadsafe(
            self.client.__aenter__(), self._loop
        )
        self._enter_future.result()  # Wait for completion
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the client session."""
        exit_future = asyncio.run_coroutine_threadsafe(
            self.client.__aexit__(exc_type, exc_val, exc_tb), self._loop
        )
        exit_future.result()  # Wait for completion
    
    def _run_async(self, coroutine):
        """Run an async function synchronously."""
        self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        return future.result()
    
    def create_document(self, document: Document) -> str:
        """Create a new document."""
        return self._run_async(self.client.create_document(document))
    
    def read_document(self, document_id: str) -> Document:
        """Read a document by ID."""
        return self._run_async(self.client.read_document(document_id))
    
    def update_document(self, document_id: str, document: Document) -> str:
        """Update a document."""
        return self._run_async(self.client.update_document(document_id, document))
    
    def delete_document(self, document_id: str) -> str:
        """Delete a document."""
        return self._run_async(self.client.delete_document(document_id))
    
    def search_documents(self, query: str, max_results: int = 10) -> str:
        """Search for documents."""
        return self._run_async(self.client.search_documents(query, max_results))
    
    def fetch_context(self, query: str, document_ids: Optional[List[str]] = None, max_results: int = 5) -> str:
        """Fetch context for a query."""
        return self._run_async(self.client.fetch_context(query, document_ids, max_results))
    
    def list_documents(self) -> str:
        """List all documents."""
        return self._run_async(self.client.list_documents()) 