"""
Conflict detection and resolution for MDP documents.

This module provides functionality for detecting and resolving conflicts
when multiple users modify the same document concurrently.
"""

import os
import re
import json
import difflib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union, Callable
import datetime

from .core import MDPFile, read_mdp, write_mdp
from .metadata import format_date, is_semantic_version
from .versioning import VersionManager, Version, get_version_manager


class ConflictError(Exception):
    """Exception raised for document conflicts."""
    pass


class Conflict:
    """
    Represents a conflict between two versions of a document.
    
    This class stores information about conflicting changes and
    provides methods for resolving them.
    """
    
    def __init__(
        self, 
        base_doc: MDPFile,
        local_doc: MDPFile,
        remote_doc: MDPFile,
        base_version: str,
        local_version: str,
        remote_version: str
    ):
        """
        Initialize a Conflict object.
        
        Args:
            base_doc: The common ancestor document
            local_doc: The local version of the document
            remote_doc: The remote version of the document
            base_version: Version of the base document
            local_version: Version of the local document
            remote_version: Version of the remote document
        """
        self.base_doc = base_doc
        self.local_doc = local_doc
        self.remote_doc = remote_doc
        self.base_version = base_version
        self.local_version = local_version
        self.remote_version = remote_version
        
        # Detect conflicts in metadata and content
        self.metadata_conflicts = self._detect_metadata_conflicts()
        self.content_conflicts = self._detect_content_conflicts()
        
        # Merged result (initially None until merge is performed)
        self.merged_doc = None
    
    def has_conflicts(self) -> bool:
        """
        Check if there are any conflicts.
        
        Returns:
            True if conflicts exist, False otherwise
        """
        return bool(self.metadata_conflicts or self.content_conflicts)
    
    def _detect_metadata_conflicts(self) -> Dict[str, Dict[str, Any]]:
        """
        Detect conflicts in metadata.
        
        Returns:
            Dictionary of conflicting fields with local and remote values
        """
        conflicts = {}
        
        # Get all fields that were changed in either version
        for field in set(self.local_doc.metadata.keys()) | set(self.remote_doc.metadata.keys()):
            # Skip fields that shouldn't be compared
            if field in ['updated_at', 'version', 'version_history']:
                continue
            
            base_value = self.base_doc.metadata.get(field)
            local_value = self.local_doc.metadata.get(field)
            remote_value = self.remote_doc.metadata.get(field)
            
            # If field was changed in both versions and changes are different
            if (local_value != base_value and 
                remote_value != base_value and 
                local_value != remote_value):
                
                conflicts[field] = {
                    'base': base_value,
                    'local': local_value,
                    'remote': remote_value
                }
        
        return conflicts
    
    def _detect_content_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect conflicts in document content.
        
        Returns:
            List of conflicting regions with base, local, and remote content
        """
        # Get content as lines
        base_lines = self.base_doc.content.splitlines()
        local_lines = self.local_doc.content.splitlines()
        remote_lines = self.remote_doc.content.splitlines()
        
        # Use difflib to get difference between base and both versions
        matcher = difflib.SequenceMatcher(None, base_lines, local_lines)
        local_opcodes = matcher.get_opcodes()
        
        matcher = difflib.SequenceMatcher(None, base_lines, remote_lines)
        remote_opcodes = matcher.get_opcodes()
        
        # Find regions changed in both versions
        conflicts = []
        
        # This is a simplified approach - a more sophisticated algorithm would be needed
        # for production use to handle overlapping changes more accurately
        for local_tag, local_i1, local_i2, local_j1, local_j2 in local_opcodes:
            if local_tag in ('replace', 'delete', 'insert'):
                for remote_tag, remote_i1, remote_i2, remote_j1, remote_j2 in remote_opcodes:
                    if remote_tag in ('replace', 'delete', 'insert'):
                        # Check if the changes overlap
                        if max(local_i1, remote_i1) < min(local_i2, remote_i2):
                            # Overlapping changes detected
                            conflicts.append({
                                'region': (min(local_i1, remote_i1), max(local_i2, remote_i2)),
                                'base': '\n'.join(base_lines[min(local_i1, remote_i1):max(local_i2, remote_i2)]),
                                'local': '\n'.join(local_lines[local_j1:local_j2]),
                                'remote': '\n'.join(remote_lines[remote_j1:remote_j2])
                            })
        
        return conflicts
    
    def auto_merge(self) -> Tuple[bool, MDPFile]:
        """
        Attempt to automatically merge the changes.
        
        Returns:
            Tuple of (success, merged document)
            
        Raises:
            ConflictError: If auto-merge cannot resolve all conflicts
        """
        # If there are conflicts that can't be auto-resolved, raise an error
        if self.has_conflicts():
            raise ConflictError(f"Cannot auto-merge document. Found {len(self.metadata_conflicts)} metadata conflicts and {len(self.content_conflicts)} content conflicts.")
        
        # Start with the local document as the base for merging
        merged_metadata = self.local_doc.metadata.copy()
        
        # Apply non-conflicting changes from remote to metadata
        for field, remote_value in self.remote_doc.metadata.items():
            # Skip fields that shouldn't be merged
            if field in ['updated_at', 'version', 'version_history']:
                continue
                
            base_value = self.base_doc.metadata.get(field)
            local_value = self.local_doc.metadata.get(field)
            
            # If field wasn't changed locally but was changed remotely, use remote value
            if local_value == base_value and remote_value != base_value:
                merged_metadata[field] = remote_value
        
        # Merge content (using a three-way merge algorithm)
        merged_content = self._merge_content()
        
        # Set version and update time
        merged_metadata['updated_at'] = format_date(datetime.datetime.now())
        
        # Determine next version: use the higher of local and remote, and increment patch
        local_ver = Version(self.local_version)
        remote_ver = Version(self.remote_version)
        next_ver = str(max(local_ver, remote_ver).next_patch())
        merged_metadata['version'] = next_ver
        
        # Create merged document
        self.merged_doc = MDPFile(
            metadata=merged_metadata,
            content=merged_content,
            path=self.local_doc.path
        )
        
        return True, self.merged_doc
    
    def _merge_content(self) -> str:
        """
        Merge document content using a three-way merge algorithm.
        
        Returns:
            Merged content as a string
        """
        base_lines = self.base_doc.content.splitlines()
        local_lines = self.local_doc.content.splitlines()
        remote_lines = self.remote_doc.content.splitlines()
        
        # Use difflib for a three-way merge
        # This is a simplified implementation
        
        # Get difference between base and both versions
        matcher = difflib.SequenceMatcher(None, base_lines, local_lines)
        local_opcodes = matcher.get_opcodes()
        
        matcher = difflib.SequenceMatcher(None, base_lines, remote_lines)
        remote_opcodes = matcher.get_opcodes()
        
        # Create merged content by applying non-conflicting changes
        result_lines = base_lines.copy()
        
        # First apply remote changes that don't conflict with local changes
        offset = 0  # Track line offset as we modify result_lines
        
        for remote_tag, remote_i1, remote_i2, remote_j1, remote_j2 in remote_opcodes:
            if remote_tag in ('replace', 'delete', 'insert'):
                # Check if this change conflicts with any local change
                conflicts = False
                for local_tag, local_i1, local_i2, local_j1, local_j2 in local_opcodes:
                    if local_tag in ('replace', 'delete', 'insert'):
                        if max(local_i1, remote_i1) < min(local_i2, remote_i2):
                            conflicts = True
                            break
                
                if not conflicts:
                    # Apply remote change
                    if remote_tag == 'replace' or remote_tag == 'insert':
                        # Replace or insert lines from remote
                        result_lines[remote_i1+offset:remote_i2+offset] = remote_lines[remote_j1:remote_j2]
                        offset += (remote_j2 - remote_j1) - (remote_i2 - remote_i1)
                    elif remote_tag == 'delete':
                        # Delete lines
                        del result_lines[remote_i1+offset:remote_i2+offset]
                        offset -= (remote_i2 - remote_i1)
        
        # Then apply local changes (they take precedence in case of conflicts)
        offset = 0  # Reset offset
        
        for local_tag, local_i1, local_i2, local_j1, local_j2 in local_opcodes:
            if local_tag in ('replace', 'delete', 'insert'):
                # Apply local change
                if local_tag == 'replace' or local_tag == 'insert':
                    # Replace or insert lines from local
                    result_lines[local_i1+offset:local_i2+offset] = local_lines[local_j1:local_j2]
                    offset += (local_j2 - local_j1) - (local_i2 - local_i1)
                elif local_tag == 'delete':
                    # Delete lines
                    del result_lines[local_i1+offset:local_i2+offset]
                    offset -= (local_i2 - local_i1)
        
        return '\n'.join(result_lines)
    
    def resolve_metadata_conflict(self, field: str, resolution: Union[str, Any]) -> None:
        """
        Resolve a metadata conflict.
        
        Args:
            field: The conflicting metadata field
            resolution: The value to use for resolution ('base', 'local', 'remote', or a custom value)
        """
        if field not in self.metadata_conflicts:
            raise ValueError(f"No conflict found for metadata field: {field}")
        
        conflict = self.metadata_conflicts[field]
        
        if resolution == 'base':
            value = conflict['base']
        elif resolution == 'local':
            value = conflict['local']
        elif resolution == 'remote':
            value = conflict['remote']
        else:
            # Use the provided custom value
            value = resolution
        
        # Apply the resolution
        if self.merged_doc is None:
            # Create merged doc if it doesn't exist yet
            self.merged_doc = MDPFile(
                metadata=self.local_doc.metadata.copy(),
                content=self.local_doc.content,
                path=self.local_doc.path
            )
        
        self.merged_doc.metadata[field] = value
        
        # Remove from conflicts
        del self.metadata_conflicts[field]
    
    def resolve_content_conflict(self, index: int, resolution: Union[str, str]) -> None:
        """
        Resolve a content conflict.
        
        Args:
            index: The index of the conflict in the conflicts list
            resolution: The content to use for resolution ('base', 'local', 'remote', or custom content)
        """
        if index < 0 or index >= len(self.content_conflicts):
            raise ValueError(f"Invalid conflict index: {index}")
        
        conflict = self.content_conflicts[index]
        
        if resolution == 'base':
            content = conflict['base']
        elif resolution == 'local':
            content = conflict['local']
        elif resolution == 'remote':
            content = conflict['remote']
        else:
            # Use the provided custom content
            content = resolution
        
        # Apply the resolution
        if self.merged_doc is None:
            # Create merged doc if it doesn't exist yet
            self.merged_doc = MDPFile(
                metadata=self.local_doc.metadata.copy(),
                content=self.local_doc.content,
                path=self.local_doc.path
            )
        
        # Split content into lines
        merged_lines = self.merged_doc.content.splitlines()
        
        # Replace the conflicting region with the resolved content
        region_start, region_end = conflict['region']
        content_lines = content.splitlines()
        
        merged_lines[region_start:region_end] = content_lines
        
        # Update merged content
        self.merged_doc.content = '\n'.join(merged_lines)
        
        # Remove from conflicts
        self.content_conflicts.pop(index)
    
    def get_conflict_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all conflicts.
        
        Returns:
            Dictionary with conflict information
        """
        return {
            'base_version': self.base_version,
            'local_version': self.local_version,
            'remote_version': self.remote_version,
            'metadata_conflicts': self.metadata_conflicts,
            'content_conflicts': self.content_conflicts,
            'has_conflicts': self.has_conflicts()
        }
    
    def save_merged(self, path: Optional[str] = None) -> str:
        """
        Save the merged document.
        
        Args:
            path: Path to save the merged document (defaults to local doc path)
            
        Returns:
            Path where the document was saved
            
        Raises:
            ConflictError: If conflicts are not resolved or merged doc doesn't exist
        """
        if self.merged_doc is None:
            raise ConflictError("No merged document exists. Perform auto_merge or resolve conflicts first.")
        
        if self.has_conflicts():
            raise ConflictError("Cannot save merged document with unresolved conflicts.")
        
        # Save the merged document
        save_path = path or self.merged_doc.path
        self.merged_doc.save(save_path)
        
        return save_path


