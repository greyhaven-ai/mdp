"""
Document manager for the MDP Language Server.

This module handles the management of document content, parsing, and tracking changes
for the LSP implementation.
"""

import logging
import os
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path

from ..core import MDPFile, extract_metadata
from ..lint import MDPLinter, LintResult, LintError
from ..document import Document

logger = logging.getLogger("mdp-lsp.documents")


class TextDocumentItem:
    """Represents a text document item in the workspace."""
    
    def __init__(
        self,
        uri: str,
        language_id: str,
        version: int,
        text: str
    ):
        self.uri = uri
        self.language_id = language_id
        self.version = version
        self.text = text
        self.path = uri_to_path(uri)
        self.mdp_file = None
        self.lint_result = None
        self.parse()
    
    def parse(self) -> bool:
        """
        Parse the document text as an MDP file.
        
        Returns:
            bool: True if parsing was successful, False otherwise
        """
        try:
            metadata, content = extract_metadata(self.text)
            self.mdp_file = MDPFile(metadata, content, self.path)
            return True
        except Exception as e:
            logger.error(f"Error parsing MDP file: {e}")
            return False
    
    def update(self, changes: List[Dict[str, Any]], version: int):
        """
        Update the document with changes.
        
        Args:
            changes: List of text document content changes
            version: New document version
        """
        self.version = version
        
        # Apply changes
        for change in changes:
            if "range" in change:
                # Incremental update (not implemented yet)
                logger.warning("Incremental updates not implemented, using full text instead")
                self.text = change["text"]
            else:
                # Full update
                self.text = change["text"]
        
        # Re-parse
        self.parse()
    
    def lint(self) -> LintResult:
        """
        Lint the document.
        
        Returns:
            LintResult: The result of linting
        """
        linter = MDPLinter()
        self.lint_result = linter.lint_string(self.text, file_path=self.path)
        return self.lint_result


class MDPDocumentManager:
    """Manages all open documents in the LSP server."""
    
    def __init__(self):
        self.documents: Dict[str, TextDocumentItem] = {}
    
    def add_document(self, uri: str, language_id: str, version: int, text: str):
        """
        Add a document to the manager.
        
        Args:
            uri: Document URI
            language_id: Document language ID
            version: Document version
            text: Document text content
        """
        document = TextDocumentItem(uri, language_id, version, text)
        self.documents[uri] = document
        return document
    
    def update_document(self, uri: str, changes: List[Dict[str, Any]], version: int):
        """
        Update a document in the manager.
        
        Args:
            uri: Document URI
            changes: List of text document content changes
            version: New document version
        """
        if uri in self.documents:
            self.documents[uri].update(changes, version)
            return self.documents[uri]
        return None
    
    def remove_document(self, uri: str):
        """
        Remove a document from the manager.
        
        Args:
            uri: Document URI
        """
        if uri in self.documents:
            del self.documents[uri]
    
    def get_document(self, uri: str) -> Optional[TextDocumentItem]:
        """
        Get a document from the manager.
        
        Args:
            uri: Document URI
        
        Returns:
            Optional[TextDocumentItem]: The document if found, None otherwise
        """
        return self.documents.get(uri)
    
    def lint_document(self, uri: str) -> Optional[LintResult]:
        """
        Lint a document.
        
        Args:
            uri: Document URI
        
        Returns:
            Optional[LintResult]: The lint result if the document exists, None otherwise
        """
        document = self.get_document(uri)
        if document:
            return document.lint()
        return None
    
    def lint_all_documents(self) -> Dict[str, LintResult]:
        """
        Lint all documents.
        
        Returns:
            Dict[str, LintResult]: Dictionary mapping URIs to lint results
        """
        results = {}
        for uri, document in self.documents.items():
            results[uri] = document.lint()
        return results


def uri_to_path(uri: str) -> str:
    """
    Convert a URI to a file path.
    
    Args:
        uri: The URI to convert
    
    Returns:
        str: The file path
    """
    if uri.startswith("file://"):
        # Remove file:// prefix
        path = uri[7:]
        
        # Handle Windows paths
        if path.startswith("/") and ":" in path:
            # Remove leading slash for Windows paths
            path = path[1:]
        
        return path
    
    return uri


def path_to_uri(path: str) -> str:
    """
    Convert a file path to a URI.
    
    Args:
        path: The file path to convert
    
    Returns:
        str: The URI
    """
    path = os.path.abspath(path)
    
    # Handle Windows paths
    if os.name == "nt":
        path = "/" + path.replace("\\", "/")
    
    return f"file://{path}" 