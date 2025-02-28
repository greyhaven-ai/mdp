"""
Collection management for MDP documents.

This module provides the Collection class for working with groups of related documents.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Iterator, Callable
import fnmatch

from .document import Document
from .utils import find_mdp_files, get_collection_hierarchy
from .metadata import create_collection_metadata, generate_uuid


class Collection:
    """
    A collection of related documents.
    
    This class provides functionality for working with groups of documents,
    making it easy to manage collections, apply operations to multiple
    documents, and maintain relationships between them.
    
    Attributes:
        name: The name of the collection
        documents: The list of documents in the collection
        metadata: Optional metadata for the collection
    """
    
    def __init__(
        self,
        name: str,
        documents: Optional[List[Document]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new Collection.
        
        Args:
            name: The name of the collection
            documents: Optional list of documents to include
            metadata: Optional metadata for the collection
        """
        self.name = name
        self.documents = documents or []
        
        # Initialize collection metadata
        if metadata is None:
            self.metadata = create_collection_metadata(
                collection_name=name,
                collection_id=generate_uuid()
            )
        else:
            self.metadata = metadata
            # Ensure the collection has an ID
            if "collection_id" not in self.metadata:
                self.metadata["collection_id"] = generate_uuid()
    
    @classmethod
    def from_directory(
        cls,
        directory: Union[str, Path],
        name: Optional[str] = None,
        recursive: bool = True,
        file_pattern: str = "*.mdp"
    ) -> "Collection":
        """
        Create a Collection from documents in a directory.
        
        Args:
            directory: The directory to search for documents
            name: The name of the collection (defaults to directory name)
            recursive: Whether to search recursively
            file_pattern: The file pattern to match
            
        Returns:
            A new Collection instance with the documents found
        """
        directory_path = Path(directory)
        
        # Use directory name as collection name if not provided
        if name is None:
            name = directory_path.name
        
        # Find all MDP files in the directory
        mdp_paths = find_mdp_files(
            directory_path,
            recursive=recursive
        )
        
        # Filter for the file pattern if specified
        if file_pattern != "*.mdp":
            mdp_paths = [p for p in mdp_paths if fnmatch.fnmatch(p.name, file_pattern)]
        
        # Load each file as a Document
        documents = []
        for path in mdp_paths:
            try:
                doc = Document.from_file(path)
                documents.append(doc)
            except (ValueError, FileNotFoundError) as e:
                # Skip invalid files but maybe log the error
                print(f"Warning: Could not load {path}: {e}")
        
        return cls(name=name, documents=documents)
    
    def add_document(self, document: Document) -> "Collection":
        """
        Add a document to the collection.
        
        Args:
            document: The document to add
            
        Returns:
            The Collection instance for method chaining
        """
        # Add collection information to the document metadata
        document.metadata["collection"] = self.name
        document.metadata["collection_id"] = self.metadata["collection_id"]
        
        # Add to the list if not already present
        if document not in self.documents:
            self.documents.append(document)
        
        return self
    
    def add_documents(self, documents: List[Document]) -> "Collection":
        """
        Add multiple documents to the collection.
        
        Args:
            documents: The documents to add
            
        Returns:
            The Collection instance for method chaining
        """
        for document in documents:
            self.add_document(document)
        
        return self
    
    def remove_document(self, document: Document) -> "Collection":
        """
        Remove a document from the collection.
        
        Args:
            document: The document to remove
            
        Returns:
            The Collection instance for method chaining
        """
        if document in self.documents:
            self.documents.remove(document)
            
            # Remove collection information from the document metadata
            if "collection" in document.metadata:
                del document.metadata["collection"]
            if "collection_id" in document.metadata:
                del document.metadata["collection_id"]
        
        return self
    
    def get_document_by_title(self, title: str) -> Optional[Document]:
        """
        Find a document in the collection by its title.
        
        Args:
            title: The title to search for
            
        Returns:
            The matching Document or None if not found
        """
        for document in self.documents:
            if document.title == title:
                return document
        
        return None
    
    def get_document_by_uuid(self, uuid_str: str) -> Optional[Document]:
        """
        Find a document in the collection by its UUID.
        
        Args:
            uuid_str: The UUID to search for
            
        Returns:
            The matching Document or None if not found
        """
        for document in self.documents:
            if document.metadata.get("uuid") == uuid_str:
                return document
        
        return None
    
    def filter(self, predicate: Callable[[Document], bool]) -> List[Document]:
        """
        Filter documents using a predicate function.
        
        Args:
            predicate: A function that takes a Document and returns True if it should be included
            
        Returns:
            A list of documents that match the predicate
        """
        return [doc for doc in self.documents if predicate(doc)]
    
    def get_hierarchy(self) -> Dict[str, List[str]]:
        """
        Get the parent-child hierarchy of documents in the collection.
        
        Returns:
            A dictionary mapping parent document titles to lists of child document titles
        """
        # Create a map of document IDs to titles
        id_to_title = {}
        
        # First pass: build ID to title mapping
        for doc in self.documents:
            # Use UUID if available
            if "uuid" in doc.metadata:
                id_to_title[doc.metadata["uuid"]] = doc.title
            # Fall back to path
            elif doc.path:
                id_to_title[str(doc.path)] = doc.title
            # As a last resort, use URI
            elif "uri" in doc.metadata:
                id_to_title[doc.metadata["uri"]] = doc.title
            
        # Get the raw hierarchy of ID references
        raw_hierarchy = get_collection_hierarchy(
            [doc._mdp_file for doc in self.documents]
        )
        
        # Convert IDs to titles where possible
        hierarchy = {}
        for parent_id, child_ids in raw_hierarchy.items():
            parent_title = id_to_title.get(parent_id, parent_id)
            child_titles = [id_to_title.get(child_id, child_id) for child_id in child_ids]
            hierarchy[parent_title] = child_titles
        
        return hierarchy
    
    def link_documents_by_references(self) -> "Collection":
        """
        Automatically create relationships based on references in document content.
        
        This method scans document content for references to other documents in the
        collection (by title or explicit links) and creates relationships automatically.
        
        Returns:
            The Collection instance for method chaining
        """
        # Implementation would search for references in content
        # and create relationships between documents
        # This is a placeholder for now
        
        # For each document, check if it references other documents
        for source_doc in self.documents:
            for target_doc in self.documents:
                if source_doc is target_doc:
                    continue
                    
                # Simple check: does source content mention target title?
                if target_doc.title and target_doc.title in source_doc.content:
                    # Create a "reference" relationship
                    source_doc.add_relationship(
                        target_doc,
                        relationship_type="reference",
                        title=f"Reference to {target_doc.title}"
                    )
        
        return self
    
    def save_all(self, directory: Optional[Union[str, Path]] = None) -> "Collection":
        """
        Save all documents in the collection.
        
        Args:
            directory: Optional directory to save to (if None, uses each document's path)
            
        Returns:
            The Collection instance for method chaining
            
        Raises:
            ValueError: If directory is None and a document has no path
        """
        for doc in self.documents:
            if directory is not None:
                # Create a path within the specified directory
                dir_path = Path(directory)
                
                # If the document has a filename, use it
                if doc.path:
                    new_path = dir_path / doc.path.name
                else:
                    # Create a filename based on the title
                    safe_title = "".join(c if c.isalnum() else "_" for c in doc.title)
                    new_path = dir_path / f"{safe_title}.mdp"
                
                doc.save(new_path)
            else:
                # Save to the document's current path
                doc.save()
        
        return self
    
    def export(self, directory: Union[str, Path]) -> "Collection":
        """
        Export the collection to a directory.
        
        This creates a new directory with all documents and a collection metadata file.
        
        Args:
            directory: The directory to export to
            
        Returns:
            The Collection instance for method chaining
        """
        export_dir = Path(directory)
        os.makedirs(export_dir, exist_ok=True)
        
        # Save all documents
        self.save_all(export_dir)
        
        # Create a collection metadata file
        collection_meta = {
            "name": self.name,
            "collection_id": self.metadata["collection_id"],
            "document_count": len(self.documents),
            "documents": [
                {
                    "title": doc.title,
                    "uuid": doc.metadata.get("uuid", ""),
                    "file": doc.path.name if doc.path else ""
                }
                for doc in self.documents
            ]
        }
        
        # Create a collection info document
        collection_doc = Document.create(
            title=f"{self.name} - Collection Index",
            content=f"# {self.name}\n\n"
                    f"This is a collection of {len(self.documents)} documents.\n\n"
                    f"## Documents\n\n" +
                    "\n".join(f"- {doc.title}" for doc in self.documents),
            **collection_meta
        )
        
        # Save the collection info
        collection_doc.save(export_dir / "collection.mdp")
        
        return self
    
    def __len__(self) -> int:
        """Get the number of documents in the collection."""
        return len(self.documents)
    
    def __iter__(self) -> Iterator[Document]:
        """Iterate over the documents in the collection."""
        return iter(self.documents)
    
    def __getitem__(self, index: int) -> Document:
        """Get a document by index."""
        return self.documents[index] 