class ConflictManager:
    """
    Manages document conflicts and resolution.
    
    This class provides methods for detecting conflicts between document versions
    and resolving them either automatically or manually.
    """
    
    def __init__(self, version_manager: Optional[VersionManager] = None):
        """
        Initialize a ConflictManager.
        
        Args:
            version_manager: VersionManager to use (creates a new one if None)
        """
        self.version_manager = version_manager
    
    def check_for_conflicts(
        self, 
        local_path: Union[str, Path],
        remote_path: Union[str, Path],
        base_version: Optional[str] = None
    ) -> Tuple[bool, Optional[Conflict]]:
        """
        Check if there are conflicts between local and remote versions.
        
        Args:
            local_path: Path to the local document
            remote_path: Path to the remote document
            base_version: Common ancestor version (auto-detected if None)
            
        Returns:
            Tuple of (has_conflicts, conflict_object)
        """
        local_path = Path(local_path)
        remote_path = Path(remote_path)
        
        # Get the version manager for the local document
        if self.version_manager is None:
            self.version_manager = get_version_manager(local_path)
        
        # Read the local and remote documents
        local_doc = read_mdp(local_path)
        remote_doc = read_mdp(remote_path)
        
        # Get version information
        local_version = local_doc.metadata.get('version', '0.0.0')
        remote_version = remote_doc.metadata.get('version', '0.0.0')
        
        # If base version is not provided, try to find the common ancestor
        if base_version is None:
            base_version = self._find_common_ancestor(local_path, local_version, remote_version)
        
        # Get the base document
        try:
            base_doc = self.version_manager.get_version(local_path, base_version)
        except FileNotFoundError:
            # If we can't find the base version, use a default empty document
            base_doc = MDPFile(
                metadata={'title': 'Base Document', 'version': base_version},
                content='',
                path=None
            )
        
        # Create a conflict object
        conflict = Conflict(
            base_doc=base_doc,
            local_doc=local_doc,
            remote_doc=remote_doc,
            base_version=base_version,
            local_version=local_version,
            remote_version=remote_version
        )
        
        return conflict.has_conflicts(), conflict
    
    def _find_common_ancestor(
        self, 
        document_path: Path, 
        version1: str, 
        version2: str
    ) -> str:
        """
        Find the most recent common ancestor of two versions.
        
        Args:
            document_path: Path to the document
            version1: First version string
            version2: Second version string
            
        Returns:
            Version string of the common ancestor
        """
        # Get version histories
        try:
            versions = self.version_manager.list_versions(document_path)
            
            # Convert to a list of version strings
            version_strings = [v['version'] for v in versions]
            
            # Find common ancestor (the highest version that's less than both versions)
            v1 = Version(version1)
            v2 = Version(version2)
            
            ancestor = None
            for v_str in version_strings:
                v = Version(v_str)
                if v < v1 and v < v2:
                    if ancestor is None or v > Version(ancestor):
                        ancestor = v_str
            
            if ancestor:
                return ancestor
            
        except Exception:
            pass
        
        # Default to 0.0.0 if we can't find a common ancestor
        return '0.0.0'
    
    def auto_merge(
        self, 
        local_path: Union[str, Path],
        remote_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        base_version: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Attempt to automatically merge two document versions.
        
        Args:
            local_path: Path to the local document
            remote_path: Path to the remote document
            output_path: Path to save the merged document (defaults to local_path)
            base_version: Common ancestor version (auto-detected if None)
            
        Returns:
            Tuple of (success, merged_path)
        """
        # Check for conflicts
        has_conflicts, conflict = self.check_for_conflicts(local_path, remote_path, base_version)
        
        if conflict is None:
            return False, None
        
        try:
            # Try to auto-merge
            success, merged_doc = conflict.auto_merge()
            
            # Save the merged document
            output_path = output_path or local_path
            merged_doc.save(output_path)
            
            return True, str(output_path)
        
        except ConflictError:
            # Auto-merge failed
            return False, None
    
    def create_conflict_file(
        self, 
        conflict: Conflict,
        output_path: Union[str, Path]
    ) -> str:
        """
        Create a file with conflict markers for manual resolution.
        
        Args:
            conflict: Conflict object
            output_path: Path to save the conflict file
            
        Returns:
            Path to the created conflict file
        """
        output_path = Path(output_path)
        
        # Create conflict file content
        content = []
        
        # Add metadata conflicts
        content.append("# METADATA CONFLICTS")
        content.append("# Resolve metadata conflicts by editing the metadata section below")
        content.append("# Keep the values you want and remove conflict markers")
        content.append("")
        
        # Create metadata section with conflicts marked
        metadata = conflict.local_doc.metadata.copy()
        
        for field, conflict_info in conflict.metadata_conflicts.items():
            metadata[field] = f"<<<<<<< LOCAL\n{conflict_info['local']}\n=======\n{conflict_info['remote']}\n>>>>>>> REMOTE"
        
        # Add metadata as YAML
        import yaml
        metadata_yaml = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        content.append("---")
        content.append(metadata_yaml)
        content.append("---")
        content.append("")
        
        # Add content with conflict markers
        content.append(conflict.local_doc.content)
        
        # Add markers for content conflicts
        for i, content_conflict in enumerate(conflict.content_conflicts):
            content.append(f"\n\n<<<<<<< LOCAL (Conflict {i+1})")
            content.append(content_conflict['local'])
            content.append("=======")
            content.append(content_conflict['remote'])
            content.append(">>>>>>> REMOTE")
        
        # Write the conflict file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        return str(output_path)
    
    def resolve_from_conflict_file(
        self,
        conflict_file_path: Union[str, Path],
        output_path: Union[str, Path]
    ) -> str:
        """
        Resolve conflicts from a manually edited conflict file.
        
        Args:
            conflict_file_path: Path to the conflict file
            output_path: Path to save the resolved document
            
        Returns:
            Path to the resolved document
            
        Raises:
            ConflictError: If the conflict file still has unresolved conflicts
        """
        conflict_file_path = Path(conflict_file_path)
        output_path = Path(output_path)
        
        # Read the conflict file
        with open(conflict_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if there are still conflict markers
        if "<<<<<<< LOCAL" in content or ">>>>>>> REMOTE" in content:
            raise ConflictError("Conflict file still has unresolved conflicts.")
        
        # Parse metadata and content
        from .metadata import extract_metadata
        metadata, doc_content = extract_metadata(content)
        
        # Create and save the resolved document
        mdp_file = MDPFile(metadata=metadata, content=doc_content)
        mdp_file.save(output_path)
        
        return str(output_path)


def detect_concurrent_modification(
    document_path: Union[str, Path],
    expected_version: Optional[str] = None
) -> bool:
    """
    Detect if a document has been modified concurrently.
    
    Args:
        document_path: Path to the document
        expected_version: The expected version (if None, uses version from metadata)
        
    Returns:
        True if the document has been modified concurrently, False otherwise
    """
    document_path = Path(document_path)
    
    # Read the document
    try:
        doc = read_mdp(document_path)
        
        # Get the current version
        current_version = doc.metadata.get('version', '0.0.0')
        latest_version = doc.metadata.get('latest_version', current_version)
        
        # If expected_version is not provided, use the version from metadata
        if expected_version is None:
            expected_version = current_version
        
        # Check if the latest version is different from the expected version
        return latest_version != expected_version
    
    except Exception:
        # If we can't read the document, assume it hasn't been modified
        return False 