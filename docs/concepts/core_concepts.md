---
title: "MDP Core Concepts"
version: "1.0.0"
author: "Datapack Team"
created_at: "2024-02-28"
updated_at: "2024-02-28"
tags: ["concepts", "documentation", "fundamentals"]
relationships:
  - type: "related"
    path: "docs/specification/mdp_specification.md"
    title: "MDP Specification"
  - type: "related"
    path: "docs/concepts/schema_validation.md"
    title: "Schema Validation"
---

# MDP Core Concepts

This document outlines the fundamental concepts of Markdown Data Pack (MDP), focusing on how it solves the critical problems facing document management in the AI ecosystem.

## The Central Problem: Context Accessibility

The primary issue in today's AI ecosystem is that **context is not easily accessible from documents**. This manifests in several ways:

1. **Lost Context**: When documents are processed by LLMs, crucial context about their purpose, origin, and relationships is often lost
2. **Relationship Blindness**: Documents are treated as isolated entities rather than connected nodes in a knowledge graph
3. **Inefficient Processing**: LLMs must repeatedly parse documents to extract implicit relationships and context
4. **Duplicative Work**: Systems need to reprocess the same documents multiple times to understand their structure

These issues lead to inefficient use of documents by LLMs and waste significant processing resources.

## MDP's Solution Architecture

MDP addresses these issues through a unified approach:

### 1. Unified Content and Metadata

MDP combines human-readable markdown content with structured YAML metadata in a single file:

```
---
title: "Document Title"
author: "Author Name"
version: "1.0.0"
# Other metadata fields
---

# Markdown Content
```

This unification means:
- Context stays with content
- No separation between human-readable and machine-processable parts
- Single source of truth for both humans and machines

### 2. Standard Metadata Schema

MDP defines a standard metadata schema with fields grouped into logical categories:

#### Core Fields
- `title`: The document title (required)
- `version`: Semantic version (e.g., "1.0.0")
- `context`: Additional context about the document's purpose and usage

#### Document Identification
- `uuid`: Globally unique identifier
- `uri`: URI reference in a registry
- `local_path`: Relative filesystem path
- `cid`: IPFS Content Identifier

#### Collection Fields
- `collection`: Collection this document belongs to
- `collection_id`: Collection identifier
- `collection_id_type`: Type of identifier used
- `position`: Position in an ordered collection

#### Authorship Fields
- `author`: Document author
- `contributors`: List of contributors
- `created_at`: Creation date (ISO 8601: YYYY-MM-DD)
- `updated_at`: Last update date (ISO 8601: YYYY-MM-DD)

#### Classification Fields
- `tags`: List of categorization tags
- `status`: Document status (e.g., "draft", "published")

#### Source Fields
- `source_file`: Original file name if converted
- `source_type`: Original file type if converted
- `source_url`: URL of original content if applicable

#### Relationship Fields
- `relationships`: References to related documents

### 3. Explicit Relationship Modeling

MDP's most powerful feature is its ability to explicitly model relationships between documents using the `relationships` field:

```yaml
relationships:
  - type: "parent"
    path: "overview.mdp"
    title: "Project Overview"
  - type: "child"
    id: "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
    title: "Implementation Details"
  - type: "related" 
    uri: "mdp://organization/project/related-doc"
    title: "Related Document"
  - type: "reference"
    path: "reference.mdp"
    title: "External Reference"
```

Each relationship has:
- A **type** (parent, child, related, reference)
- An **identifier** (path, id, uri, or cid)
- Optional metadata like title and description

### 4. Context Preservation

MDP ensures that essential context about a document is preserved by:

1. Keeping metadata and content together in one file
2. Using standardized fields for common metadata
3. Allowing custom fields with the `x_` prefix for domain-specific metadata
4. Enabling explicit representation of document relationships

This context preservation is critical for LLMs to efficiently process documents without needing to rebuild this context every time.

## Core Benefits for AI Systems

MDP provides several key benefits for AI systems:

1. **Immediate Context Access**: LLMs can immediately understand document context from standardized metadata
2. **Relationship Awareness**: Systems can easily navigate between related documents
3. **Reduced Processing Overhead**: No need to repeatedly parse documents to extract implicit relationships
4. **Consistent Structure**: Standard schema enables consistent processing across documents
5. **Evolution Support**: Version tracking and authorship information support document evolution

## Practical Implementation

The MDP format is designed to be:

1. **Simple to implement**: Based on widely-used markdown and YAML
2. **Easy to validate**: Standard schema enables validation
3. **Compatible**: Works with existing markdown and YAML tools
4. **Extensible**: Custom fields for specialized use cases
5. **Human and machine friendly**: Readable by both humans and machines

By combining these features, MDP creates a document ecosystem where context flows seamlessly between documents and is readily accessible to both humans and AI systems. 