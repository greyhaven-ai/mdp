"""
Metadata handling for MDP (Markdown Data Pack) files.

This module provides functions for extracting and validating metadata from MDP files.
"""

import re
import datetime
import uuid
from typing import Any, Dict, List, Tuple, Union, Optional

import yaml


# Regular expression to match YAML frontmatter
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Date format for standardized date fields (ISO 8601)
DATE_FORMAT = "%Y-%m-%d"

# Regular expression for validating IPFS CID v0 and v1
IPFS_CID_V0_PATTERN = re.compile(r"^Qm[1-9A-HJ-NP-Za-km-z]{44}$")
IPFS_CID_V1_PATTERN = re.compile(r"^b[a-zA-Z0-9]{58,}$")

# Regular expression for validating semantic versioning (MAJOR.MINOR.PATCH)
SEMVER_PATTERN = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')

# Standard metadata fields with descriptions and types
STANDARD_METADATA_FIELDS = {
    # Core fields
    "title": {"description": "The title of the document", "type": str, "required": True},
    "version": {"description": "The version of the document", "type": str, "required": False},
    "context": {"description": "Additional context about the document, its purpose, and how it should be used", "type": str, "required": False},
    
    # Document identification fields
    "uuid": {"description": "Globally unique identifier for the document", "type": str, "required": False},
    "uri": {"description": "URI reference for the document in a registry", "type": str, "required": False},
    "local_path": {"description": "Local filesystem path relative to a defined root", "type": str, "required": False},
    "cid": {"description": "IPFS Content Identifier (CID) for content addressing", "type": str, "required": False},
    
    # Collection fields
    "collection": {"description": "Collection this document belongs to", "type": str, "required": False},
    "collection_id": {"description": "Unique identifier for the collection", "type": str, "required": False},
    "collection_id_type": {
        "description": "Type of identifier used for collection_id (uuid, uri, cid, string)", 
        "type": str, 
        "required": False,
        "enum": ["uuid", "uri", "cid", "string"]
    },
    "position": {"description": "Position in an ordered collection", "type": int, "required": False},
    
    # Authorship fields
    "author": {"description": "The author of the document", "type": str, "required": False},
    "contributors": {"description": "List of contributors to the document", "type": list, "required": False},
    "created_at": {
        "description": "The creation date of the document (ISO 8601: YYYY-MM-DD)", 
        "type": str, 
        "required": False,
        "format": "date"
    },
    "updated_at": {
        "description": "The last update date of the document (ISO 8601: YYYY-MM-DD)", 
        "type": str, 
        "required": False,
        "format": "date"
    },
    
    # Classification fields
    "tags": {"description": "List of tags for categorizing the document", "type": list, "required": False},
    "status": {"description": "The status of the document (e.g., draft, published)", "type": str, "required": False},
    
    # Source fields
    "source_file": {"description": "The original file name if converted", "type": str, "required": False},
    "source_type": {"description": "The original file type if converted", "type": str, "required": False},
    "source_url": {"description": "The URL of the original content if applicable", "type": str, "required": False},
    
    # Relationship fields
    "relationships": {"description": "References to related documents", "type": list, "required": False},
}

# Required metadata fields
REQUIRED_METADATA_FIELDS: List[str] = [
    field for field, info in STANDARD_METADATA_FIELDS.items() if info["required"]
]

# Optional metadata fields with default values
DEFAULT_METADATA: Dict[str, Any] = {
    "created_at": datetime.date.today().strftime(DATE_FORMAT),
}

# Custom field namespace prefix
CUSTOM_NAMESPACE_PREFIX = "x_"

# Define valid relationship types
VALID_RELATIONSHIP_TYPES = [
    "parent",   # Document that contains or encompasses this document
    "child",    # Document that is contained by or elaborates on this document 
    "related",  # Document with a non-hierarchical connection
    "reference" # External standard or resource
]

# Define IPFS URI prefix
IPFS_URI_PREFIX = "ipfs://"

