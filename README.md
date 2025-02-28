# MDP (Markdown Data Package)

A global standard file specification for document management that combines the readability of Markdown with structured metadata capabilities.

## Overview

MDP (Markdown Data Package) is a format that combines Markdown content with YAML frontmatter for metadata, creating a powerful and flexible document representation format. It's designed to be:

- **Human-readable**: Clear and readable even without special tools
- **Machine-processable**: Structured metadata makes it easy for automated tools to understand documents
- **Format agnostic**: Works with any text or data format while maintaining consistent metadata
- **Extensible**: Flexible schema allows easy addition of new metadata fields
- **Version controlled**: Works seamlessly with git and other version control systems
- **Content-addressable**: Supports content-addressed documents with unique identifiers

## Core Functionality

MDP provides a comprehensive framework for working with metadata-rich documents:

- **Document Management**: Create, read, update, and validate markdown documents with structured metadata
- **Collections**: Organize related documents with shared properties and relationships
- **Schema Validation**: Ensure metadata consistency with customizable schema validation
- **Conflict Resolution**: Intelligent merging and conflict resolution for collaborative document editing
- **LSP Support**: Language Server Protocol integration for enhanced editing capabilities
- **CLI Tools**: Command-line utilities for document processing and management
- **Model Context Protocol (MCP)**: Integration with AI assistants and models

## Core vs Extended Functionality

The MDP package provides the core specification and implementation with zero external dependencies beyond Python's standard library. For extended functionality like format conversions (HTML, PDF, etc.), metadata extraction, and AI-powered features, please see the [Datapack](https://github.com/datapack) platform, which builds on MDP.

## Basic Format

An MDP file consists of:

1. **YAML Frontmatter**: Structured metadata at the beginning of the file
2. **Markdown Content**: The document's content in Markdown format

```markdown
---
title: Example Document
author: MDP Team
version: 1.0.0
created_at: 2023-06-01
tags:
  - example
  - documentation
---

# Example Document

This is the content of the document written in Markdown.

## Section 1

This is a section with **formatting** and [links](https://example.com).
```

## Installation

```bash
pip install mdp
```

## Usage

### Creating Documents

```python
from mdp import Document

# Create a document with content and metadata
doc = Document.create(
    title="Example Document",
    content="# Example\n\nThis is an example document.",
    author="MDP Team",
    tags=["example", "documentation"]
)

# Save as MDP
doc.save("example.mdp")
```

### Reading Documents

```python
from mdp import Document

# Load from an MDP file
doc = Document.from_file("example.mdp")

# Access properties
print(doc.title)         # "Example Document"
print(doc.content)       # "# Example\n\nThis is an example document."
print(doc.metadata)      # Complete metadata dictionary
```

### Working with Collections

```python
from mdp import Collection, Document

# Create a collection
collection = Collection("Example Collection")

# Add documents to the collection
doc1 = Document.create(title="First Document", content="# First Document")
doc2 = Document.create(title="Second Document", content="# Second Document")

collection.add_document(doc1)
collection.add_document(doc2)

# Save all documents in the collection
collection.save_all("documents/")

# Create a collection from a directory
from pathlib import Path
dir_collection = Collection.from_directory(
    directory=Path("my_documents"),
    name="My Directory Collection",
    recursive=True
)
```

### Versioning and Conflict Resolution

MDP provides tools for managing document versions and resolving conflicts:

```python
from mdp import Document

# Load a document
doc = Document.from_file("document.mdp")

# Create a new version
doc.bump_version(version_type="minor")  # Increment the minor version number
doc.save()

# Create a version snapshot
version_path = doc.create_version(
    version="1.1.0", 
    description="Added new section"
)

# Get version history
versions = doc.get_versions()

# Compare with a previous version
diff = doc.compare_with_version("1.0.0")

# Rollback to a previous version
doc.rollback_to_version("1.0.0")

# Create a branch
branch_doc = doc.create_branch("feature-branch")

# Merge changes from a branch
doc.merge_from_branch(branch_doc)

# Check for conflicts with another document
other_doc = Document.from_file("other_version.mdp")
has_conflicts, conflict_summary = doc.check_for_conflicts(other_doc)

# Auto-merge documents
merged_doc = doc.auto_merge(other_doc, "merged.mdp")

# Create a conflict resolution file for manual editing
conflict_file = doc.create_conflict_resolution_file(other_doc, "conflicts.mdp")

# Resolve conflicts from an edited conflict file
resolved_doc = Document.resolve_from_conflict_file("conflicts.mdp", "resolved.mdp")
```

