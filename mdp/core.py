"""
Core functionality for working with MDP (Markdown Data Pack) files.

This module provides the main MDPFile class and functions for reading and writing .mdp files.
"""

import os
import uuid
import yaml
import json
import datetime
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any, Set
import jsonschema

from .metadata import extract_metadata, validate_metadata, is_semantic_version, next_version, format_date


class MDPFile:
    """
    Low-level representation of an MDP file with metadata and content.
    """
    def __init__(self, metadata: Dict[str, Any], content: str, path: Optional[str] = None):
        self.metadata = metadata
        self.content = content
        self.path = path

    def to_string(self) -> str:
        """
        Convert the MDP file to a string representation.
        
        Returns:
            str: The string representation of the MDP file.
        """
        metadata_str = yaml.dump(self.metadata, default_flow_style=False, sort_keys=False)
        return f"---\n{metadata_str}---\n\n{self.content}"
    
    def save(self, path: Optional[str] = None) -> str:
        """
        Save the MDP file to disk.
        
        Args:
            path (Optional[str]): The path to save the file to. If None, uses the path from the object.
            
        Returns:
            str: The path where the file was saved.
            
        Raises:
            ValueError: If no path is provided and the object doesn't have a path.
        """
        if path is None:
            if self.path is None:
                raise ValueError("No path specified for saving the MDP file")
            path = self.path
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_string())
        
        self.path = path
        return path
    
    @classmethod
    def from_string(cls, content: str, path: Optional[str] = None) -> 'MDPFile':
        """
        Create an MDPFile object from a string.
        
        Args:
            content (str): The MDP file content as a string.
            path (Optional[str]): The path to associate with the MDPFile.
            
        Returns:
            MDPFile: A new MDPFile instance.
        """
        metadata, content = extract_metadata(content)
        return cls(metadata, content, path)
    
    @classmethod
    def from_file(cls, path: str) -> 'MDPFile':
        """
        Create an MDPFile object from a file.
        
        Args:
            path (str): The path to the MDP file.
            
        Returns:
            MDPFile: A new MDPFile instance.
            
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        return read_mdp(path)


def read_mdp(path: str) -> MDPFile:
    """
    Read an MDP file from disk.
    
    Args:
        path (str): Path to the MDP file.
        
    Returns:
        MDPFile: An MDPFile object with the metadata and content from the file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata, doc_content = extract_metadata(content)
    return MDPFile(metadata, doc_content, path)


def write_mdp(path: str, metadata: Dict[str, Any], content: str) -> MDPFile:
    """
    Write metadata and content to a file in MDP format.
    
    Args:
        path (str): Path to save the MDP file.
        metadata (Dict[str, Any]): Metadata to include in the MDP file.
        content (str): Content to include in the MDP file.
        
    Returns:
        MDPFile: The MDPFile object that was saved.
    """
    mdp_file = MDPFile(metadata, content)
    mdp_file.save(path)
    return mdp_file


def extract_metadata(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML metadata from a string containing an MDP document.
    
    Args:
        content (str): The MDP document content including metadata.
        
    Returns:
        Tuple[Dict[str, Any], str]: A tuple containing the metadata dictionary and the content.
        
    Raises:
        ValueError: If the metadata section is not properly formatted.
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)'
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        # No metadata section found, or improperly formatted
        return {}, content
    
    yaml_str = match.group(1)
    remaining_content = match.group(2)
    
    try:
        metadata = yaml.safe_load(yaml_str) or {}
        return metadata, remaining_content.lstrip()
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing metadata YAML: {e}")


