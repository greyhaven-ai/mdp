# MDP Python API Reference

This document provides an overview of the public Python API for the MDP (Markdown Data Pack) format.

## Core Modules

MDP consists of several core modules:

- `mdp.core` - Basic operations for reading and writing MDP files
- `mdp.document` - High-level document operations
- `mdp.metadata` - Metadata functionality
- `mdp.collection` - Collection management
- `mdp.relationships` - Handles relationships between documents
- `mdp.validators` - Field validation

## Document Class

The `Document` class provides a high-level interface for working with MDP files.

```python
from mdp.document import Document

# Create a new document
doc = Document.create(
    title="My Document",
    content="# My Document\n\nThis is my document content.",
    tags=["sample", "documentation"],
    created_at="2024-07-01"
)

# Access document properties
print(doc.title)  # "My Document"
print(doc.path)   # None (not saved yet)
print(doc.tags)   # ["sample", "documentation"]

# Save the document
doc.save("my_document.mdp")

# Load a document
doc = Document.from_file("my_document.mdp")

# Access metadata
print(doc.metadata["created_at"])  # "2024-07-01"

# Update content
doc.content = "# Updated Content\n\nThis is the updated content."

# Save the updated document
doc.save()
```

## Core Classes

### Document

The `Document` class represents an MDP document with metadata and content.

```python
import mdp

# Create a new document
doc = mdp.Document(
    content="# My Document\n\nThis is the content.",
    metadata={
        "title": "My Document",
        "author": "Author Name",
        "created_at": "2024-07-01"
    }
)

# Save the document
doc.save("my_document.mdp")

# Load an existing document
doc = mdp.Document.load("my_document.mdp")

# Access metadata directly
print(doc.title)  # Shorthand for doc.metadata["title"]
print(doc.metadata["author"])

# Modify metadata
doc.title = "Updated Title"
doc.metadata["updated_at"] = "2024-07-02"

# Access content
print(doc.content)

# Modify content
doc.content = "# Updated Title\n\nContent has been modified."

# Validate the document
doc.validate()

# Get document relationships
relationships = doc.relationships

# Add a relationship
doc.add_relationship(
    type="related",
    path="another_document.mdp",
    title="Another Document"
)

# Remove a relationship
doc.remove_relationship(index=0)  # Remove first relationship
```

### Collection

The `Collection` class manages groups of related documents.

```python
import mdp

# Create a new collection
collection = mdp.Collection(
    id="user-manual",
    name="User Manual",
    description="Complete user documentation"
)

# Add documents to the collection
collection.add_document("chapter1.mdp")
collection.add_document("chapter2.mdp", position=2)

# Save collection metadata
collection.save("user-manual.collection.mdp")

# Load an existing collection
collection = mdp.Collection.load("user-manual.collection.mdp")

# Access collection metadata
print(collection.id)
print(collection.name)
print(collection.metadata["description"])

# Access documents in the collection
documents = collection.documents

# Get ordered documents
ordered_docs = collection.get_ordered_documents()
```

### MDPFile

The `MDPFile` class is a lower-level representation of an MDP file.

```python
from mdp.core import MDPFile, read_mdp, write_mdp

# Create an MDPFile object
mdp_file = MDPFile(
    metadata={"title": "My Document"},
    content="# My Document\n\nThis is the content.",
    path="my_document.mdp"
)

# Convert to string
mdp_str = mdp_file.to_string()

# Save to disk
mdp_file.save()

# Read from disk
mdp_file = read_mdp("my_document.mdp")

# Write to disk
write_mdp("new_document.mdp", {"title": "New Document"}, "# New Document\n\nContent.")
```

## Utility Functions

The `utils` module provides various utility functions.

```python
from mdp import utils

# Generate a UUID
uuid = utils.generate_uuid()

# Create metadata with default values
metadata = utils.create_metadata(
    title="My Document",
    author="Author Name"
)

# Validate metadata
utils.validate_metadata(metadata)

# Format dates properly
formatted_date = utils.format_date("2024-07-01")

# Check if a string is a valid UUID
is_valid = utils.is_valid_uuid("f47ac10b-58cc-4372-a567-0e02b2c3d479")

# Check if a string is a valid IPFS CID
is_valid = utils.is_valid_cid("QmX5fAjbxbx8pbDcDmyNJS5gBXZcB3zrR9upt9yKvkX4vR")

# Find related documents
related_docs = utils.find_related_documents(doc, directory="./documents")
```

## CLI Functions

The `cli` module provides the command-line interface functionality.

```python
from mdp import cli

# Run CLI commands programmatically
cli.create_document("My Document", "my_document.mdp")
cli.validate_document("my_document.mdp")
cli.list_collection("my-collection")
```

## IPFS Integration

The `integrations.ipfs` module provides IPFS integration (requires the ipfs optional dependency).

```python
from mdp.integrations import ipfs

# Configure IPFS integration
ipfs.configure(
    api_url="http://localhost:5001/api/v0",
    gateway_url="https://ipfs.io/ipfs/"
)

# Generate CID for a document
cid = ipfs.generate_cid(doc)

# Add document to IPFS
ipfs.add_document(doc)

# Get document from IPFS
retrieved_doc = ipfs.get_document("QmX5fAjbxbx8pbDcDmyNJS5gBXZcB3zrR9upt9yKvkX4vR")

# Get related documents from IPFS
related_docs = ipfs.get_related_documents(doc)
```

## Error Handling

```python
from mdp.exceptions import MDPError, ValidationError

try:
    doc = mdp.Document.load("nonexistent.mdp")
except MDPError as e:
    print(f"MDP error: {e}")

try:
    doc.validate()
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Extended Functionality via Datapack

More advanced functionality, including converters and metadata extraction, is available through the Datapack platform, which builds on the core MDP format:

- Format conversion (HTML, PDF, JSON, YAML, XML)
- Advanced metadata extraction
- Batch processing tools
- Content analysis capabilities

## Full API Documentation

For complete API documentation, including all classes, methods, and functions, visit the [full API documentation](https://greyhaven-ai.github.io/mdp/api/). 