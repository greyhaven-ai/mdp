"""
High-level interface for working with MDP documents.

This module provides the Document class, which is the primary interface for working with
Markdown Data Pack (MDP) files in a user-friendly way.
"""

import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Iterable, Tuple
import sys

from .core import MDPFile, read_mdp, write_mdp
from .metadata import (
    create_metadata,
    generate_uuid,
    create_relationship,
    add_relationship_to_metadata,
    DEFAULT_METADATA,
    VALID_RELATIONSHIP_TYPES,
    format_date,
    is_semantic_version,
    next_version
)
from .utils import (
    resolve_reference,
    find_related_documents
)


class Document:
    """
    A document with metadata and content.
    
    This class provides a high-level interface for working with MDP files,
    abstracting away the low-level details and providing convenient methods
    for common operations.
    
    Attributes:
        content: The markdown content of the document
        metadata: The metadata dictionary of the document
        path: Optional path to the file on disk
    """
    
    def __init__(
        self, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        path: Optional[Union[str, Path]] = None
    ):
        """
        Initialize a new Document.
        
        Args:
            content: The markdown content of the document
            metadata: The metadata dictionary (will be validated)
            path: Optional path to the file on disk
        """
        if metadata is None:
            metadata = create_metadata(title="Untitled Document")
        
        self._mdp_file = MDPFile(
            metadata=metadata,
            content=content,
            path=Path(path) if path else None
        )
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Document":
        """
        Create a Document from an MDP file.
        
        Args:
            path: Path to the MDP file
            
        Returns:
            A new Document instance
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not a valid MDP file
        """
        mdp_file = read_mdp(path)
        doc = cls(
            content=mdp_file.content,
            metadata=mdp_file.metadata,
            path=mdp_file.path
        )
        doc._mdp_file = mdp_file  # Store the original MDPFile
        return doc
    
    @classmethod
    def create(
        cls, 
        content: str = "", 
        title: Optional[str] = None, 
        author: Optional[str] = None,
        **metadata_kwargs
    ) -> "Document":
        """
        Create a new Document with sensible defaults.
        
        Args:
            content: The markdown content of the document
            title: The title of the document
            author: The author of the document
            **metadata_kwargs: Additional metadata fields
            
        Returns:
            A new Document instance
        """
        metadata = create_metadata(
            title=title or "Untitled Document",
            author=author,
            **metadata_kwargs
        )
        
        return cls(content=content, metadata=metadata)
    
    def save(self, path: Optional[Union[str, Path]] = None) -> "Document":
        """
        Save the document to a file.
        
        Args:
            path: The path to save the document to. If None, uses the current path.
            
        Returns:
            The Document instance for method chaining
            
        Raises:
            ValueError: If no path is provided and the document has no path
        """
        if path is not None:
            path = Path(path)
        
        self._mdp_file.save(path)
        return self
    
    def to_string(self) -> str:
        """
        Convert the document to its string representation.
        
        Returns:
            The MDP file format as a string
        """
        return self._mdp_file.to_string()
    
    @property
    def content(self) -> str:
        """Get the document content."""
        return self._mdp_file.content
    
    @content.setter
    def content(self, value: str):
        """Set the document content."""
        self._mdp_file.content = value
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the document metadata."""
        return self._mdp_file.metadata
    
    @property
    def path(self) -> Optional[Path]:
        """Get the document path."""
        return self._mdp_file.path
    
    # Convenience properties for common metadata fields
    
    @property
    def title(self) -> str:
        """Get the document title."""
        return self.metadata.get("title", "")
    
    @title.setter
    def title(self, value: str):
        """Set the document title."""
        self.metadata["title"] = value
    
    @property
    def author(self) -> Optional[str]:
        """Get the document author."""
        return self.metadata.get("author")
    
    @author.setter
    def author(self, value: str):
        """Set the document author."""
        self.metadata["author"] = value
    
    @property
    def created_at(self) -> Optional[str]:
        """Get the document creation date."""
        return self.metadata.get("created_at")
    
    @created_at.setter
    def created_at(self, value: Union[str, date]):
        """Set the document creation date."""
        self.metadata["created_at"] = format_date(value)
    
    @property
    def updated_at(self) -> Optional[str]:
        """Get the document last update date."""
        return self.metadata.get("updated_at")
    
    @updated_at.setter
    def updated_at(self, value: Union[str, date]):
        """Set the document last update date."""
        self.metadata["updated_at"] = format_date(value)
    
    @property
    def tags(self) -> List[str]:
        """Get the document tags."""
        return self.metadata.get("tags", [])
    
    def add_tag(self, tag: str) -> "Document":
        """
        Add a tag to the document.
        
        Args:
            tag: The tag to add
            
        Returns:
            The Document instance for method chaining
        """
        if "tags" not in self.metadata:
            self.metadata["tags"] = []
        
        if tag not in self.metadata["tags"]:
            self.metadata["tags"].append(tag)
        
        return self
    
    def remove_tag(self, tag: str) -> "Document":
        """
        Remove a tag from the document.
        
        Args:
            tag: The tag to remove
            
        Returns:
            The Document instance for method chaining
        """
        if "tags" in self.metadata and tag in self.metadata["tags"]:
            self.metadata["tags"].remove(tag)
        
        return self
    
    # Relationship methods
    
    def add_relationship(
        self,
        target: Union[str, "Document"],
        relationship_type: str = "related",
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> "Document":
        """
        Add a relationship to another document.
        
        Args:
            target: The target document or its identifier (path, UUID, or URI)
            relationship_type: The type of relationship (parent, child, related, reference)
            title: Optional title for the relationship
            description: Optional description of the relationship
            
        Returns:
            The Document instance for method chaining
            
        Raises:
            ValueError: If the relationship type is invalid
        """
        if relationship_type not in VALID_RELATIONSHIP_TYPES:
            raise ValueError(f"Invalid relationship type: {relationship_type}. "
                            f"Must be one of: {', '.join(VALID_RELATIONSHIP_TYPES)}")
        
        # Determine the reference type and value
        if isinstance(target, Document):
            # If the target has a UUID, use that
            if "uuid" in target.metadata:
                ref_id = target.metadata["uuid"]
                is_uri = False
            # If the target has a path, use that
            elif target.path:
                ref_id = str(target.path)
                is_uri = False
            # If all else fails, use the title
            else:
                ref_id = target.title
                is_uri = False
            
            # Use the target's title if none provided
            if title is None:
                title = target.title
        
        # If it's a string, try to determine if it's a path, UUID, or URI
        else:
            ref_id = target
            is_uri = ref_id.startswith("mdp://")
        
        # Convert Path objects to strings if necessary
        if isinstance(ref_id, Path):
            ref_id = str(ref_id)
        
        # Add the relationship to metadata directly with proper parameter forwarding
        add_relationship_to_metadata(
            self.metadata,
            reference=ref_id,
            rel_type=relationship_type,
            title=title,
            description=description,
            is_uri=is_uri
        )
        
        return self
    
    def get_related_documents(
        self,
        relationship_type: Optional[str] = None,
        base_path: Optional[Union[str, Path]] = None
    ) -> List["Document"]:
        """
        Get all related documents of the specified type.
        
        Args:
            relationship_type: Optional type of relationship to filter by
            base_path: Optional base path for resolving relative paths
            
        Returns:
            A list of related Document instances
        """
        # Convert base_path to Path if it's a string
        if base_path is not None and not isinstance(base_path, Path):
            base_path = Path(base_path)
        
        # Use the document's path as the base path if not provided
        if base_path is None and self.path is not None:
            base_path = self.path.parent
        
        # Find the related MDP files
        related_files = find_related_documents(
            self._mdp_file,
            relationship_type=relationship_type,
            base_path=base_path
        )
        
        # Convert them to Document instances
        related_docs = []
        for mdp_file in related_files:
            doc = Document(
                content=mdp_file.content,
                metadata=mdp_file.metadata,
                path=mdp_file.path
            )
            doc._mdp_file = mdp_file  # Store the original MDPFile
            related_docs.append(doc)
        
        return related_docs

    @property
    def version(self) -> Optional[str]:
        """Get the document version."""
        return self.metadata.get("version")

    @version.setter
    def version(self, value: str):
        """
        Set the document version.
        
        Args:
            value: The version string (should be a valid semantic version)
            
        Raises:
            ValueError: If the version is not a valid semantic version
        """
        if not is_semantic_version(value):
            raise ValueError(f"Invalid semantic version: {value}. Expected format: X.Y.Z")
        
        self.metadata["version"] = value

    def bump_version(self, version_type: str = "patch") -> "Document":
        """
        Bump the document version according to semantic versioning.
        
        Args:
            version_type: The type of version increment ('major', 'minor', or 'patch')
            
        Returns:
            The Document instance for method chaining
            
        Raises:
            ValueError: If the current version is not a valid semantic version or
                      version_type is invalid.
        """
        current_version = self.version or "0.0.0"
        new_version = next_version(current_version, version_type)
        self.version = new_version
        self.updated_at = format_date(date.today())
        return self

    @property
    def version_history(self) -> List[Dict[str, Any]]:
        """Get the document version history."""
        return self.metadata.get("version_history", [])

    def create_version(
        self, 
        version: Optional[str] = None, 
        author: Optional[str] = None, 
        description: Optional[str] = None,
        version_type: str = "patch"
    ) -> str:
        """
        Create a new version of this document.
        
        Args:
            version: Optional explicit version to use. If not provided, increments current version.
            author: Optional author of this version.
            description: Optional description of changes.
            version_type: The type of version increment if version not specified ('major', 'minor', 'patch').
            
        Returns:
            Path to the new version file.
            
        Raises:
            ValueError: If the document has no path or version is invalid.
        """
        if not self.path:
            raise ValueError("Document must be saved before creating a version")
        
        # Use the version manager
        from .versioning import get_version_manager
        vm = get_version_manager(self.path)
        
        # If no explicit version, determine the next version
        if not version:
            current_version = self.version or "0.0.0"
            version = next_version(current_version, version_type)
        
        # Update document version
        self.version = version
        self.updated_at = format_date(date.today())
        
        # Save changes
        self.save()
        
        # Create version
        return vm.create_version(
            document_path=self.path,
            version=version,
            author=author or self.author,
            description=description
        )

    def get_versions(self) -> List[Dict[str, Any]]:
        """
        Get all versions of this document.
        
        Returns:
            List of version entries sorted by version (newest first).
            
        Raises:
            ValueError: If the document has no path.
        """
        if not self.path:
            raise ValueError("Document must be saved before getting versions")
        
        from .versioning import get_version_manager
        vm = get_version_manager(self.path)
        return vm.list_versions(self.path)

    def compare_with_version(self, version: str) -> Dict[str, Any]:
        """
        Compare the current document with a specific version.
        
        Args:
            version: The version to compare with
            
        Returns:
            Dictionary with differences in metadata and content
            
        Raises:
            ValueError: If the document has no path or version is invalid
        """
        if not self.path:
            raise ValueError("Document must be saved before comparing versions")
        
        # Get the current version
        current_version = self.version
        if not current_version:
            raise ValueError("Document has no version")
        
        from .versioning import get_version_manager
        vm = get_version_manager(self.path)
        return vm.compare_versions(self.path, current_version, version)

    def rollback_to_version(self, version: str, create_backup: bool = True) -> "Document":
        """
        Roll back to a previous version.
        
        Args:
            version: The version to roll back to
            create_backup: Whether to create a backup of the current state
            
        Returns:
            The Document instance (reloaded after rollback)
            
        Raises:
            ValueError: If the document has no path or version is invalid
        """
        if not self.path:
            raise ValueError("Document must be saved before rolling back")
        
        from .versioning import get_version_manager
        vm = get_version_manager(self.path)
        
        # Perform rollback
        vm.rollback_to_version(self.path, version, create_backup)
        
        # Reload the document
        rolled_back_doc = Document.from_file(self.path)
        
        # Update this document instance with the rolled back content
        self._mdp_file = rolled_back_doc._mdp_file
        
        return self

    def create_branch(self, branch_name: str, base_version: Optional[str] = None) -> "Document":
        """
        Create a branch of this document.
        
        Args:
            branch_name: Name for the new branch
            base_version: Optional version to branch from (latest if None)
            
        Returns:
            New Document instance for the branch
            
        Raises:
            ValueError: If the document has no path
        """
        if not self.path:
            raise ValueError("Document must be saved before creating a branch")
        
        from .versioning import get_version_manager
        vm = get_version_manager(self.path)
        
        # Create branch
        branch_path = vm.create_branch(self.path, branch_name, base_version)
        
        # Return the branch document
        return Document.from_file(branch_path)

    def merge_from_branch(self, branch_doc: "Document", create_backup: bool = True) -> "Document":
        """
        Merge changes from a branch document into this document.
        
        Args:
            branch_doc: Branch document to merge from
            create_backup: Whether to create a backup before merge
            
        Returns:
            The Document instance after merge
            
        Raises:
            ValueError: If either document has no path
        """
        if not self.path:
            raise ValueError("Document must be saved before merging")
        
        if not branch_doc.path:
            raise ValueError("Branch document must be saved before merging")
        
        from .versioning import get_version_manager
        vm = get_version_manager(self.path)
        
        # Perform merge
        vm.merge_branch(branch_doc.path, self.path, create_backup)
        
        # Reload this document
        merged_doc = Document.from_file(self.path)
        
        # Update this document instance with the merged content
        self._mdp_file = merged_doc._mdp_file
        
        return self
    
    # Conflict resolution methods
    
    def check_for_conflicts(self, other_doc: "Document") -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if there are conflicts between this document and another document.
        
        Args:
            other_doc: The other document to compare with
            
        Returns:
            Tuple of (has_conflicts, conflict_summary)
            
        Raises:
            ValueError: If this document has no path
        """
        if not self.path:
            raise ValueError("Document must be saved before checking for conflicts")
        
        from .conflict import ConflictManager
        manager = ConflictManager()
        
        # If other document has no path, save it to a temporary location
        if not other_doc.path:
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, "temp_doc.mdp")
            other_doc.save(temp_path)
            has_conflicts, conflict = manager.check_for_conflicts(self.path, temp_path)
            
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        else:
            has_conflicts, conflict = manager.check_for_conflicts(self.path, other_doc.path)
        
        if conflict:
            return has_conflicts, conflict.get_conflict_summary()
        else:
            return False, None
    
    def auto_merge(self, other_doc: "Document", output_path: Optional[Union[str, Path]] = None) -> "Document":
        """
        Attempt to automatically merge changes from another document.
        
        Args:
            other_doc: The document to merge from
            output_path: Optional path to save the merged document (defaults to self.path)
            
        Returns:
            A new Document instance with the merged content
            
        Raises:
            ValueError: If this document has no path
            ConflictError: If conflicts cannot be auto-resolved
        """
        if not self.path:
            raise ValueError("Document must be saved before merging")
        
        from .conflict import ConflictManager
        manager = ConflictManager()
        
        # If other document has no path, save it to a temporary location
        if not other_doc.path:
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, "temp_doc.mdp")
            other_doc.save(temp_path)
            
            try:
                success, merged_path = manager.auto_merge(self.path, temp_path, output_path)
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
        else:
            success, merged_path = manager.auto_merge(self.path, other_doc.path, output_path)
        
        if not success or not merged_path:
            from .conflict import ConflictError
            raise ConflictError("Auto-merge failed due to unresolvable conflicts.")
        
        # Return a new document with the merged content
        return Document.from_file(merged_path)
    
    def create_conflict_resolution_file(self, other_doc: "Document", output_path: Union[str, Path]) -> str:
        """
        Create a file with conflict markers for manual resolution.
        
        Args:
            other_doc: The document to compare with
            output_path: Path to save the conflict resolution file
            
        Returns:
            Path to the created conflict file
            
        Raises:
            ValueError: If this document has no path
        """
        if not self.path:
            raise ValueError("Document must be saved before creating conflict file")
        
        from .conflict import ConflictManager
        manager = ConflictManager()
        
        # If other document has no path, save it to a temporary location
        if not other_doc.path:
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, "temp_doc.mdp")
            other_doc.save(temp_path)
            
            try:
                has_conflicts, conflict = manager.check_for_conflicts(self.path, temp_path)
                if has_conflicts and conflict:
                    return manager.create_conflict_file(conflict, output_path)
                else:
                    # No conflicts, just copy this document
                    self.save(output_path)
                    return str(output_path)
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
        else:
            has_conflicts, conflict = manager.check_for_conflicts(self.path, other_doc.path)
            if has_conflicts and conflict:
                return manager.create_conflict_file(conflict, output_path)
            else:
                # No conflicts, just copy this document
                self.save(output_path)
                return str(output_path)
    
    @classmethod
    def resolve_from_conflict_file(cls, conflict_file_path: Union[str, Path], output_path: Union[str, Path]) -> "Document":
        """
        Resolve conflicts from a manually edited conflict file.
        
        Args:
            conflict_file_path: Path to the conflict file
            output_path: Path to save the resolved document
            
        Returns:
            A new Document instance with the resolved content
            
        Raises:
            ConflictError: If the conflict file still has unresolved conflicts
        """
        from .conflict import ConflictManager
        manager = ConflictManager()
        
        # Resolve conflicts and save resolved document
        resolved_path = manager.resolve_from_conflict_file(conflict_file_path, output_path)
        
        # Return document with resolved content
        return cls.from_file(resolved_path)
    
    def detect_concurrent_modification(self, expected_version: Optional[str] = None) -> bool:
        """
        Detect if the document has been modified concurrently by another user.
        
        Args:
            expected_version: The expected version (if None, uses version from metadata)
            
        Returns:
            True if the document has been modified concurrently, False otherwise
        """
        if not self.path:
            return False
        
        from .conflict import detect_concurrent_modification
        return detect_concurrent_modification(self.path, expected_version) 