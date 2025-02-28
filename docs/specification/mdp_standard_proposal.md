---
title: "MDP (Markdown Data Pack): A Global Standard Proposal"
version: "1.0.0"
author: "Datapack Team"
published_date: "2024-10-18"
status: "Proposal"
uuid: "ffac10b-58cc-4372-a567-0e02b2c3d480"
---

# MDP (Markdown Data Pack)

> A proposed open standard for documents that combines structured metadata with markdown content, enabling both human readability and machine processability through a single file format.

## Background

In today's AI ecosystem, documents exist in a fragmented landscape of formats, each with different strengths and limitations. Traditional document formats like PDF excel at presentation but lack structured data. Data formats like JSON and XML excel at machine processability but are not optimized for human authoring and reading. Markdown has emerged as a popular format for human-friendly content, but lacks standardized metadata capabilities.

This fragmentation creates significant challenges for modern knowledge systems that need both:

1. **Human-friendly documents** that are easy to author, read, edit, and version control
2. **Machine-processable data** that enables automation, relationships, and semantic understanding

MDP (Markdown Data Pack) addresses this gap by combining the best of both worlds: the human readability of Markdown with the structured data capabilities of YAML frontmatter, all in a standardized, open format.

The MDP specification has been influenced by other emerging standards and file primitives designed for the AI era, including Cursor's `.mdc` rule files (which use structured metadata annotations with markdown content) and Jeremy Howard's `llms.txt` proposal (which provides a standardized way to make website content more accessible to LLMs). These formats share a common goal of making content both human-readable and machine-processable, principles that are central to the MDP standard.

## Core Concept

The MDP format has a simple structure:

```
---
title: "Document Title"
author: "Author Name"
created_at: "2023-04-20"
tags: ["documentation", "standard"]
uuid: "550e8400-e29b-41d4-a716-446655440000"
---

# Document Title

This is the content of the document in markdown format.
```

This format enables:

- **Structured metadata** for machine processability
- **Rich markdown content** for human readability
- **Self-contained files** that keep metadata with content
- **Semantic relationships** between documents
- **Collection and hierarchy** organization
- **Version control compatibility** due to text-based format

## Why We Need a Standard

While custom combinations of YAML and Markdown exist across various systems, the lack of a standardized approach leads to:

1. **Interoperability issues** between different tools and platforms
2. **Inconsistent implementations** of metadata schemas
3. **Limited portability** of documents across systems
4. **Reinvention of basic capabilities** by different teams
5. **Absence of common tooling** for validation and processing

By establishing MDP as an open standard, we can:

- **Create a common foundation** for document management systems
- **Enable interoperability** between compliant tools and platforms
- **Reduce development overhead** through shared libraries and utilities
- **Establish best practices** for document metadata
- **Foster innovation** through a consistent baseline

## Specification Documents

For technical details and implementation guidance:

- [Complete Specification](./mdp_specification.md): The detailed MDP file format specification
- [JSON Schema](./mdp_schema.json): JSON Schema for validating MDP metadata
- [OpenAPI Specification](./mdp_openapi.yaml): API specification for working with MDP documents
- [Implementation Examples](./mdp_implementation_examples.md): Code examples in multiple languages

## Key Features

### 1. Required and Optional Metadata

MDP establishes a core metadata schema with a minimal set of required fields and a rich set of optional fields:

| Category | Example Fields |
|----------|---------------|
| Core | title, version, context |
| Identification | uuid, uri, local_path |
| Authorship | author, contributors, created_at, updated_at |
| Organization | collection, tags, status, position |
| Relationships | parent, child, related, reference links |

### 2. Relationships Between Documents

MDP supports explicit relationships between documents:

```yaml
relationships:
  - type: "parent"
    id: "550e8400-e29b-41d4-a716-446655440000"
    title: "Parent Document Title"
  - type: "related"
    path: "related-document.mdp"
```

### 3. Collection Support

Documents can be organized into collections:

```yaml
collection: "Tutorial Series"
collection_id: "tut-series-2024"
position: 3
```

### 4. Custom Metadata Fields

Extensibility through prefixed custom fields:

```yaml
x_department: "Engineering"
x_priority: "High"
x_review_date: "2023-06-15"
```

## Implementation Status

The standard includes reference implementations to encourage adoption:

- [Python Reference Implementation](https://github.com/greyhaven-ai/mdp): Full featured library
- JavaScript/Node.js library (in development)
- Go implementation (planned)
- Rust implementation (planned)

## Adoption Pathway

We propose the following path for MDP adoption:

1. **Standardization**: Finalize the core specification with community input
2. **Reference Implementations**: Provide high-quality libraries in major languages
3. **Tool Ecosystem**: Develop validators, converters, and editor integrations
4. **Documentation**: Create comprehensive guides and examples
5. **Community Building**: Foster a community of implementers and users

## Call to Action

We invite developers, content creators, and organizations to:

- **Review** the specification documents
- **Contribute** feedback and suggestions
- **Implement** MDP in your tools and platforms
- **Join** the community discussions

## Community Resources

- [GitHub Repository](https://github.com/greyhaven-ai/mdp): Source code and issue tracking
- [Discussion Forum](https://github.com/greyhaven-ai/mdp/discussions): Community discussions and support
- [Contributing Guide](../community/contributing.md): How to contribute to the project 