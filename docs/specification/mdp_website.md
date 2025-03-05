# MDP (Markdown Data Pack)

> A standard file format that combines structured metadata with markdown content, enabling both human readability and machine processability.

MDP addresses a critical gap in document management: the need for a format that is simultaneously human-friendly and machine-processable. By combining YAML frontmatter for structured metadata with markdown for content, MDP creates a versatile file format for modern document systems.

## Core Specification

- [Format Definition](./mdp_specification.md): The complete MDP file format specification
- [JSON Schema](./mdp_schema.json): JSON Schema for validating MDP metadata
- [OpenAPI Specification](./mdp_openapi.yaml): API specification for working with MDP documents
- [Standard Proposal](./mdp_standard_proposal.md): The proposed MDP standard for global adoption
- [Implementation Examples](./mdp_implementation_examples.md): Code examples in multiple languages

## Implementation

- [Reference Implementation](https://github.com/greyhaven-ai/mdp): Python package implementing the MDP specification
- [Installation Guide](../integration/installation.md): How to install and set up the MDP tools
- [Python API Documentation](../integration/python_api.md): Reference for the Python library

## Tutorials

- [Getting Started](../examples/getting_started.md): An introduction to creating and using MDP files
- [Document Relationships](../examples/relationships.md): How to create and manage document relationships
- [Collections](../examples/collections.md): Working with document collections
- [Typed Collection IDs](../docs/collection_id_types.md): Using typed identifiers for collections
- [Content Addressing](../examples/ipfs.md): Using IPFS for content addressing

## Examples

- [Basic MDP Document](../examples/basic.mdp): A simple MDP file
- [MDP with Relationships](../examples/relationships.mdp): Document with relationship metadata
- [MDP Collection](../examples/collection): A set of related MDP documents

## Format Overview

An MDP file consists of two parts:
```
---
title: "Document Title"
author: "Author Name" 
created_at: "2023-04-20"
tags: ["documentation", "specification"]
collection: "Example Collection"
collection_id: "550e8400-e29b-41d4-a716-446655440000"
collection_id_type: "uuid"
---

# Document Title

This is the content of the document in markdown format.
```

The frontmatter metadata (between the `---` delimiters) uses YAML syntax and contains structured data about the document. The content after the frontmatter is standard markdown text.

## Key Benefits

1. **Human-readable**: Both metadata and content are in formats easily read by humans
2. **Machine-processable**: Structured metadata enables programmatic processing
3. **Version-control friendly**: Text-based format works well with Git and other VCS
4. **Flexible**: Can represent various document types and relationships
5. **Self-contained**: Metadata travels with the content in a single file
6. **Type-safe**: Supports typed identifiers for documents, collections, and relationships

## Getting Started

### Quick Start Example

Create a simple MDP file:

```
---
title: "Hello MDP"
author: "New User"
created_at: "2024-10-18"
tags: ["example", "beginner"]
---

# Hello MDP

This is my first MDP document.
```

### Installation

Install our Python reference implementation with:

```bash
pip install mdp
```

### Simple Usage

```python
from mdp import read_mdp, write_mdp

# Read an MDP file
doc = read_mdp("document.mdp")

# Access metadata and content
title = doc.metadata["title"]
content = doc.content

# Create a new MDP file
metadata = {
    "title": "New Document",
    "author": "Your Name",
    "created_at": "2024-10-18"
}
content = "# New Document\n\nHello world!"
write_mdp("new_document.mdp", metadata, content)
```

## Community

- [GitHub Repository](https://github.com/greyhaven-ai/mdp): Source code and issue tracking
- [Discussion Forum](https://github.com/greyhaven-ai/mdp/discussions): Community discussions and support
- [Contributing Guide](../community/contributing.md): How to contribute to the project

## Support the Standard

- Use MDP in your projects
- Contribute to the reference implementations
- Suggest improvements to the specification
- Spread the word about the standard 