# Valid collection ID types
VALID_COLLECTION_ID_TYPES = ["uuid", "uri", "cid", "string"]

def is_custom_field(field_name: str) -> bool:
    """
    Check if a field name is in the custom namespace.
    
    Args:
        field_name: The name of the field to check.
    
    Returns:
        True if the field is in the custom namespace, False otherwise.
    """
    return field_name.startswith(CUSTOM_NAMESPACE_PREFIX)


def validate_date_format(date_str: str) -> bool:
    """
    Validate that a string is in the correct date format.
    
    Args:
        date_str: The date string to validate.
    
    Returns:
        True if the date is valid, False otherwise.
    """
    try:
        datetime.datetime.strptime(date_str, DATE_FORMAT)
        return True
    except ValueError:
        return False


def is_valid_ipfs_cid(cid: str) -> bool:
    """
    Check if a string is a valid IPFS Content Identifier (CID).
    
    Args:
        cid: The string to check.
    
    Returns:
        True if the string is a valid IPFS CID, False otherwise.
    """
    # Check for CIDv0 (Qm...) or CIDv1 (b...)
    return bool(IPFS_CID_V0_PATTERN.match(cid) or IPFS_CID_V1_PATTERN.match(cid))


def create_ipfs_uri(cid: str) -> str:
    """
    Create an IPFS URI from a CID.
    
    Args:
        cid: The IPFS Content Identifier.
    
    Returns:
        An IPFS URI in the format "ipfs://CID".
        
    Raises:
        ValueError: If the CID is invalid.
    """
    if not is_valid_ipfs_cid(cid):
        raise ValueError(f"Invalid IPFS CID: {cid}")
    
    return f"{IPFS_URI_PREFIX}{cid}"


def extract_cid_from_ipfs_uri(uri: str) -> str:
    """
    Extract the CID from an IPFS URI.
    
    Args:
        uri: The IPFS URI, e.g., "ipfs://QmX5f..."
    
    Returns:
        The CID portion of the URI.
        
    Raises:
        ValueError: If the URI is not a valid IPFS URI.
    """
    if not uri.startswith(IPFS_URI_PREFIX):
        raise ValueError(f"Not a valid IPFS URI: {uri}. Must start with '{IPFS_URI_PREFIX}'")
    
    cid = uri[len(IPFS_URI_PREFIX):]
    
    if not is_valid_ipfs_cid(cid):
        raise ValueError(f"Invalid CID in IPFS URI: {cid}")
    
    return cid


