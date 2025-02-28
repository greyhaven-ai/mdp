---
title: "MDP Quick Start Guide"
version: "1.0.0"
author: "Datapack Team"
created_at: "2024-02-28"
tags: ["quickstart", "guide", "tutorial"]
uuid: "f6a7b8c9-d0e1-2345-fg67-89abcdef0123"
relationships:
  - type: "related"
    path: "concepts/core_concepts.md"
    title: "MDP Core Concepts"
  - type: "related"
    path: "specification/mdp_specification.md"
    title: "MDP Specification"
---

# MDP Quick Start Guide

This guide will help you get started with the Markdown Data Pack (MDP) format and library, so you can quickly begin leveraging document context and relationships in your projects.

## What is MDP?

Markdown Data Pack (MDP) is a document format that combines human-readable markdown content with structured metadata and explicit document relationships. It helps solve the "context problem" in document management by keeping important information about a document together with its content.

## Installation

### Python Package

```bash
# Install the MDP library
pip install mdp

# Install with extra features
pip install "mdp[all]"  # Includes all optional dependencies

# For development
pip install -e ".[dev]"  # From source with development dependencies
```

### CLI Tool

```bash
# Install the CLI tool
pip install mdp-cli

# Verify installation
mdp --version
```

## Creating Your First MDP Document

Let's create a simple MDP document:

```python
from mdp import Document

# Create a new document with basic metadata
doc = Document.create(
    title="Getting Started with MDP",
    author="Your Name",
    content="""
# Getting Started with MDP

This is a sample MDP document. The content is written in markdown,
while metadata is stored in YAML frontmatter.

## Features

- Human-readable content
- Structured metadata
- Explicit relationships between documents
"""
)

# Add tags
doc.add_tag("documentation")
doc.add_tag("tutorial")

# Save the document
doc.save("getting_started.mdp")

# Print the document as a string
print(doc.to_string())
```

The generated file will look like this:

```
---
title: "Getting Started with MDP"
author: "Your Name"
uuid: "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
created_at: "2024-02-28"
tags: ["documentation", "tutorial"]
---

# Getting Started with MDP

This is a sample MDP document. The content is written in markdown,
while metadata is stored in YAML frontmatter.

## Features

- Human-readable content
- Structured metadata
- Explicit relationships between documents
```

## Reading MDP Documents

```python
from mdp import Document

# Read an MDP file
doc = Document.from_file("getting_started.mdp")

# Access metadata
print(f"Title: {doc.title}")
print(f"Author: {doc.author}")
print(f"Created: {doc.created_at}")
print(f"Tags: {', '.join(doc.tags)}")

# Access content
print("\nContent:")
print(doc.content)
```

## Working with Relationships

Relationships are a key feature of MDP. Let's create a document with relationships:

```python
from mdp import Document

# Create a parent document
parent_doc = Document.create(
    title="Project Overview",
    author="Project Manager",
    content="# Project Overview\n\nThis document provides an overview of the project."
)
parent_doc.save("project_overview.mdp")

# Create a child document with a relationship to the parent
child_doc = Document.create(
    title="Technical Specifications",
    author="Technical Lead",
    content="# Technical Specifications\n\nThis document contains technical specifications."
)

# Add a relationship to the parent document
child_doc.add_relationship(
    target="project_overview.mdp",
    relationship_type="parent",
    title="Project Overview"
)

# Add another related document
child_doc.add_relationship(
    target="implementation_guide.mdp",  # This document doesn't need to exist yet
    relationship_type="related",
    title="Implementation Guide",
    description="Guide for implementing the specifications"
)

# Save the document
child_doc.save("technical_specs.mdp")
```

The child document will contain relationship metadata:

```
---
title: "Technical Specifications"
author: "Technical Lead"
uuid: "b2c3d4e5-f6a7-8901-bcde-23456789abcd"
created_at: "2024-02-28"
relationships:
  - type: "parent"
    path: "project_overview.mdp"
    title: "Project Overview"
  - type: "related"
    path: "implementation_guide.mdp"
    title: "Implementation Guide"
    description: "Guide for implementing the specifications"
---

# Technical Specifications

This document contains technical specifications.
```

