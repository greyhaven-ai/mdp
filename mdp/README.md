# MDP Module

The MDP (Markdown Data Pack) module provides functionality for working with .mdp files, which are text files with YAML frontmatter metadata at the top followed by markdown content.

## Overview

MDP files are designed to be:

- **Human-readable**: Content is in Markdown, which is easy to read and write
- **Machine-processable**: Metadata can be extracted and used by applications
- **Self-contained**: All information is stored in a single file
- **Extensible**: Can be extended with custom metadata fields

## Usage

### Working with Documents

```python
from mdp import Document

# Create a new document
doc = Document.create(
    title="Example Document",
    content="# Example Document\n\nThis is an example document.",
    author="MDP Team",
    tags=["example", "mdp", "documentation"]
)

# Save the document
doc.save("example.mdp")

# Load a document
doc = Document.from_file("example.mdp")

# Access and modify properties
print(doc.title)  # "Example Document"
doc.title = "Updated Title"

# Add a tag
doc.add_tag("documentation")

# Save changes
doc.save()
```

### Working with Collections

```python
from mdp import Collection, Document

# Create a collection of documents
collection = Collection("Example Collection")

# Add documents to the collection
doc1 = Document.create(title="First Document", content="Content of first document")
doc2 = Document.create(title="Second Document", content="Content of second document")

collection.add_document(doc1)
collection.add_document(doc2)

# Create a relationship between documents
doc1.add_relationship(doc2, relationship_type="related")

# Save the entire collection
collection.save_all("documents/")

# Load a collection from a directory
collection = Collection.from_directory("documents/")
```

### Converting Files to MDP

```python
from mdp import convert_file, convert_directory

# Convert a single file
doc = convert_file("document.txt", title="Converted Document")

# Convert all text and markdown files in a directory
docs = convert_directory(
    "source_documents/", 
    output_directory="converted_documents/",
    recursive=True
)
```

### Advanced Conversion

```python
from mdp import extract_text_from_pdf, import_website

# Extract text from a PDF
pdf_doc = extract_text_from_pdf("document.pdf")

# Import content from a website
web_doc = import_website("https://example.com")
```

## File Format

An MDP file consists of two main parts:

1. **YAML Frontmatter**: A section at the top of the file containing structured metadata in YAML format.
2. **Markdown Content**: The main content of the file in Markdown format.

Example:

```
---
title: Example MDP File
context: This document provides context for understanding the project structure and how to use it as a reference when analyzing the codebase.
author: MDP Team
tags:
  - example
  - mdp
  - documentation
---

# Example MDP File

This is an example MDP file that demonstrates the format.
```

## Standard Metadata Fields

The MDP module defines a set of standard metadata fields to ensure consistency across files. These fields are organized into categories:

### Core Fields

| Field | Description | Type | Required |
|-------|-------------|------|----------|
| `title` | The title of the document | String | **Yes** |
| `version` | The version of the document | String | No |
| `context` | Additional context about the document, its purpose, and how it should be used | String | No |

### Document Identification Fields

| Field | Description | Type | Required |
|-------|-------------|------|----------|
| `uuid` | Globally unique identifier for the document | String | No |
| `uri` | URI reference for the document in a registry | String | No |
| `local_path` | Local filesystem path relative to a defined root | String | No |

### Collection Fields

| Field | Description | Type | Required |
|-------|-------------|------|----------|
| `collection` | Collection this document belongs to | String | No |
| `collection_id` | Unique identifier for the collection | String | No |
| `position` | Position in an ordered collection | Integer | No |

### Authorship Fields

| Field | Description | Type | Required |
|-------|-------------|------|----------|
| `author` | The author of the document | String | No |
| `contributors` | List of contributors to the document | List | No |
| `created_at` | The creation date of the document (ISO 8601: YYYY-MM-DD) | String | No |
| `updated_at` | The last update date of the document (ISO 8601: YYYY-MM-DD) | String | No |

### Classification Fields

| Field | Description | Type | Required |
|-------|-------------|------|----------|
| `tags` | List of tags for categorizing the document | List | No |
| `status` | The status of the document (e.g., draft, published) | String | No |

### Source Fields

| Field | Description | Type | Required |
|-------|-------------|------|----------|
| `source_file` | The original file name if converted | String | No |
| `source_type` | The original file type if converted | String | No |
| `source_url` | The URL of the original content if applicable | String | No |

### Relationship Fields

| Field | Description | Type | Required |
|-------|-------------|------|----------|
| `relationships` | References to related documents | List | No |

## Relationship Types

MDP supports different types of relationships between documents:

- `parent`: Document that contains or encompasses this document
- `child`: Document that is contained by or elaborates on this document
- `related`: Document with a non-hierarchical connection
- `reference`: External standard or resource

You can easily work with relationships using the Document class:

```python
# Add a relationship
doc1.add_relationship(doc2, relationship_type="parent")

# Get related documents
children = doc1.get_related_documents(relationship_type="child")
```

## Custom Field Namespaces

To add custom metadata fields without conflicting with standard fields, use the custom field namespace prefix (`x_`):

```python
# Add custom fields directly to the metadata
doc = Document.create(title="Document with Custom Fields")
doc.metadata["x_priority"] = "high"
doc.metadata["x_department"] = "engineering"
```

For more information, see the [MDP File Format documentation](../../docs/mdp_format.md). 