def extract_metadata(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract metadata and content from an MDP file string.
    
    Args:
        content: The content of the MDP file as a string.
    
    Returns:
        A tuple containing the metadata dictionary and the markdown content.
    
    Raises:
        ValueError: If the content does not contain valid YAML frontmatter.
    """
    # Check if the content starts with YAML frontmatter
    match = FRONTMATTER_PATTERN.match(content)
    
    if not match:
        # If no frontmatter is found, return empty metadata and the original content
        return DEFAULT_METADATA.copy(), content
    
    # Extract the YAML frontmatter and the remaining content
    frontmatter_str = match.group(1)
    markdown_content = content[match.end():]
    
    try:
        # Parse the YAML frontmatter
        metadata = yaml.safe_load(frontmatter_str) or {}
        
        # Apply default values for missing fields
        for key, value in DEFAULT_METADATA.items():
            if key not in metadata:
                metadata[key] = value
        
        return metadata, markdown_content
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")


def is_semantic_version(version_str: str) -> bool:
    """
    Check if a string is a valid semantic version (MAJOR.MINOR.PATCH).
    
    Args:
        version_str: The string to check.
    
    Returns:
        True if the string is a valid semantic version, False otherwise.
    """
    return bool(SEMVER_PATTERN.match(version_str))


def compare_semantic_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic versions.
    
    Args:
        version1: First semantic version string.
        version2: Second semantic version string.
        
    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
        
    Raises:
        ValueError: If either version string is not a valid semantic version.
    """
    if not is_semantic_version(version1):
        raise ValueError(f"Invalid semantic version: {version1}")
    if not is_semantic_version(version2):
        raise ValueError(f"Invalid semantic version: {version2}")
    
    parts1 = [int(part) for part in version1.split('.')]
    parts2 = [int(part) for part in version2.split('.')]
    
    for p1, p2 in zip(parts1, parts2):
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1
    
    return 0


def next_version(current_version: str, version_type: str = 'patch') -> str:
    """
    Calculate the next version based on semantic versioning.
    
    Args:
        current_version: The current semantic version.
        version_type: The type of version increment ('major', 'minor', or 'patch').
        
    Returns:
        The next semantic version string.
        
    Raises:
        ValueError: If the current version is not a valid semantic version or
                    version_type is invalid.
    """
    if not is_semantic_version(current_version):
        raise ValueError(f"Invalid semantic version: {current_version}")
    
    if version_type not in ('major', 'minor', 'patch'):
        raise ValueError(f"Invalid version type: {version_type}. Must be 'major', 'minor', or 'patch'")
    
    major, minor, patch = map(int, current_version.split('.'))
    
    if version_type == 'major':
        return f"{major + 1}.0.0"
    elif version_type == 'minor':
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate metadata from an MDP file.
    
    Args:
        metadata: The metadata dictionary to validate.
    
    Returns:
        A dictionary with validation results containing:
        - valid: Boolean indicating if the metadata is valid
        - errors: List of error messages if validation failed
    """
    valid = True
    errors = {}
    
    # Check for required fields
    for field in REQUIRED_METADATA_FIELDS:
        if field not in metadata:
            valid = False
            errors[field] = f"Missing required field"
    
    # Validate field types for standard fields
    for field, value in metadata.items():
        # Skip validation for custom fields
        if is_custom_field(field):
            continue
            
        if field in STANDARD_METADATA_FIELDS:
            field_info = STANDARD_METADATA_FIELDS[field]
            expected_type = field_info["type"]
            
            # Validate type
            if value is not None and not isinstance(value, expected_type):
                valid = False
                errors[field] = f"Invalid type: expected {expected_type.__name__}, got {type(value).__name__}"
            
            # Validate date format if applicable
            if value is not None and field_info.get("format") == "date" and isinstance(value, str):
                if not validate_date_format(value):
                    valid = False
                    errors[field] = f"Invalid date format: expected format {DATE_FORMAT} (e.g., 2023-05-15)"
            
            # Validate enum values if applicable
            if value is not None and "enum" in field_info and value not in field_info["enum"]:
                valid = False
                errors[field] = f"Invalid value: must be one of {field_info['enum']}"
    
    # Validate UUID if present
    if "uuid" in metadata and metadata["uuid"] and not is_valid_uuid(metadata["uuid"]):
        valid = False
        errors["uuid"] = f"Invalid UUID format: {metadata['uuid']}"
    
    # Validate URI if present
    if "uri" in metadata and metadata["uri"]:
        try:
            parse_uri(metadata["uri"])
        except ValueError as e:
            valid = False
            errors["uri"] = f"Invalid URI format: {str(e)}"
    
    # Validate version if present (check for semantic versioning)
    if "version" in metadata and metadata["version"]:
        if not is_semantic_version(metadata["version"]):
            valid = False
            errors["version"] = f"Invalid version format: {metadata['version']}. Expected semantic version (e.g., 1.0.0)"
    
    # Validate CID if present
    if "cid" in metadata and metadata["cid"] and not is_valid_ipfs_cid(metadata["cid"]):
        valid = False
        errors["cid"] = f"Invalid IPFS CID format: {metadata['cid']}"
    
    # Validate collection_id based on collection_id_type if both are present
    if "collection_id" in metadata and metadata["collection_id"]:
        collection_id = metadata["collection_id"]
        collection_id_type = metadata.get("collection_id_type", "string")
        
        if collection_id_type not in VALID_COLLECTION_ID_TYPES:
            valid = False
            errors["collection_id_type"] = f"Invalid collection ID type: {collection_id_type}. Must be one of: {', '.join(VALID_COLLECTION_ID_TYPES)}"
        
        # Validate based on collection_id_type
        if collection_id_type == "uuid" and not is_valid_uuid(collection_id):
            valid = False
            errors["collection_id"] = f"Invalid UUID format for collection_id: {collection_id}"
        elif collection_id_type == "uri":
            try:
                parse_uri(collection_id)
            except ValueError as e:
                valid = False
                errors["collection_id"] = f"Invalid URI format for collection_id: {str(e)}"
        elif collection_id_type == "cid" and not is_valid_ipfs_cid(collection_id):
            valid = False
            errors["collection_id"] = f"Invalid IPFS CID format for collection_id: {collection_id}"
    
    # Validate relationships if present
    if "relationships" in metadata and metadata["relationships"]:
        try:
            validate_relationships(metadata["relationships"])
        except ValueError as e:
            valid = False
            errors["relationships"] = str(e)
    
    # Validate position is positive if present
    if "position" in metadata and metadata["position"] is not None:
        if not isinstance(metadata["position"], int) or metadata["position"] < 0:
            valid = False
            errors["position"] = f"Position must be a non-negative integer, got: {metadata['position']}"
    
    return {
        "valid": valid,
        "errors": errors
    }


def merge_metadata(
    base: Dict[str, Any], 
    override: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge two metadata dictionaries, with override taking precedence.
    
    Args:
        base: The base metadata dictionary.
        override: The override metadata dictionary.
    
    Returns:
        A new metadata dictionary with merged values.
    """
    result = base.copy()
    
    for key, value in override.items():
        # If both dictionaries have the same key and both values are dictionaries,
        # recursively merge them
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_metadata(result[key], value)
        else:
            # Otherwise, override the value
            result[key] = value
    
    return result


def create_metadata(
    metadata: Dict[str, Any] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Create a metadata dictionary with default values.
    
    Args:
        metadata: An optional base metadata dictionary.
        **kwargs: Additional metadata fields to include.
    
    Returns:
        A metadata dictionary with default values applied.
    """
    # Start with default metadata
    result = DEFAULT_METADATA.copy()
    
    # Add a UUID by default if not overridden later
    if "uuid" not in result:
        result["uuid"] = generate_uuid()
    
    # Apply base metadata if provided
    if metadata:
        result = merge_metadata(result, metadata)
    
    # Apply additional fields
    if kwargs:
        result = merge_metadata(result, kwargs)
    
    # Ensure UUID is valid, generate one if not
    result = add_uuid_to_metadata(result)
    
    return result


def get_standard_fields() -> Dict[str, Dict[str, Any]]:
    """
    Get the dictionary of standard metadata fields with their descriptions and types.
    
    Returns:
        A dictionary of standard metadata fields.
    """
    return STANDARD_METADATA_FIELDS.copy()


def create_custom_field(name: str, value: Any) -> Tuple[str, Any]:
    """
    Create a custom metadata field with the appropriate namespace prefix.
    
    Args:
        name: The name of the custom field (without prefix).
        value: The value of the custom field.
    
    Returns:
        A tuple containing the prefixed field name and its value.
    
    Raises:
        ValueError: If the name conflicts with a standard field.
    """
    # Check if the name conflicts with a standard field
    if name in STANDARD_METADATA_FIELDS:
        raise ValueError(f"Custom field name '{name}' conflicts with a standard field. Use a different name.")
    
    # Add the prefix if not already present
    if not name.startswith(CUSTOM_NAMESPACE_PREFIX):
        name = f"{CUSTOM_NAMESPACE_PREFIX}{name}"
    
    return name, value


def get_today_date() -> str:
    """
    Get today's date in the standard format.
    
    Returns:
        Today's date as a string in the standard format.
    """
    return datetime.date.today().strftime(DATE_FORMAT)


def format_date(date_obj: Union[datetime.date, datetime.datetime, str]) -> str:
    """
    Format a date object or string to the standard date format.
    
    Args:
        date_obj: A date object, datetime object, or date string.
    
    Returns:
        A date string in the standard format.
    
    Raises:
        ValueError: If the date_obj is not a valid date or cannot be parsed.
    """
    if isinstance(date_obj, (datetime.date, datetime.datetime)):
        return date_obj.strftime(DATE_FORMAT)
    elif isinstance(date_obj, str):
        try:
            # Try to parse the date string
            parsed_date = datetime.datetime.strptime(date_obj, DATE_FORMAT)
            return parsed_date.strftime(DATE_FORMAT)
        except ValueError:
            # Try a few common formats
            for fmt in ["%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y", "%B %d, %Y"]:
                try:
                    parsed_date = datetime.datetime.strptime(date_obj, fmt)
                    return parsed_date.strftime(DATE_FORMAT)
                except ValueError:
                    continue
            raise ValueError(f"Could not parse date string: {date_obj}. Expected format: {DATE_FORMAT}")
    else:
        raise ValueError(f"Invalid date type: {type(date_obj)}. Expected datetime.date, datetime.datetime, or string.")


def generate_uuid() -> str:
    """
    Generate a new UUID (v4) for document identification.
    
    Returns:
        A string representation of a UUID v4.
    """
    return str(uuid.uuid4())


def is_valid_uuid(uuid_str: str) -> bool:
    """
    Check if a string is a valid UUID.
    
    Args:
        uuid_str: The string to check.
    
    Returns:
        True if the string is a valid UUID, False otherwise.
    """
    try:
        uuid_obj = uuid.UUID(uuid_str)
        return True
    except ValueError:
        return False


def parse_uri(uri: str) -> Dict[str, str]:
    """
    Parse an MDP URI into its components.
    
    Args:
        uri: The URI to parse (e.g., "mdp://organization/project/document")
    
    Returns:
        A dictionary with URI components.
    
    Raises:
        ValueError: If the URI is invalid.
    """
    if not uri.startswith("mdp://"):
        # Check if it's an IPFS URI
        if uri.startswith(IPFS_URI_PREFIX):
            cid = extract_cid_from_ipfs_uri(uri)
            return {
                "uri": uri,
                "protocol": "ipfs",
                "cid": cid
            }
        raise ValueError(f"Invalid MDP URI: {uri}. Must start with 'mdp://' or 'ipfs://'")
    
    # Remove the protocol part
    path = uri[6:]
    
    # Split the path
    components = path.split('/')
    
    result = {
        "uri": uri,
        "protocol": "mdp",
    }
    
    # Map components to fields
    if len(components) > 0:
        result["organization"] = components[0]
    if len(components) > 1:
        result["project"] = components[1]
    if len(components) > 2:
        result["path"] = '/'.join(components[2:])
    
    return result 


def create_relationship(
    reference: str, 
    rel_type: str, 
    title: Optional[str] = None, 
    description: Optional[str] = None,
    is_uri: bool = False,
    is_ipfs_cid: bool = False
) -> Dict[str, Any]:
    """
    Create a relationship entry for the relationships metadata field.
    
    Args:
        reference: The UUID, URI, path, or IPFS CID of the related document
        rel_type: The type of relationship (parent, child, related, reference)
        title: Optional title of the related document
        description: Optional description of the relationship
        is_uri: Whether the reference is a URI (true) or UUID/path (false)
        is_ipfs_cid: Whether the reference is an IPFS CID
    
    Returns:
        A dictionary representing the relationship
        
    Raises:
        ValueError: If the relationship type is invalid
    """
    if rel_type not in VALID_RELATIONSHIP_TYPES:
        raise ValueError(f"Invalid relationship type: {rel_type}. Must be one of: {', '.join(VALID_RELATIONSHIP_TYPES)}")
    
    relationship = {
        "type": rel_type,
    }
    
    # Add the appropriate identifier based on type
    if is_ipfs_cid:
        if not is_valid_ipfs_cid(reference):
            raise ValueError(f"Invalid IPFS CID format: {reference}")
        relationship["cid"] = reference
    elif is_uri:
        relationship["uri"] = reference
    elif is_valid_uuid(reference):
        relationship["id"] = reference
    else:
        relationship["path"] = reference
    
    # Add optional fields if provided
    if title:
        relationship["title"] = title
    if description:
        relationship["description"] = description
    
    return relationship


def validate_relationship(relationship: Dict[str, Any]) -> None:
    """
    Validate a relationship entry.
    
    Args:
        relationship: The relationship dictionary to validate
        
    Raises:
        ValueError: If the relationship is invalid
    """
    # Check that the relationship has a valid type
    if "type" not in relationship:
        raise ValueError("Relationship missing required field: type")
    
    if relationship["type"] not in VALID_RELATIONSHIP_TYPES:
        raise ValueError(f"Invalid relationship type: {relationship['type']}. Must be one of: {', '.join(VALID_RELATIONSHIP_TYPES)}")
    
    # Check that the relationship has at least one valid identifier
    if not any(key in relationship for key in ["id", "uri", "path", "cid"]):
        raise ValueError("Relationship must have at least one of: id, uri, path, or cid")
    
    # Validate UUID if present
    if "id" in relationship and not is_valid_uuid(relationship["id"]):
        raise ValueError(f"Invalid UUID in relationship: {relationship['id']}")
    
    # Validate URI if present
    if "uri" in relationship:
        try:
            parse_uri(relationship["uri"])
        except ValueError as e:
            raise ValueError(f"Invalid URI in relationship: {e}")
    
    # Validate CID if present
    if "cid" in relationship and not is_valid_ipfs_cid(relationship["cid"]):
        raise ValueError(f"Invalid IPFS CID in relationship: {relationship['cid']}")
    
    # Check that other fields have correct types
    if "title" in relationship and not isinstance(relationship["title"], str):
        raise ValueError(f"Invalid type for 'title' in relationship: expected str, got {type(relationship['title']).__name__}")
    
    if "description" in relationship and not isinstance(relationship["description"], str):
        raise ValueError(f"Invalid type for 'description' in relationship: expected str, got {type(relationship['description']).__name__}")


def validate_relationships(relationships: List[Dict[str, Any]]) -> None:
    """
    Validate all relationships in a relationships list.
    
    Args:
        relationships: List of relationship dictionaries to validate
        
    Raises:
        ValueError: If any relationship is invalid
    """
    if not isinstance(relationships, list):
        raise ValueError(f"Relationships field must be a list, got {type(relationships).__name__}")
    
    for index, relationship in enumerate(relationships):
        if not isinstance(relationship, dict):
            raise ValueError(f"Relationship at index {index} must be a dictionary, got {type(relationship).__name__}")
        
        try:
            validate_relationship(relationship)
        except ValueError as e:
            raise ValueError(f"Invalid relationship at index {index}: {e}")


def add_uuid_to_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the metadata has a UUID, generating one if it doesn't exist.
    
    Args:
        metadata: The metadata dictionary to update
        
    Returns:
        The metadata dictionary with a UUID
    """
    if "uuid" not in metadata or not metadata["uuid"]:
        metadata["uuid"] = generate_uuid()
    elif not is_valid_uuid(metadata["uuid"]):
        raise ValueError(f"Invalid UUID in metadata: {metadata['uuid']}")
    
    return metadata 


def create_collection_metadata(
    collection_name: str,
    position: Optional[int] = None,
    collection_id: Optional[str] = None,
    collection_id_type: Optional[str] = "string",
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Create metadata for a document that belongs to a collection.
    
    Args:
        collection_name: The name of the collection
        position: Optional position in the collection
        collection_id: Optional unique identifier for the collection
        collection_id_type: Type of the collection_id (uuid, uri, cid, string)
        **kwargs: Additional metadata fields
        
    Returns:
        Metadata dictionary with collection information
        
    Raises:
        ValueError: If the collection_id_type is invalid or the collection_id doesn't match the specified type
    """
    # Validate collection_id_type
    if collection_id_type not in VALID_COLLECTION_ID_TYPES:
        raise ValueError(f"Invalid collection_id_type: {collection_id_type}. Must be one of: {', '.join(VALID_COLLECTION_ID_TYPES)}")
    
    # Validate collection_id if provided
    if collection_id:
        if collection_id_type == "uuid" and not is_valid_uuid(collection_id):
            raise ValueError(f"Invalid UUID format for collection_id: {collection_id}")
        elif collection_id_type == "uri":
            try:
                parse_uri(collection_id)
            except ValueError as e:
                raise ValueError(f"Invalid URI format for collection_id: {str(e)}")
        elif collection_id_type == "cid" and not is_valid_ipfs_cid(collection_id):
            raise ValueError(f"Invalid IPFS CID format for collection_id: {collection_id}")
    
    # Create base metadata with other provided fields
    metadata = create_metadata(**kwargs)
    
    # Add collection information
    metadata["collection"] = collection_name
    
    if collection_id:
        metadata["collection_id"] = collection_id
        metadata["collection_id_type"] = collection_id_type
    
    if position is not None:
        if not isinstance(position, int) or position < 0:
            raise ValueError("Position must be a non-negative integer")
        metadata["position"] = position
    
    return metadata


def add_relationship_to_metadata(
    metadata: Dict[str, Any],
    relationship: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a relationship to metadata.
    
    Args:
        metadata: The metadata dictionary to update
        relationship: The relationship to add, created with create_relationship
        
    Returns:
        Updated metadata dictionary
    """
    # Validate the relationship
    validate_relationship(relationship)
    
    # Initialize relationships list if it doesn't exist
    if "relationships" not in metadata:
        metadata["relationships"] = []
    
    # Add the relationship
    metadata["relationships"].append(relationship)
    
    return metadata


def create_uri(
    *args,
    scheme: Optional[str] = "mdp",
    organization: Optional[str] = None,
    project: Optional[str] = None,
    path: Optional[str] = None
) -> str:
    """
    Create a URI from components.
    
    Args:
        *args: Backward compatibility for positional args (organization, project, path)
        scheme: The URI scheme ('mdp' or 'ipfs')
        organization: The organization name (for mdp URIs)
        project: The project name (for mdp URIs)
        path: The document path or CID
        
    Returns:
        A properly formatted URI
        
    Raises:
        ValueError: If the components are invalid
    """
    # Handle backward compatibility with positional args
    if args:
        if len(args) == 1:
            # If a single positional arg is passed, it's likely a CID for an IPFS URI
            return f"ipfs://{args[0]}"
        elif len(args) == 3:
            # If three positional args are passed, they're organization, project, path
            organization, project, path = args
            scheme = "mdp"
    
    if scheme == "ipfs":
        if not path:
            raise ValueError("Path (CID) is required for IPFS URIs")
        if not is_valid_ipfs_cid(path):
            raise ValueError(f"Invalid IPFS CID: {path}")
        return f"ipfs://{path}"
    elif scheme == "mdp":
        # Validate and sanitize components
        for component in [organization, project]:
            if component and '/' in component:
                raise ValueError(f"URI component cannot contain '/': {component}")
        
        if not all([organization, project, path]):
            raise ValueError("Organization, project, and path are required for MDP URIs")
        
        return f"mdp://{organization}/{project}/{path}"
    else:
        raise ValueError(f"Unsupported URI scheme: {scheme}. Must be 'mdp' or 'ipfs'") 