## Using the CLI

The MDP CLI provides tools for working with MDP files:

### Creating a Document

```bash
mdp create "Document Title" --author "Your Name" --output document.mdp
```

### Validating a Document

```bash
mdp validate document.mdp
```

### Converting to/from Other Formats

```bash
# Convert Markdown to MDP
mdp convert readme.md --output readme.mdp

# Convert MDP to HTML
mdp convert document.mdp --format html --output document.html
```

### Working with Collections

```bash
# Create a collection from a directory
mdp collection create ./docs --name "Documentation"

# Summarize a collection
mdp summarize ./docs --recursive
```

## Document Validation

MDP includes built-in validation to ensure your documents follow the specification:

```python
from mdp.validation import validate_document

# Validate a document
doc = Document.from_file("document.mdp")
validation_result = validate_document(doc)

if validation_result.is_valid:
    print("Document is valid!")
else:
    print("Document validation errors:")
    for error in validation_result.errors:
        print(f"- {error}")
```

## Working with Document Collections

MDP allows you to work with collections of related documents:

```python
from mdp import Collection

# Create a collection from a directory
collection = Collection.from_directory("./documents", name="Documentation")

# Access documents in the collection
for doc in collection:
    print(f"Document: {doc.title}")

# Find a document by title
spec_doc = collection.get_document_by_title("Technical Specifications")
if spec_doc:
    print(f"Found document: {spec_doc.title}")
    
# Get parent-child hierarchy
hierarchy = collection.get_hierarchy()
for parent, children in hierarchy.items():
    print(f"Parent: {parent}")
    for child in children:
        print(f"  - Child: {child}")
```

## Next Steps

Now that you're familiar with the basics of MDP, you can:

1. Explore the [Core Concepts](concepts/core_concepts.md) to understand the underlying principles
2. Read the [MDP Specification](specification/mdp_specification.md) for detailed format information
3. Learn about [Document Relationships](concepts/relationships.md) and how to use them effectively
4. Try the [Python API](integration/python_api.md) for more advanced usage

## Example: Complete MDP Document

Here's a complete example of an MDP document with all standard metadata fields and relationships:

```
---
title: "Complete MDP Example"
version: "1.0.0"
author: "Documentation Team"
contributors: ["Jane Smith", "John Doe"]
created_at: "2024-02-15"
updated_at: "2024-02-28"
tags: ["example", "documentation", "complete"]
status: "published"
uuid: "c3d4e5f6-a7b8-9012-cdef-3456789abcde"
uri: "mdp://organization/project/examples/complete"
context: "This document serves as a comprehensive example of an MDP file with all standard metadata fields."
collection: "MDP Examples"
collection_id: "d4e5f6a7-b8c9-0123-def4-56789abcde01"
collection_id_type: "uuid"
position: 1
relationships:
  - type: "parent"
    path: "examples_index.mdp"
    title: "Examples Index"
    
  - type: "child"
    path: "simple_example.mdp"
    title: "Simple MDP Example"
    description: "A simpler version of this example"
    
  - type: "related"
    uri: "mdp://organization/project/specification"
    title: "MDP Specification"
    
  - type: "reference"
    path: "standards/markdown_standard.mdp" 
    title: "Markdown Standard"
---

# Complete MDP Example

This document demonstrates a complete MDP file with all standard metadata fields and relationship types.

## Standard Metadata Fields

The YAML frontmatter above includes examples of all standard metadata fields defined in the MDP specification.

## Relationship Types

The document includes examples of all four relationship types:

1. Parent relationship: Points to a document that contains or encompasses this document
2. Child relationship: Points to a document that is contained by or elaborates on this document
3. Related relationship: Points to a document with a non-hierarchical connection
4. Reference relationship: Points to an external standard or resource

## Custom Fields

Custom fields can be added with the `x_` prefix:

```yaml
x_department: "Documentation"
x_review_date: "2024-03-15"
```
``` 