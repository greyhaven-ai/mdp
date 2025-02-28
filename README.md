# MDP (Markdown Data Package)

A global standard file specification for document management that combines the readability of Markdown with structured metadata capabilities.

## Overview

MDP (Markdown Data Package) is a format that combines Markdown content with YAML frontmatter for metadata, creating a powerful and flexible document representation format. It's designed to be:

- **Human-readable**: Clear and readable even without special tools
- **Machine-processable**: Structured metadata makes it easy for automated tools to understand documents
- **Format agnostic**: Works with any text or data format while maintaining consistent metadata
- **Extensible**: Flexible schema allows easy addition of new metadata fields
- **Version controlled**: Works seamlessly with git and other version control systems
- **Content-addressable**: Optional IPFS integration for content-addressed documents

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
import uuid

# Create a collection with a UUID identifier
collection_id = str(uuid.uuid4())
collection = Collection("Example Collection", collection_id=collection_id, collection_id_type="uuid")

# Add documents to the collection
doc1 = Document.create(title="First Document", content="# First Document")
doc2 = Document.create(title="Second Document", content="# Second Document")

collection.add_document(doc1)
collection.add_document(doc2)

# Save all documents in the collection
collection.save_all("documents/")
```

### MCP (Model Context Protocol) Integration

MDP includes support for the Model Context Protocol (MCP), making it easy to serve and access documents via MCP-compatible clients:

```python
from mdp.mcp.server import create_mcp_server
from mdp.mcp.client import MCPClient

# Server-side: Create and start an MCP server
server = create_mcp_server("My Document Server") 
server.run()

# Client-side: Connect to the server and retrieve documents
async with MCPClient("http://localhost:8000") as client:
    # Create a document
    doc = Document.create(title="Sample", content="# Sample")
    result = await client.create_document(doc)
    
    # Search documents
    results = await client.search_documents("sample")
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
doc1.add_relationship(doc2, relationship_type="references")

# Save the relationship
doc1.save()
```

### Collection ID Types

MDP supports typed collection identifiers, allowing you to specify the format of collection IDs:

```python
from mdp import Collection, Document

# Create a collection with a UUID identifier
collection = Collection(
    name="Example Collection",
    collection_id="550e8400-e29b-41d4-a716-446655440000",
    collection_id_type="uuid"
)

# Create a collection with an IPFS CID
ipfs_collection = Collection(
    name="IPFS Collection",
    collection_id="QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco",
    collection_id_type="cid"
)

# Create a document in a collection
doc = Document.create(
    title="Collection Document",
    content="# Collection Document",
    collection="Example Collection",
    collection_id="550e8400-e29b-41d4-a716-446655440000",
    collection_id_type="uuid"
)
```

Example MDP file with typed collection ID:

```markdown
---
title: Collection Document
collection: Example Collection
collection_id: 550e8400-e29b-41d4-a716-446655440000
collection_id_type: uuid
---

# Collection Document

This document belongs to a collection with a UUID identifier.
```

### IPFS Integration

MDP supports IPFS Content Identifiers (CIDs) for content-addressed documents:

```python
from mdp import Document
import ipfshttpclient

# Connect to IPFS
client = ipfshttpclient.connect()

# Create a document
doc = Document.create(
    title="IPFS Example",
    content="# IPFS Integration\n\nThis document is stored on IPFS.",
    author="MDP Team",
    tags=["ipfs", "content-addressing"]
)

# Save the document to IPFS
result = client.add_str(doc.to_string())
cid = result['Hash']

# Add the CID to the document metadata
doc.metadata['cid'] = cid
doc.save("ipfs_example.mdp")

# Create a relationship using IPFS CID
another_doc = Document.from_file("another_document.mdp")
another_doc.add_relationship(
    reference=cid,
    relationship_type="related",
    title="IPFS Example",
    is_ipfs_cid=True
)
another_doc.save()
```

Example MDP file with IPFS CID:

```markdown
---
title: IPFS Example
author: MDP Team
created_at: 2023-07-15
tags:
  - ipfs
  - content-addressing
cid: QmX5fAjbxbx8pbDcDmyNJS5gBXZcB3zrR9upt9yKvkX4vR
relationships:
  - type: related
    cid: QmY7Yh4UquoXHLPFo2XbhXkhBvFoPwmQUSa92pxnxjQuPU
    title: Related IPFS Document
---

# IPFS Integration

This document is stored on IPFS with content addressing.
```

### Format Conversion

MDP includes utilities for converting between different formats:

```python
from mdp import Document
from mdp.converter import convert_to_html, convert_to_pdf

# Convert MDP to other formats
doc = Document.from_file("document.mdp")
convert_to_html(doc, "document.html")
convert_to_pdf(doc, "document.pdf")

# Import from other formats
from mdp.converter import convert_from_markdown, convert_from_html
doc1 = convert_from_markdown("document.md")
doc2 = convert_from_html("document.html")
```

## Command-Line Interface

MDP includes a CLI for common operations:

```bash
# Convert MDP files to HTML
mdp convert document.mdp --format html --output document.html

# Show document information
mdp info document.mdp

# Create a collection from MDP files
mdp collection create documents/ collection.json --recursive
```

## Ecosystem

MDP is part of a broader ecosystem for document management:

- **MDP Format**: The core file format specification (this library)
- **Datapack**: A platform for document management that uses MDP as its standard document format

## License

This project is licensed under the MIT License - see the LICENSE file for details.