def validate_metadata(metadata: Dict[str, Any], schema_path: Optional[str] = None) -> bool:
    """
    Validate metadata against the MDP schema.
    
    Args:
        metadata (Dict[str, Any]): The metadata to validate.
        schema_path (Optional[str]): Path to a custom schema file. If None, uses the standard schema.
        
    Returns:
        bool: True if validation passes.
        
    Raises:
        ValidationError: If validation fails.
        FileNotFoundError: If the schema file does not exist.
    """
    if schema_path is None:
        # Use the standard schema
        schema_path = os.path.join(os.path.dirname(__file__), 'schema', 'mdp_schema.json')
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    try:
        jsonschema.validate(instance=metadata, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        # Re-raise with a clearer error message
        from .exceptions import ValidationError
        raise ValidationError(f"Metadata validation failed: {e.message}")


def create_document(title: str, 
                    content: str, 
                    path: str, 
                    author: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    relationships: Optional[List[Dict[str, Any]]] = None,
                    **metadata) -> MDPFile:
    """
    Create a new MDP document with provided metadata and content.
    
    Args:
        title (str): Document title.
        content (str): Document content.
        path (str): Path to save the document.
        author (Optional[str]): Document author.
        tags (Optional[List[str]]): List of tags.
        relationships (Optional[List[Dict[str, Any]]]): List of document relationships.
        **metadata: Additional metadata fields.
        
    Returns:
        MDPFile: The created MDP document.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Set up basic metadata
    doc_metadata = {
        "title": title,
        "created_at": now,
        "updated_at": now,
        "uuid": str(uuid.uuid4()),
    }
    
    # Add optional fields if provided
    if author:
        doc_metadata["author"] = author
    if tags:
        doc_metadata["tags"] = tags
    if relationships:
        doc_metadata["relationships"] = relationships
    
    # Add any additional metadata
    doc_metadata.update(metadata)
    
    # Create and save the document
    return write_mdp(path, doc_metadata, content)


def update_document(path: str, 
                   content: Optional[str] = None, 
                   **metadata) -> MDPFile:
    """
    Update an existing MDP document.
    
    Args:
        path (str): Path to the document to update.
        content (Optional[str]): New content for the document. If None, keeps existing content.
        **metadata: Metadata fields to update.
        
    Returns:
        MDPFile: The updated MDP document.
        
    Raises:
        FileNotFoundError: If the document does not exist.
    """
    # Read the existing document
    mdp_file = read_mdp(path)
    
    # Update the metadata
    if metadata:
        mdp_file.metadata.update(metadata)
        mdp_file.metadata["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Update the content if provided
    if content is not None:
        mdp_file.content = content
    
    # Save the updated document
    mdp_file.save()
    return mdp_file


def delete_document(path: str) -> bool:
    """
    Delete an MDP document.
    
    Args:
        path (str): Path to the document to delete.
        
    Returns:
        bool: True if the document was deleted, False if it didn't exist.
    """
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return False


def list_documents(directory: str, recursive: bool = True) -> List[str]:
    """
    List all MDP documents in a directory.
    
    Args:
        directory (str): Directory to search for MDP documents.
        recursive (bool): Whether to search subdirectories recursively.
        
    Returns:
        List[str]: A list of paths to MDP documents.
    """
    mdp_files = []
    
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.mdp'):
                    mdp_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            if file.endswith('.mdp') and os.path.isfile(os.path.join(directory, file)):
                mdp_files.append(os.path.join(directory, file))
    
    return mdp_files


def batch_update_documents(directory: str, 
                          update_func: callable, 
                          recursive: bool = True) -> Dict[str, str]:
    """
    Apply an update function to multiple MDP documents.
    
    Args:
        directory (str): Directory containing the documents to update.
        update_func (callable): Function that takes an MDPFile and returns an updated MDPFile.
        recursive (bool): Whether to process subdirectories recursively.
        
    Returns:
        Dict[str, str]: A dictionary mapping file paths to success/error messages.
    """
    results = {}
    documents = list_documents(directory, recursive)
    
    for doc_path in documents:
        try:
            mdp_file = read_mdp(doc_path)
            updated_file = update_func(mdp_file)
            updated_file.save()
            results[doc_path] = "Updated successfully"
        except Exception as e:
            results[doc_path] = f"Error: {str(e)}"
    
    return results


def add_relationship(doc_path: str, 
                    rel_type: str, 
                    target_path: str, 
                    title: Optional[str] = None, 
                    **rel_metadata) -> MDPFile:
    """
    Add a relationship to an MDP document.
    
    Args:
        doc_path (str): Path to the document to update.
        rel_type (str): Type of relationship ('parent', 'child', 'related', etc.).
        target_path (str): Path to the target document.
        title (Optional[str]): Title of the target document.
        **rel_metadata: Additional metadata for the relationship.
        
    Returns:
        MDPFile: The updated MDP document.
        
    Raises:
        FileNotFoundError: If the document does not exist.
    """
    mdp_file = read_mdp(doc_path)
    
    # Create the relationship object
    relationship = {
        "type": rel_type,
        "path": target_path
    }
    
    if title:
        relationship["title"] = title
    
    # Add any additional metadata
    relationship.update(rel_metadata)
    
    # Add the relationship to the document
    if "relationships" not in mdp_file.metadata:
        mdp_file.metadata["relationships"] = []
    
    mdp_file.metadata["relationships"].append(relationship)
    mdp_file.metadata["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Save the updated document
    mdp_file.save()
    return mdp_file


def create_collection(collection_id: str, 
                     name: str, 
                     path: str,
                     description: Optional[str] = None, 
                     **metadata) -> MDPFile:
    """
    Create a new MDP collection.
    
    Args:
        collection_id (str): Unique identifier for the collection.
        name (str): Name of the collection.
        path (str): Path to save the collection file.
        description (Optional[str]): Description of the collection.
        **metadata: Additional metadata for the collection.
        
    Returns:
        MDPFile: The created collection file.
    """
    # Set up collection metadata
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    coll_metadata = {
        "id": collection_id,
        "name": name,
        "created_at": now,
        "updated_at": now,
        "documents": []
    }
    
    if description:
        coll_metadata["description"] = description
    
    # Add any additional metadata
    coll_metadata.update(metadata)
    
    # Create empty content for the collection file
    content = f"# {name}\n\n"
    if description:
        content += f"{description}\n\n"
    content += "This is a collection of MDP documents."
    
    # Create and save the collection file
    return write_mdp(path, coll_metadata, content)


def add_document_to_collection(collection_path: str, document_path: str, position: Optional[int] = None) -> MDPFile:
    """
    Add a document to an MDP collection.
    
    Args:
        collection_path (str): Path to the collection file.
        document_path (str): Path to the document to add.
        position (Optional[int]): Position of the document in the collection.
        
    Returns:
        MDPFile: The updated collection file.
        
    Raises:
        FileNotFoundError: If the collection or document does not exist.
    """
    # Read the collection file
    collection = read_mdp(collection_path)
    
    # Make sure the documents field exists
    if "documents" not in collection.metadata:
        collection.metadata["documents"] = []
    
    # Check if the document is already in the collection
    if document_path in collection.metadata["documents"]:
        return collection
    
    # Add the document at the specified position, or at the end
    if position is not None:
        collection.metadata["documents"].insert(position, document_path)
    else:
        collection.metadata["documents"].append(document_path)
    
    # Update the collection's last updated time
    collection.metadata["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Save the updated collection
    collection.save()
    
    # Add collection metadata to the document
    try:
        document = read_mdp(document_path)
        document.metadata["collection"] = collection.metadata["name"]
        document.metadata["collection_id"] = collection.metadata["id"]
        if position is not None:
            document.metadata["position"] = position
        document.metadata["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
        document.save()
    except FileNotFoundError:
        pass  # Document might not exist yet
    
    return collection


def remove_document_from_collection(collection_path: str, document_path: str) -> MDPFile:
    """
    Remove a document from an MDP collection.
    
    Args:
        collection_path (str): Path to the collection file.
        document_path (str): Path to the document to remove.
        
    Returns:
        MDPFile: The updated collection file.
        
    Raises:
        FileNotFoundError: If the collection does not exist.
    """
    # Read the collection file
    collection = read_mdp(collection_path)
    
    # Remove the document if it exists in the collection
    if "documents" in collection.metadata and document_path in collection.metadata["documents"]:
        collection.metadata["documents"].remove(document_path)
        collection.metadata["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
        collection.save()
        
        # Update the document to remove collection metadata
        try:
            document = read_mdp(document_path)
            if "collection" in document.metadata:
                del document.metadata["collection"]
            if "collection_id" in document.metadata:
                del document.metadata["collection_id"]
            if "position" in document.metadata:
                del document.metadata["position"]
            document.metadata["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
            document.save()
        except FileNotFoundError:
            pass  # Document might not exist
    
    return collection


def get_collection_documents(collection_path: str) -> List[MDPFile]:
    """
    Get all documents in an MDP collection.
    
    Args:
        collection_path (str): Path to the collection file.
        
    Returns:
        List[MDPFile]: A list of MDPFile objects for all documents in the collection.
        
    Raises:
        FileNotFoundError: If the collection does not exist.
    """
    # Read the collection file
    collection = read_mdp(collection_path)
    
    # Get all documents in the collection
    documents = []
    if "documents" in collection.metadata:
        for doc_path in collection.metadata["documents"]:
            try:
                document = read_mdp(doc_path)
                documents.append(document)
            except FileNotFoundError:
                continue  # Skip documents that don't exist
    
    return documents


def find_relationships(document_path: str, rel_type: Optional[str] = None) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Find all relationships for an MDP document.
    
    Args:
        document_path (str): Path to the document.
        rel_type (Optional[str]): Type of relationships to find. If None, returns all relationships.
        
    Returns:
        List[Tuple[str, Dict[str, Any]]]: A list of tuples with (path, relationship metadata).
        
    Raises:
        FileNotFoundError: If the document does not exist.
    """
    # Read the document
    document = read_mdp(document_path)
    
    # Find all relationships
    relationships = []
    if "relationships" in document.metadata:
        for rel in document.metadata["relationships"]:
            if rel_type is None or rel.get("type") == rel_type:
                # Get the path from the relationship
                rel_path = rel.get("path")
                if rel_path:
                    relationships.append((rel_path, rel))
    
    return relationships


def find_documents_by_metadata(directory: str, 
                              query: Dict[str, Any], 
                              recursive: bool = True) -> List[MDPFile]:
    """
    Find documents matching specific metadata criteria.
    
    Args:
        directory (str): Directory to search for documents.
        query (Dict[str, Any]): Metadata criteria to match.
        recursive (bool): Whether to search subdirectories recursively.
        
    Returns:
        List[MDPFile]: A list of MDPFile objects matching the criteria.
    """
    matching_docs = []
    
    # Get all documents in the directory
    for doc_path in list_documents(directory, recursive):
        try:
            document = read_mdp(doc_path)
            
            # Check if the document matches all criteria
            matches = True
            for key, value in query.items():
                # Handle nested keys (e.g., "metadata.author")
                if "." in key:
                    parts = key.split(".")
                    doc_value = document.metadata
                    for part in parts:
                        if part in doc_value:
                            doc_value = doc_value[part]
                        else:
                            matches = False
                            break
                    if not matches:
                        break
                    
                    # Handle list comparisons for nested keys
                    if isinstance(value, list) and isinstance(doc_value, list):
                        if not all(v in doc_value for v in value):
                            matches = False
                            break
                    elif doc_value != value:
                        matches = False
                        break
                # Handle simple keys
                elif key not in document.metadata:
                    matches = False
                    break
                # Handle list comparisons for tags and other list fields
                elif isinstance(value, list) and isinstance(document.metadata[key], list):
                    if not all(v in document.metadata[key] for v in value):
                        matches = False
                        break
                elif document.metadata[key] != value:
                    matches = False
                    break
            
            if matches:
                matching_docs.append(document)
        except Exception:
            continue  # Skip documents that can't be read or processed
    
    return matching_docs


def get_document_history(document_path: str, versions_dir: str) -> List[str]:
    """
    Get the list of all versions of a document.
    
    This function is deprecated and maintained for backward compatibility.
    Use the VersionManager class from the versioning module instead.
    
    Args:
        document_path (str): Path to the document.
        versions_dir (str): Directory where versions are stored.
        
    Returns:
        List[str]: List of paths to version files, sorted by date (newest first).
    """
    import warnings
    from .versioning import get_version_manager
    
    warnings.warn(
        "get_document_history is deprecated. Use VersionManager.list_versions instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Use the new versioning system
    vm = get_version_manager(document_path)
    
    try:
        # Try to get versions from the new system first
        versions = vm.list_versions(document_path)
        if versions:
            # Return paths from version entries
            return [v.get("path", "") for v in versions if "path" in v]
    except Exception:
        pass
    
    # Fall back to the old system
    base_name = os.path.basename(document_path)
    name, ext = os.path.splitext(base_name)
    
    # Look for version files
    version_pattern = f"{name}.*.{ext}"
    versions = []
    
    if os.path.exists(versions_dir):
        for file in os.listdir(versions_dir):
            if re.match(version_pattern, file):
                versions.append(os.path.join(versions_dir, file))
    
    # Sort versions by date in the filename
    def get_version_date(file_path):
        match = re.search(r'\.(\d{4}-\d{2}-\d{2})\.', file_path)
        if match:
            return match.group(1)
        return ""
    
    versions.sort(key=get_version_date, reverse=True)
    return versions


def create_document_version(document_path: str, versions_dir: str, version: Optional[str] = None, 
                           author: Optional[str] = None, description: Optional[str] = None) -> str:
    """
    Create a new version of an MDP document.
    
    This function is deprecated and maintained for backward compatibility.
    Use the VersionManager class from the versioning module instead.
    
    Args:
        document_path (str): Path to the document.
        versions_dir (str): Directory to store the version.
        version (Optional[str]): Semantic version string (e.g., "1.0.0"). If None, auto-increments.
        author (Optional[str]): Author of this version.
        description (Optional[str]): Description of changes in this version.
        
    Returns:
        str: Path to the created version file.
        
    Raises:
        FileNotFoundError: If the document does not exist.
    """
    import warnings
    from .versioning import get_version_manager
    
    warnings.warn(
        "create_document_version is deprecated. Use VersionManager.create_version instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Use the new versioning system
    vm = get_version_manager(document_path)
    
    # Determine version if not provided
    if not version:
        # Read the document to get current version
        document = read_mdp(document_path)
        current_version = document.metadata.get("version", "0.0.0")
        
        # If current version isn't a semantic version, start at 0.1.0
        if not is_semantic_version(current_version):
            version = "0.1.0"
        else:
            # Increment patch version
            version = next_version(current_version, 'patch')
    
    # Create version using new system
    return vm.create_version(document_path, version, author, description)


def compare_documents(doc1_path: str, doc2_path: str) -> Dict[str, Any]:
    """
    Compare two MDP documents and find differences.
    
    Args:
        doc1_path (str): Path to the first document.
        doc2_path (str): Path to the second document.
        
    Returns:
        Dict[str, Any]: A dictionary with differences in metadata and content.
        
    Raises:
        FileNotFoundError: If either document does not exist.
    """
    # Read both documents
    doc1 = read_mdp(doc1_path)
    doc2 = read_mdp(doc2_path)
    
    # Compare metadata
    metadata_diff = {
        "added": {},
        "removed": {},
        "changed": {}
    }
    
    # Find added and changed fields
    for key, value in doc2.metadata.items():
        if key not in doc1.metadata:
            metadata_diff["added"][key] = value
        elif doc1.metadata[key] != value:
            metadata_diff["changed"][key] = {
                "old": doc1.metadata[key],
                "new": value
            }
    
    # Find removed fields
    for key in doc1.metadata:
        if key not in doc2.metadata:
            metadata_diff["removed"][key] = doc1.metadata[key]
    
    # Compare content (simple string comparison)
    content_changed = doc1.content != doc2.content
    
    return {
        "metadata_diff": metadata_diff,
        "content_changed": content_changed
    }


def copy_metadata(source_path: str, target_path: str, fields: Optional[List[str]] = None) -> MDPFile:
    """
    Copy metadata from one MDP document to another.
    
    Args:
        source_path (str): Path to the source document.
        target_path (str): Path to the target document.
        fields (Optional[List[str]]): List of fields to copy. If None, copies all fields.
        
    Returns:
        MDPFile: The updated target document.
        
    Raises:
        FileNotFoundError: If either document does not exist.
    """
    # Read both documents
    source = read_mdp(source_path)
    target = read_mdp(target_path)
    
    # Copy the specified fields (or all fields)
    if fields is None:
        # Copy all fields except unique identifiers
        excluded_fields = {"uuid", "path", "created_at"}
        for key, value in source.metadata.items():
            if key not in excluded_fields:
                target.metadata[key] = value
    else:
        # Copy only the specified fields
        for field in fields:
            if field in source.metadata:
                target.metadata[field] = source.metadata[field]
    
    # Update the 'updated_at' field
    target.metadata["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Save the updated target document
    target.save()
    return target 