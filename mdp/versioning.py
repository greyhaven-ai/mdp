"""
Enhanced versioning system for MDP documents.

This module provides a more robust document versioning system with semantic versioning
and improved version history management.
"""

import os
import re
import json
from pathlib import Path
import datetime
from typing import Dict, Any, List, Tuple, Optional, Union
import shutil
import uuid
import difflib

from .core import MDPFile, read_mdp, write_mdp
from .metadata import format_date, is_semantic_version

# Regular expression for semantic versioning (MAJOR.MINOR.PATCH)
SEMVER_PATTERN = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')

class Version:
    """
    Represents a semantic version (major.minor.patch).
    
    This class provides parsing and comparison for semantic versions.
    """
    
    def __init__(self, version_str: str):
        """
        Initialize a Version from a string.
        
        Args:
            version_str: A string in the format 'major.minor.patch'
            
        Raises:
            ValueError: If the version string is not a valid semantic version
        """
        match = SEMVER_PATTERN.match(version_str)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_str}. Expected format: X.Y.Z")
        
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
        self.version_str = version_str
    
    def __str__(self) -> str:
        """Convert to string representation."""
        return self.version_str
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Version({self.major}.{self.minor}.{self.patch})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another Version."""
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __lt__(self, other) -> bool:
        """Compare versions (less than)."""
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __le__(self, other) -> bool:
        """Compare versions (less than or equal)."""
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)
    
    def __gt__(self, other) -> bool:
        """Compare versions (greater than)."""
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)
    
    def __ge__(self, other) -> bool:
        """Compare versions (greater than or equal)."""
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)
    
    def next_major(self) -> 'Version':
        """Get the next major version (X+1.0.0)."""
        return Version(f"{self.major + 1}.0.0")
    
    def next_minor(self) -> 'Version':
        """Get the next minor version (X.Y+1.0)."""
        return Version(f"{self.major}.{self.minor + 1}.0")
    
    def next_patch(self) -> 'Version':
        """Get the next patch version (X.Y.Z+1)."""
        return Version(f"{self.major}.{self.minor}.{self.patch + 1}")


class VersionManager:
    """
    Manages document versions with semantic versioning support.
    
    This class provides methods for creating, retrieving, and comparing versions
    of MDP documents using semantic versioning.
    """
    
    def __init__(self, versions_dir: Union[str, Path]):
        """
        Initialize a VersionManager.
        
        Args:
            versions_dir: Directory to store version files
        """
        self.versions_dir = Path(versions_dir)
        os.makedirs(self.versions_dir, exist_ok=True)
    
    def create_version(
        self, 
        document_path: Union[str, Path],
        version: str,
        author: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Create a new version of a document.
        
        Args:
            document_path: Path to the document
            version: Version string (X.Y.Z)
            author: Optional author of this version
            description: Optional description of changes
            
        Returns:
            Path to the created version file
            
        Raises:
            ValueError: If the version is not valid or already exists
        """
        document_path = Path(document_path)
        
        # Validate semantic version
        if not is_semantic_version(version):
            raise ValueError(f"Invalid semantic version: {version}. Expected format: X.Y.Z")
        
        # Check if document exists
        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        # Generate version filename
        base_name = document_path.stem
        version_path = self.versions_dir / f"{base_name}.{version}{document_path.suffix}"
        
        # Check if version already exists
        if version_path.exists():
            raise ValueError(f"Version {version} already exists: {version_path}")
        
        # Read the document
        mdp_file = read_mdp(document_path)
        
        # Update version history in metadata
        self._update_version_history(mdp_file, version, author, description, str(version_path))
        
        # Make sure metadata has a version field
        if "version" not in mdp_file.metadata or mdp_file.metadata["version"] != version:
            mdp_file.metadata["version"] = version
        
        # Save as a version
        mdp_file.save(version_path)
        
        # Update the original document to track the latest version
        self._update_original_document(document_path, version)
        
        return str(version_path)
    
    def _update_version_history(
        self, 
        mdp_file: MDPFile,
        version: str,
        author: Optional[str] = None,
        description: Optional[str] = None,
        path: Optional[str] = None
    ) -> None:
        """
        Update the version history in a document's metadata.
        
        Args:
            mdp_file: The MDPFile to update
            version: Version string
            author: Optional author of this version
            description: Optional description of changes
            path: Optional path to the version file
        """
        # Initialize version history if it doesn't exist
        if "version_history" not in mdp_file.metadata:
            mdp_file.metadata["version_history"] = []
        
        # Create version entry
        version_entry = {
            "version": version,
            "date": format_date(datetime.date.today())
        }
        
        if author:
            version_entry["author"] = author
        elif "author" in mdp_file.metadata:
            version_entry["author"] = mdp_file.metadata["author"]
            
        if description:
            version_entry["description"] = description
            
        if path:
            version_entry["path"] = path
        
        # Add to version history
        mdp_file.metadata["version_history"].append(version_entry)
        
        # Update latest version
        mdp_file.metadata["latest_version"] = version
    
    def _update_original_document(self, document_path: Path, version: str) -> None:
        """
        Update the original document with version information.
        
        Args:
            document_path: Path to the original document
            version: Version string
        """
        try:
            # Read the original document
            mdp_file = read_mdp(document_path)
            
            # Update version and latest_version
            mdp_file.metadata["version"] = version
            mdp_file.metadata["latest_version"] = version
            
            # Update the updated_at field
            mdp_file.metadata["updated_at"] = format_date(datetime.date.today())
            
            # Save the updated document
            mdp_file.save()
        except Exception as e:
            print(f"Warning: Could not update original document: {e}")
    
    def get_version(self, document_path: Union[str, Path], version: str) -> MDPFile:
        """
        Get a specific version of a document.
        
        Args:
            document_path: Path to the document
            version: Version string (X.Y.Z)
            
        Returns:
            MDPFile for the requested version
            
        Raises:
            ValueError: If the version is not valid
            FileNotFoundError: If the version does not exist
        """
        document_path = Path(document_path)
        
        # Validate semantic version
        if not is_semantic_version(version):
            raise ValueError(f"Invalid semantic version: {version}. Expected format: X.Y.Z")
        
        # Generate version filename
        base_name = document_path.stem
        version_path = self.versions_dir / f"{base_name}.{version}{document_path.suffix}"
        
        # Check if version exists
        if not version_path.exists():
            raise FileNotFoundError(f"Version {version} not found: {version_path}")
        
        # Read and return the version
        return read_mdp(version_path)
    
    def list_versions(self, document_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        List all versions of a document.
        
        Args:
            document_path: Path to the document
            
        Returns:
            List of version entries sorted by version (newest first)
        """
        document_path = Path(document_path)
        
        # Check if document exists
        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        # Read the document to get version history from metadata
        try:
            mdp_file = read_mdp(document_path)
            if "version_history" in mdp_file.metadata:
                # Sort by version (parse and sort using Version class)
                versions = mdp_file.metadata["version_history"]
                versions.sort(
                    key=lambda v: Version(v["version"]), 
                    reverse=True
                )
                return versions
        except Exception:
            pass
        
        # Fall back to scanning the versions directory if metadata doesn't have history
        base_name = document_path.stem
        version_pattern = re.compile(fr'^{re.escape(base_name)}\.(\d+\.\d+\.\d+){document_path.suffix}$')
        
        versions = []
        
        if self.versions_dir.exists():
            for file in os.listdir(self.versions_dir):
                match = version_pattern.match(file)
                if match:
                    version = match.group(1)
                    version_path = self.versions_dir / file
                    
                    # Try to get metadata from the version file
                    try:
                        version_file = read_mdp(version_path)
                        # Create a version entry
                        version_entry = {
                            "version": version,
                            "date": version_file.metadata.get("updated_at", "Unknown"),
                            "path": str(version_path)
                        }
                        
                        if "author" in version_file.metadata:
                            version_entry["author"] = version_file.metadata["author"]
                            
                        versions.append(version_entry)
                    except Exception:
                        # If we can't read the file, just add basic info
                        versions.append({
                            "version": version,
                            "date": datetime.datetime.fromtimestamp(version_path.stat().st_mtime).strftime("%Y-%m-%d"),
                            "path": str(version_path)
                        })
        
        # Sort versions by semantic version (newest first)
        versions.sort(
            key=lambda v: Version(v["version"]), 
            reverse=True
        )
        
        return versions
    
    def get_latest_version(self, document_path: Union[str, Path]) -> MDPFile:
        """
        Get the latest version of a document.
        
        Args:
            document_path: Path to the document
            
        Returns:
            MDPFile for the latest version
            
        Raises:
            FileNotFoundError: If no versions are found
        """
        versions = self.list_versions(document_path)
        
        if not versions:
            raise FileNotFoundError(f"No versions found for document: {document_path}")
        
        # Get the latest version (first in the sorted list)
        latest = versions[0]
        
        # If the path is in the version entry, use it
        if "path" in latest:
            return read_mdp(latest["path"])
        
        # Otherwise, construct the path
        document_path = Path(document_path)
        version = latest["version"]
        version_path = self.versions_dir / f"{document_path.stem}.{version}{document_path.suffix}"
        
        return read_mdp(version_path)
    
    def compare_versions(
        self, 
        document_path: Union[str, Path],
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        Compare two versions of a document.
        
        Args:
            document_path: Path to the document
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Dictionary with differences in metadata and content
            
        Raises:
            ValueError: If either version is not valid
            FileNotFoundError: If either version does not exist
        """
        # Get the two versions
        v1_file = self.get_version(document_path, version1)
        v2_file = self.get_version(document_path, version2)
        
        # Compare metadata
        metadata_diff = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        # Find added and changed fields
        for key, value in v2_file.metadata.items():
            if key not in v1_file.metadata:
                metadata_diff["added"][key] = value
            elif v1_file.metadata[key] != value:
                metadata_diff["changed"][key] = {
                    "old": v1_file.metadata[key],
                    "new": value
                }
        
        # Find removed fields
        for key in v1_file.metadata:
            if key not in v2_file.metadata:
                metadata_diff["removed"][key] = v1_file.metadata[key]
        
        # Compare content
        content_diff = self._generate_diff(v1_file.content, v2_file.content)
        
        return {
            "metadata_diff": metadata_diff,
            "content_diff": content_diff,
            "version1": version1,
            "version2": version2
        }
    
    def _generate_diff(self, text1: str, text2: str) -> List[Dict[str, Any]]:
        """
        Generate a structured diff between two text strings.
        
        Args:
            text1: Original text
            text2: Modified text
            
        Returns:
            List of diff entries with operation and text
        """
        differ = difflib.Differ()
        diff_lines = list(differ.compare(text1.splitlines(), text2.splitlines()))
        
        structured_diff = []
        for line in diff_lines:
            if line.startswith('+ '):
                structured_diff.append({
                    "op": "add",
                    "text": line[2:]
                })
            elif line.startswith('- '):
                structured_diff.append({
                    "op": "remove",
                    "text": line[2:]
                })
            elif line.startswith('? '):
                # Skip the "?" lines that Differ generates
                continue
            else:
                structured_diff.append({
                    "op": "unchanged",
                    "text": line[2:]
                })
        
        return structured_diff
    
    def rollback_to_version(
        self, 
        document_path: Union[str, Path],
        version: str,
        create_backup: bool = True
    ) -> str:
        """
        Roll back a document to a previous version.
        
        Args:
            document_path: Path to the document
            version: Version to roll back to
            create_backup: Whether to create a backup of the current state first
            
        Returns:
            Path to the updated document
            
        Raises:
            ValueError: If the version is not valid
            FileNotFoundError: If the version does not exist
        """
        document_path = Path(document_path)
        
        # Get the version to roll back to
        version_file = self.get_version(document_path, version)
        
        # Create a backup if requested
        if create_backup:
            # Get current document
            current = read_mdp(document_path)
            
            # Get current version
            current_version = current.metadata.get("version", "0.0.0")
            
            # Create a backup version
            self.create_version(
                document_path=document_path,
                version=current_version,
                description=f"Automatic backup before rollback to {version}"
            )
        
        # Create a new version entry for the rollback
        now = format_date(datetime.date.today())
        
        # Determine the new version number (increment patch)
        try:
            # Try to get the current version
            current = read_mdp(document_path)
            current_version = current.metadata.get("latest_version", current.metadata.get("version", "0.0.0"))
            
            # Parse it and increment patch
            v = Version(current_version)
            new_version = str(v.next_patch())
        except Exception:
            # If that fails, just use the rollback version with patch+1
            try:
                v = Version(version)
                new_version = str(v.next_patch())
            except Exception:
                # Last resort: use a timestamp-based version
                new_version = "0.0.1"
        
        # Update the version history
        if "version_history" not in version_file.metadata:
            version_file.metadata["version_history"] = []
        
        # Add new entry for this rollback
        version_file.metadata["version_history"].append({
            "version": new_version,
            "date": now,
            "description": f"Rollback to version {version}"
        })
        
        # Update version and dates
        version_file.metadata["version"] = new_version
        version_file.metadata["latest_version"] = new_version
        version_file.metadata["updated_at"] = now
        
        # Save the rolled-back document
        version_file.save(document_path)
        
        return str(document_path)
    
    def create_branch(
        self, 
        document_path: Union[str, Path],
        branch_name: str,
        base_version: Optional[str] = None
    ) -> str:
        """
        Create a branch of a document.
        
        Args:
            document_path: Path to the document
            branch_name: Name for the new branch
            base_version: Optional version to branch from (latest if None)
            
        Returns:
            Path to the branched document
            
        Raises:
            ValueError: If the base version is not valid
            FileNotFoundError: If the document or base version does not exist
        """
        document_path = Path(document_path)
        
        # Determine the base version file
        if base_version:
            base_file = self.get_version(document_path, base_version)
        else:
            # Use the current document as the base
            base_file = read_mdp(document_path)
            base_version = base_file.metadata.get("version", "0.0.0")
        
        # Create branch filename
        branch_path = document_path.parent / f"{document_path.stem}-{branch_name}{document_path.suffix}"
        
        # Check if branch already exists
        if branch_path.exists():
            raise ValueError(f"Branch already exists: {branch_path}")
        
        # Create a copy of the base file
        new_file = MDPFile(
            metadata=base_file.metadata.copy(),
            content=base_file.content,
            path=str(branch_path)
        )
        
        # Update metadata for the branch
        # Generate a new UUID for the branch
        new_file.metadata["uuid"] = str(uuid.uuid4())
        
        # Reset version history but keep track of origin
        if "version_history" in new_file.metadata:
            # Keep only the entry for the base version
            base_history = [entry for entry in new_file.metadata["version_history"] 
                           if entry.get("version") == base_version]
            new_file.metadata["version_history"] = base_history
        
        # Set branch information
        new_file.metadata["branch_name"] = branch_name
        new_file.metadata["branched_from"] = {
            "document": str(document_path),
            "version": base_version,
            "date": format_date(datetime.date.today())
        }
        
        # Add relationship to the original document
        if "relationships" not in new_file.metadata:
            new_file.metadata["relationships"] = []
        
        new_file.metadata["relationships"].append({
            "type": "parent",
            "path": str(document_path),
            "description": f"Original document (branched at version {base_version})"
        })
        
        # Update dates
        now = format_date(datetime.date.today())
        new_file.metadata["created_at"] = now
        new_file.metadata["updated_at"] = now
        
        # Save the branched document
        new_file.save()
        
        # Try to update the original document to reference this branch
        try:
            original = read_mdp(document_path)
            
            # Add relationship to the branch
            if "relationships" not in original.metadata:
                original.metadata["relationships"] = []
            
            original.metadata["relationships"].append({
                "type": "child",
                "path": str(branch_path),
                "description": f"Branch: {branch_name}"
            })
            
            # Save the updated original
            original.save()
        except Exception:
            # Don't fail if we can't update the original
            pass
        
        return str(branch_path)
    
    def merge_branch(
        self,
        branch_path: Union[str, Path],
        target_path: Union[str, Path],
        create_backup: bool = True
    ) -> str:
        """
        Merge a branch back into its original document.
        
        Args:
            branch_path: Path to the branch document
            target_path: Path to the target document (usually the original)
            create_backup: Whether to create a backup of the target first
            
        Returns:
            Path to the merged document
            
        Raises:
            ValueError: If the branch is not valid
            FileNotFoundError: If either document does not exist
        """
        branch_path = Path(branch_path)
        target_path = Path(target_path)
        
        # Check if both documents exist
        if not branch_path.exists():
            raise FileNotFoundError(f"Branch document not found: {branch_path}")
        
        if not target_path.exists():
            raise FileNotFoundError(f"Target document not found: {target_path}")
        
        # Read both documents
        branch = read_mdp(branch_path)
        target = read_mdp(target_path)
        
        # Create a backup if requested
        if create_backup:
            target_version = target.metadata.get("version", "0.0.0")
            self.create_version(
                document_path=target_path,
                version=target_version,
                description=f"Automatic backup before merge from {branch_path.name}"
            )
        
        # Get branch information
        branch_name = branch.metadata.get("branch_name", branch_path.stem)
        
        # Determine the new version
        try:
            target_version = target.metadata.get("version", "0.0.0")
            v = Version(target_version)
            
            # Use minor version bump for merges
            new_version = str(v.next_minor())
        except Exception:
            # If that fails, use a timestamp-based version
            new_version = "0.1.0"
        
        # Merge metadata (keeping original UUID and other key fields)
        preserve_fields = {"uuid", "created_at", "path"}
        
        for key, value in branch.metadata.items():
            if key not in preserve_fields:
                target.metadata[key] = value
        
        # Update version information
        target.metadata["version"] = new_version
        target.metadata["latest_version"] = new_version
        target.metadata["updated_at"] = format_date(datetime.date.today())
        
        # Add merge info to metadata
        if "merge_history" not in target.metadata:
            target.metadata["merge_history"] = []
        
        target.metadata["merge_history"].append({
            "branch": branch_name,
            "date": format_date(datetime.date.today()),
            "from_version": branch.metadata.get("version", "unknown"),
            "to_version": new_version
        })
        
        # Update the content
        target.content = branch.content
        
        # Save the merged document
        target.save()
        
        return str(target_path)


# Convenience function to get version manager with default configuration
def get_version_manager(document_path: Union[str, Path]) -> VersionManager:
    """
    Get a VersionManager for a document with default configuration.
    
    Args:
        document_path: Path to the document
        
    Returns:
        Configured VersionManager instance
    """
    document_path = Path(document_path)
    versions_dir = document_path.parent / ".versions"
    return VersionManager(versions_dir) 