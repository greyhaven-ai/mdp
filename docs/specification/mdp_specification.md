---
title: "MDP (Markdown Data Pack) File Format Specification"
version: "1.0.0"
author: "Datapack Team"
published_date: "2024-07-01"
status: "Draft"
---

# MDP (Markdown Data Pack) File Format

> A standard for combining structured metadata with markdown content, enabling both human readability and machine processability through a single file format.

## Background

Document management systems face a critical challenge: balancing human readability with machine processability. While formats like JSON and XML are excellent for machines, they're not optimized for human authoring. Meanwhile, plain Markdown excels at readability but lacks structured metadata capabilities.

MDP (Markdown Data Pack) solves this problem by combining the readability of Markdown with the structured data capabilities of YAML frontmatter, creating a format that's both human-friendly and machine-processable.

## Specification

### File Format

- **Extension**: Files MUST use the `.mdp` extension
- **Encoding**: Files MUST be encoded in UTF-8
- **Line Endings**: CRLF or LF (platform-independent)
- **Structure**: YAML Frontmatter + Markdown Content

The file consists of two parts:
1. **YAML Frontmatter**: Metadata enclosed between triple-dash separators (`---`)
2. **Markdown Content**: Standard markdown text following the frontmatter

```
---
title: "Document Title"
author: "Author Name"
created_at: "2023-04-20"
tags: ["documentation", "specification"]
---

# Document Title

This is the content of the document in markdown format.
```

### Core Metadata Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Document title |
| version | string | No | Document version |
| context | string | No | Additional context about document purpose |

### Identification Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | Recommended | Globally unique identifier (UUID v4) |
| uri | string | No | URI reference for the document |
| local_path | string | No | Local filesystem path relative to a root |
| cid | string | No | IPFS Content Identifier (CID) for content addressing |

### Authorship Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| author | string | No | Document author |
| contributors | array | No | List of document contributors |
| created_at | string | Recommended | Creation date (ISO 8601: YYYY-MM-DD) |
| updated_at | string | Recommended | Last update date (ISO 8601: YYYY-MM-DD) |

### Organization Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| collection | string | No | Collection this document belongs to |
| collection_id | string | No | Unique identifier for the collection |
| collection_id_type | string | No | Type of identifier used for collection_id (uuid, uri, cid, string) |
| position | integer | No | Position in an ordered collection |
| tags | array | No | List of tags for categorization |
| status | string | No | Document status (draft, published, etc.) |

The `collection_id_type` field specifies the format of the `collection_id`, with the following valid values:
- `uuid`: A globally unique identifier in UUID format
- `uri`: A URI reference (either MDP or IPFS format)
- `cid`: An IPFS Content Identifier
- `string`: A simple string identifier (default if not specified)

### Relationship Fields

The `relationships` field defines connections between documents using relationship objects:

```yaml
relationships:
  - type: "parent"
    id: "550e8400-e29b-41d4-a716-446655440000"
    title: "Parent Document Title"
  - type: "related"
    path: "related-document.mdp"
    description: "A related document"
  - type: "reference"
    uri: "mdp://organization/project/document"
  - type: "related"
    cid: "QmX5fAjbxbx8pbDcDmyNJS5gBXZcB3zrR9upt9yKvkX4vR"
    title: "IPFS-addressed Document"
```

Valid relationship types:
- `parent`: Document that contains or encompasses this document
- `child`: Document that is contained by or elaborates on this document
- `related`: Document with a non-hierarchical connection
- `reference`: External standard or resource

### Custom Fields

Custom metadata fields can be added with the `x_` prefix to avoid collisions with standard fields:

```yaml
x_department: "Engineering"
x_priority: "High"
x_review_date: "2023-06-15"
```

## URI Formats

MDP supports two URI formats:

1. **MDP URI Format**: `mdp://organization/project/document`
2. **IPFS URI Format**: `ipfs://CID` (where CID is a valid IPFS Content Identifier)

