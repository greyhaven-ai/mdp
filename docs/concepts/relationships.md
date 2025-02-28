---
title: "Document Relationships in MDP"
version: "1.0.0"
author: "Datapack Team"
created_at: "2024-02-28"
updated_at: "2024-02-28"
tags: ["relationships", "documentation", "metadata"]
relationships:
  - type: "related"
    path: "docs/concepts/core_concepts.md"
    title: "MDP Core Concepts"
  - type: "related"
    path: "docs/specification/mdp_specification.md"
    title: "MDP Specification"
---

# Document Relationships in MDP

One of the most powerful features of the Markdown Data Pack (MDP) format is its ability to explicitly model relationships between documents. This document explains how relationships work in MDP and provides practical examples that conform to the MDP metadata standard.

## Understanding Document Relationships

In the AI ecosystem, documents rarely exist in isolation. They form networks of interconnected information, where each document relates to others in various ways. MDP makes these relationships explicit through structured metadata.

### Why Relationships Matter

Explicit document relationships provide several benefits:

1. **Context Enhancement**: Relationships provide additional context about a document's role in a larger knowledge structure
2. **Navigation Paths**: LLMs and systems can follow relationship links to find related information
3. **Knowledge Graphs**: Document collections can be visualized and processed as knowledge graphs
4. **Semantic Understanding**: Relationship types add semantic meaning to document connections

## Relationship Model in MDP

MDP uses a structured approach to define relationships in the `relationships` field of the document metadata.

### Relationship Types

MDP supports four standard relationship types:

- **parent**: Document that contains or encompasses this document
- **child**: Document that is contained by or elaborates on this document
- **related**: Document with a non-hierarchical connection
- **reference**: External standard or resource

### Relationship Structure

Each relationship entry requires:

1. A `type` field specifying the relationship type
2. At least one identifier field (`id`, `uri`, `path`, or `cid`)

Optional fields include:
- `title`: The title of the related document
- `description`: A description of the relationship

## Example Relationships

Here are examples of properly formatted relationships that match the MDP metadata standard:

### Basic Relationship Examples

```yaml
relationships:
  - type: "parent"
    path: "project_overview.mdp"
    title: "Project Overview"
  
  - type: "child"
    path: "implementation_details.mdp"
    title: "Implementation Details"
    description: "Technical implementation specifics for this feature"
  
  - type: "related"
    path: "alternative_approach.mdp"
    title: "Alternative Approach"
  
  - type: "reference"
    path: "standards/coding_standards.mdp"
    title: "Coding Standards"
```

### Using UUIDs for Relationships

```yaml
relationships:
  - type: "parent"
    id: "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
    title: "Project Overview"
  
  - type: "child"
    id: "b2c3d4e5-f6a7-8901-bcde-23456789abcd"
    title: "Implementation Details"
```

### Using URIs for Relationships

```yaml
relationships:
  - type: "related"
    uri: "mdp://organization/project/documents/related-document"
    title: "Related Document"
  
  - type: "reference"
    uri: "mdp://standards/coding/python-style-guide"
    title: "Python Style Guide"
```

### Using IPFS CIDs for Relationships

```yaml
relationships:
  - type: "related"
    cid: "QmX5fLsdYf8VmJCLJ7FYYGWcTKm1zPFe1QNJgcN2sGDevk"
    title: "Related Document"
    
  - type: "reference"
    cid: "QmYbGT7GiHQci5BoKhBPTKUDoEtbS6AK4L57Lb9VuPKL98"
    title: "External Reference"
```

## Practical Implementation

### Creating Relationships in Python

Using the MDP Python library, you can create and add relationships to documents:

```python
from mdp import Document
from mdp.metadata import create_relationship

# Create a new document
doc = Document.create(
    title="Feature Specification",
    author="Jane Smith",
    content="# Feature Specification\n\nDetails of the feature..."
)

# Add a parent relationship
doc.add_relationship(
    target="project_overview.mdp",
    relationship_type="parent",
    title="Project Overview"
)

# Add a child relationship using a UUID
doc.add_relationship(
    target="b2c3d4e5-f6a7-8901-bcde-23456789abcd",
    relationship_type="child",
    title="Implementation Details",
    description="Technical implementation of the feature"
)

# Save the document
doc.save("feature_specification.mdp")
```