### Schema Validation

MDP provides schema validation for document metadata:

```python
from mdp import Document
from mdp.core import validate_metadata
import json
import os

# Load a schema 
schema_path = os.path.join("schema", "custom_schema.json")

# Validate document metadata against schema
doc = Document.from_file("document.mdp")
is_valid = validate_metadata(doc.metadata, schema_path)
```

### MCP (Model Context Protocol) Integration

MDP includes support for the Model Context Protocol (MCP), making it easy to integrate with AI models and assistants:

```python
# Import the MCP server module
from mdp.mcp.server import create_mcp_server

# Create and start an MCP server with document support
server = create_mcp_server("Document Server")
server.run()
```

## Command-Line Interface

MDP includes a CLI for common operations:

```bash
# Display information about an MDP document
mdp info document.mdp

# Create a new MDP document
mdp create document.mdp --title "My Document" --author "Author Name"

# Work with collections
mdp collection create --name "My Collection" --path collections/
mdp collection list collections/my_collection/

# Work with document versions
mdp version create document.mdp --message "Updated content"
mdp version list document.mdp
mdp version show document.mdp --version 1.0.0
mdp version compare document.mdp --from 1.0.0 --to 1.1.0
mdp version rollback document.mdp --to 1.0.0

# Check and resolve conflicts
mdp conflict check document1.mdp document2.mdp
mdp conflict merge document1.mdp document2.mdp --output merged.mdp
```

## Language Server Support

MDP provides Language Server Protocol (LSP) support for enhanced editing capabilities:

```bash
# Start the MDP language server
mdp lsp serve

# In your editor configuration, connect to the MDP language server
# for real-time validation, auto-completion, and other features
```

## Features

### Rich Metadata

MDP supports complex nested metadata structures:

```yaml
---
title: Complex Metadata Example
author:
  name: John Doe
  email: john@example.com
  organization: Example Corp
versions:
  - number: 1.0.0
    date: 2023-05-01
    changes: Initial release
  - number: 1.1.0
    date: 2023-06-01
    changes: Bug fixes and improvements
---
```

### Document Relationships

MDP allows you to establish relationships between documents:

```python
from mdp import Document

doc1 = Document.from_file("document1.mdp")
doc2 = Document.from_file("document2.mdp")

# Create a relationship
doc1.add_relationship(
    target=doc2,
    relationship_type="references",
    title="Referenced Document",
    description="This document references important concepts from the target"
)

# Save the relationship
doc1.save()

# Get related documents
related_docs = doc1.get_related_documents(relationship_type="references")
```

### Collection Management

MDP provides powerful tools for working with collections of documents:

```python
from mdp import Collection, Document
from pathlib import Path

# Create a collection
collection = Collection("Example Collection")

# Add documents to the collection
doc1 = Document.create(title="First Document", content="# First Document")
doc2 = Document.create(title="Second Document", content="# Second Document")
collection.add_document(doc1)
collection.add_document(doc2)

# Create a collection from a directory
dir_collection = Collection.from_directory(
    directory=Path("my_documents"),
    name="My Directory Collection",
    recursive=True
)

# Find documents in a collection
found_doc = collection.get_document_by_title("First Document")
by_uuid = collection.get_document_by_uuid("550e8400-e29b-41d4-a716-446655440000")

# Filter documents
tag_docs = collection.filter(lambda doc: "important" in doc.tags)

# Get the document hierarchy
hierarchy = collection.get_hierarchy()

# Save all documents in a collection
collection.save_all(Path("output_directory"))

# Export collection with metadata
collection.export(Path("exported_collection"))
```

Example MDP file with collection metadata:

```markdown
---
title: Collection Document
collection: Example Collection
collection_id: 550e8400-e29b-41d4-a716-446655440000
---

# Collection Document

This document belongs to a collection.
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