## Validation Requirements

### Required
- Title field must be present
- UUID should be valid if present
- Dates should follow ISO 8601 format
- Relationships must have a valid type and identifier
- IPFS CIDs should be valid if present
- If `collection_id_type` is specified, the `collection_id` must conform to that type

### Recommended
- Include created_at and updated_at dates
- Use UUID for document identification
- Add tags for improved searchability
- Include context information where applicable
- Specify `collection_id_type` when using `collection_id`

## Implementation Guidelines

When implementing MDP parsers and generators:

1. Use proper YAML parsing for frontmatter extraction
2. Validate all required metadata fields
3. Ensure proper type validation for metadata values
4. Use standard date formats (ISO 8601)
5. Validate relationships for proper structure
6. Validate IPFS CIDs when present
7. Validate collection IDs based on their specified type
8. Preserve markdown formatting during reads/writes

## Implementations

### Reference Implementation

The official reference implementation is the `mdp` Python package:
```bash
pip install mdp
```

The package provides:
- Parsers and generators for MDP files
- Validation tools
- Converters to/from other formats
- Collection management utilities
- CLI for working with MDP files

### Other Implementations

- JavaScript/Node.js library (in development)
- Go implementation (planned)
- Rust implementation (planned)

## Examples

### Basic MDP Document

```
---
title: "Getting Started with MDP"
author: "Documentation Team"
created_at: "2023-04-15"
updated_at: "2023-05-20"
tags: ["tutorial", "beginner"]
status: "published"
uuid: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
---

# Getting Started with MDP

This document explains how to create and use MDP files.

## Introduction

MDP (Markdown Data Pack) files combine metadata with markdown content...
```

### Document with Typed Collection ID

```
---
title: "Chapter 2: Advanced Features"
author: "Technical Writer"
created_at: "2023-04-18"
collection: "User Manual"
collection_id: "550e8400-e29b-41d4-a716-446655440000"
collection_id_type: "uuid"
position: 2
relationships:
  - type: "parent"
    id: "550e8400-e29b-41d4-a716-446655440000"
    title: "User Manual"
  - type: "related"
    path: "chapter3.mdp"
    title: "Chapter 3: Configuration"
---

# Chapter 2: Advanced Features

This chapter covers advanced features of the product.
```

### Document with IPFS Content Addressing and Collection

```
---
title: "IPFS Integration Guide"
author: "Distributed Systems Team"
created_at: "2023-06-10"
tags: ["ipfs", "content-addressing", "distributed"]
cid: "QmX5fAjbxbx8pbDcDmyNJS5gBXZcB3zrR9upt9yKvkX4vR"
collection: "IPFS Documentation"
collection_id: "QmY7Yh4UquoXHLPFo2XbhXkhBvFoPwmQUSa92pxnxjQuPU"
collection_id_type: "cid"
relationships:
  - type: "related"
    cid: "QmY7Yh4UquoXHLPFo2XbhXkhBvFoPwmQUSa92pxnxjQuPU"
    title: "IPFS Configuration Guide"
---

# IPFS Integration Guide

This guide explains how to use IPFS with MDP documents...
```

## Benefits

1. **Human-readable**: Both metadata and content are in text formats easily readable by humans
2. **Machine-processable**: Structured metadata enables programmatic processing
3. **Version-control friendly**: Text-based format works well with Git and other VCS
4. **Flexible**: Can represent various document types and relationships
5. **Self-contained**: Metadata travels with the content in a single file
6. **Extendable**: Custom metadata fields can be added without breaking the format
7. **Content-addressable**: Support for IPFS CIDs enables content-addressed documents

## Resources

- [MDP JSON Schema](./mdp_schema.json): JSON Schema for validating MDP metadata
- [MDP OpenAPI Specification](./mdp_openapi.yaml): API specification for working with MDP documents
- [MDP GitHub Repository](https://github.com/greyhaven-ai/mdp): Official repository for the MDP package 