### Navigating Relationships

```python
from mdp import Document

# Load a document
doc = Document.from_file("feature_specification.mdp")

# Get all related documents
related_docs = doc.get_related_documents()

# Get only child documents
child_docs = doc.get_related_documents(relationship_type="child")

# Access a specific related document
parent_docs = doc.get_related_documents(relationship_type="parent")
if parent_docs:
    parent = parent_docs[0]
    print(f"Parent document: {parent.title}")
```

## Advanced Relationship Concepts

### Bidirectional Relationships

MDP relationships can be bidirectional. For example, if Document A has a "parent" relationship to Document B, then Document B should have a "child" relationship to Document A.

```yaml
# Document A
relationships:
  - type: "parent"
    path: "document_b.mdp"
    title: "Document B"

# Document B
relationships:
  - type: "child"
    path: "document_a.mdp"
    title: "Document A"
```

### Relationship Validation

The MDP library provides validation for relationships to ensure they are properly formed:

```python
from mdp.metadata import validate_relationship, validate_relationships

# Validate a single relationship
relationship = {
    "type": "parent",
    "path": "document.mdp",
    "title": "Document Title"
}
validate_relationship(relationship)  # Raises ValueError if invalid

# Validate multiple relationships
relationships = [
    {"type": "parent", "path": "document_a.mdp"},
    {"type": "child", "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab"}
]
validate_relationships(relationships)  # Raises ValueError if any are invalid
```

## Relationship Best Practices

1. **Be explicit**: Always specify the relationship type and include a title when possible.
2. **Be consistent**: Use the same identifier type (path, id, uri, cid) for similar documents.
3. **Maintain bidirectionality**: Ensure reciprocal relationships exist between documents.
4. **Prefer UUIDs**: When possible, use UUIDs rather than paths for more robust relationships.
5. **Add descriptions**: Include descriptive text for complex relationships.

## Real-World Example: Project Documentation

Here's a complete example of a project documentation structure with relationships:

```
project/
├── overview.mdp           # Project overview document
├── requirements.mdp       # Requirements document
├── design/
│   ├── architecture.mdp   # Architecture document
│   └── ui_design.mdp      # UI design document
└── implementation/
    ├── backend.mdp        # Backend implementation
    └── frontend.mdp       # Frontend implementation
```

```yaml
# overview.mdp metadata
title: "Project Overview"
version: "1.0.0"
author: "Project Team"
uuid: "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
relationships:
  - type: "child"
    path: "requirements.mdp"
    title: "Requirements Document"
  - type: "child"
    path: "design/architecture.mdp"
    title: "Architecture Design"
  - type: "child"
    path: "design/ui_design.mdp"
    title: "UI Design"
```

```yaml
# requirements.mdp metadata
title: "Requirements Document"
version: "1.0.0"
author: "Product Manager"
uuid: "b2c3d4e5-f6a7-8901-bcde-23456789abcd"
relationships:
  - type: "parent"
    path: "overview.mdp"
    title: "Project Overview"
  - type: "child"
    path: "design/architecture.mdp"
    title: "Architecture Design"
```

```yaml
# design/architecture.mdp metadata
title: "Architecture Design"
version: "1.0.0"
author: "System Architect"
uuid: "c3d4e5f6-a7b8-9012-cdef-3456789abcde"
relationships:
  - type: "parent"
    path: "../overview.mdp"
    title: "Project Overview"
  - type: "parent"
    path: "../requirements.mdp"
    title: "Requirements Document"
  - type: "related"
    path: "ui_design.mdp"
    title: "UI Design"
  - type: "child"
    path: "../implementation/backend.mdp"
    title: "Backend Implementation"
  - type: "child"
    path: "../implementation/frontend.mdp"
    title: "Frontend Implementation"
```

By implementing these relationship patterns, you create a network of connected documents that LLMs and systems can navigate to gather context and related information efficiently. 