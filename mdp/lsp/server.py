"""
MDP Language Server implementation.

This module implements the Language Server Protocol for MDP files,
enabling rich editing features in compatible editors and IDEs.
"""

import logging
import os
from typing import Dict, List, Optional, Set, Any

from .documents import MDPDocumentManager, uri_to_path
from .features import (
    get_diagnostics_from_lint_result,
    get_yaml_schema_completions,
    get_markdown_completions,
    get_hover_information,
    get_document_symbols
)
from ..commands.format import format_string

logger = logging.getLogger("mdp-lsp.server")


class MDPLanguageServer:
    """
    Language Server implementation for MDP files.
    
    This server provides language features such as diagnostics, completions, hover,
    document symbols, code formatting, and more, enabling rich editing capabilities
    in compatible editors and IDEs.
    """
    
    def __init__(self):
        self.document_manager = MDPDocumentManager()
        self.client_capabilities = {}
        self.server_capabilities = {
            "textDocumentSync": {
                "openClose": True,
                "change": 1  # 1 = Full, 2 = Incremental
            },
            "completionProvider": {
                "resolveProvider": False,
                "triggerCharacters": [":", "-", " ", "[", "."]
            },
            "hoverProvider": True,
            "documentSymbolProvider": True,
            "documentFormattingProvider": True
        }
        self.workspace_folders = []
    
    def on_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the initialize request.
        
        Args:
            params: Initialize request parameters
        
        Returns:
            Dict[str, Any]: Initialize result
        """
        self.client_capabilities = params.get("capabilities", {})
        
        if "workspaceFolders" in params:
            self.workspace_folders = params["workspaceFolders"]
        
        return {
            "capabilities": self.server_capabilities,
            "serverInfo": {
                "name": "MDP Language Server",
                "version": "0.1.0"
            }
        }
    
    def on_initialized(self, params: Dict[str, Any]) -> None:
        """
        Handle the initialized notification.
        
        Args:
            params: Initialized notification parameters
        """
        logger.info("MDP Language Server initialized")
    
    def on_shutdown(self, params: Dict[str, Any]) -> None:
        """
        Handle the shutdown request.
        
        Args:
            params: Shutdown request parameters
        
        Returns:
            None
        """
        logger.info("MDP Language Server shutting down")
        return None
    
    def on_textDocument_didOpen(self, params: Dict[str, Any]) -> None:
        """
        Handle the textDocument/didOpen notification.
        
        Args:
            params: Text document open notification parameters
        """
        text_document = params["textDocument"]
        uri = text_document["uri"]
        language_id = text_document["languageId"]
        version = text_document["version"]
        text = text_document["text"]
        
        # Add the document to the manager
        document = self.document_manager.add_document(uri, language_id, version, text)
        
        # Validate the document
        self._validate_document(uri)
    
    def on_textDocument_didChange(self, params: Dict[str, Any]) -> None:
        """
        Handle the textDocument/didChange notification.
        
        Args:
            params: Text document change notification parameters
        """
        text_document = params["textDocument"]
        uri = text_document["uri"]
        version = text_document["version"]
        changes = params["contentChanges"]
        
        # Update the document
        document = self.document_manager.update_document(uri, changes, version)
        
        # Validate the document
        self._validate_document(uri)
    
    def on_textDocument_didClose(self, params: Dict[str, Any]) -> None:
        """
        Handle the textDocument/didClose notification.
        
        Args:
            params: Text document close notification parameters
        """
        text_document = params["textDocument"]
        uri = text_document["uri"]
        
        # Remove the document from the manager
        self.document_manager.remove_document(uri)
    
    def on_textDocument_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the textDocument/completion request.
        
        Args:
            params: Completion request parameters
        
        Returns:
            Dict[str, Any]: Completion result
        """
        uri = params["textDocument"]["uri"]
        position = params["position"]
        
        # Get the document
        document = self.document_manager.get_document(uri)
        if not document:
            return {"items": []}
        
        # Get completions for YAML
        yaml_completions = get_yaml_schema_completions(document.text, position)
        
        # Get completions for Markdown
        markdown_completions = get_markdown_completions(document.text, position)
        
        # Combine completions
        completions = yaml_completions + markdown_completions
        
        return {"items": completions}
    
    def on_textDocument_hover(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle the textDocument/hover request.
        
        Args:
            params: Hover request parameters
        
        Returns:
            Optional[Dict[str, Any]]: Hover result
        """
        uri = params["textDocument"]["uri"]
        position = params["position"]
        
        # Get the document
        document = self.document_manager.get_document(uri)
        if not document:
            return None
        
        # Get hover information
        hover = get_hover_information(document.text, position)
        return hover
    
    def on_textDocument_documentSymbol(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Handle the textDocument/documentSymbol request.
        
        Args:
            params: Document symbol request parameters
        
        Returns:
            List[Dict[str, Any]]: Document symbol result
        """
        uri = params["textDocument"]["uri"]
        
        # Get the document
        document = self.document_manager.get_document(uri)
        if not document:
            return []
        
        # Get document symbols
        symbols = get_document_symbols(document.text)
        
        # Fill in URI
        for symbol in symbols:
            symbol["location"]["uri"] = uri
        
        return symbols
    
    def on_textDocument_formatting(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Handle the textDocument/formatting request.
        
        Args:
            params: Formatting request parameters
        
        Returns:
            List[Dict[str, Any]]: Formatting result
        """
        uri = params["textDocument"]["uri"]
        options = params.get("options", {})
        
        # Get the document
        document = self.document_manager.get_document(uri)
        if not document:
            return []
        
        try:
            # Format the document
            formatted_text = format_string(
                document.text,
                sort_tags=True,
                normalize_headings=True,
                wrap_content=80,
                wrap_metadata=60,
                metadata_order=None
            )
            
            # If there are no changes, return empty result
            if formatted_text == document.text:
                return []
            
            # Create a full document edit
            return [
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": document.text.count('\n'), "character": 0}
                    },
                    "newText": formatted_text
                }
            ]
        except Exception as e:
            logger.error(f"Error formatting document: {e}")
            return []
    
    def _validate_document(self, uri: str) -> None:
        """
        Validate a document and publish diagnostics.
        
        Args:
            uri: Document URI
        """
        # Lint the document
        lint_result = self.document_manager.lint_document(uri)
        
        # Convert lint result to LSP diagnostics
        diagnostics = get_diagnostics_from_lint_result(lint_result)
        
        # Publish diagnostics
        self._publish_diagnostics(uri, diagnostics)
    
    def _publish_diagnostics(self, uri: str, diagnostics: List[Dict[str, Any]]) -> None:
        """
        Publish diagnostics for a document.
        
        Args:
            uri: Document URI
            diagnostics: List of diagnostics
        """
        # In a real server, we would send a notification to the client
        # For now, we'll just log it
        logger.info(f"Publishing {len(diagnostics)} diagnostics for {uri}") 