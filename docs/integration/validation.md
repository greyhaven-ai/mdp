# MDP Validation Guide

This guide explains how to validate Markdown Data Pack (MDP) documents and ensure they conform to the specification.

## Understanding MDP Validation

Validation in MDP ensures that documents adhere to the expected structure and that metadata contains the correct fields with appropriate values. Proper validation:

1. Ensures consistency across documents
2. Prevents errors in applications that process MDP files
3. Maintains compatibility with tools in the MDP ecosystem
4. Improves search and filter capabilities

## Types of Validation

### Schema Validation

The MDP specification defines a JSON Schema that governs the structure and content of MDP metadata. This schema enforces:

- Required fields (like `title`)
- Field types (strings, arrays, objects, etc.)
- Format requirements (like UUID, date strings)
- Allowed values for enumerated fields
- Relationship structures

### Metadata Validation

The core MDP package provides built-in validation for metadata fields, ensuring:

- Field types match expectations (strings, arrays, etc.)
- Date fields follow the ISO 8601 format (YYYY-MM-DD)
- UUIDs are properly formatted
- URIs follow the proper structure
- IPFS CIDs are valid
- Collection IDs match their specified types
- Relationships contain all required fields

## Core Validation Functions

The MDP package provides several key validation functions in the `metadata` and `core` modules:

```python
from mdp.metadata import validate_metadata
from mdp.core import MDPFile

# Validate metadata dictionary
metadata = {
    "title": "Test Document",
    "created_at": "2024-07-10",
    "tags": ["test", "documentation"]
}

# This will raise ValidationError if validation fails
validate_metadata(metadata)

# MDPFile objects automatically validate metadata on creation
mdp_file = MDPFile(metadata=metadata, content="# Test Document")
```

## Validation in Document Operations

The `Document` class automatically performs validation when creating or loading documents:

```python
from mdp.document import Document
from mdp.exceptions import ValidationError

try:
    # Create a document (validates metadata)
    doc = Document.create(
        title="Test Document",
        content="# Test Document\n\nThis is a test.",
        created_at="2024-07-10"
    )
    
    # Load a document (validates metadata during loading)
    doc = Document.from_file("document.mdp")
    
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Using Custom Schemas

For projects with specific requirements, you can validate against a custom schema:

```python
from mdp.core import validate_metadata

# Validate against a custom schema
validate_metadata(metadata, schema_path="custom_schema.json")
```

To create a custom schema, start with the MDP standard schema as a base and modify it to include your custom requirements.

## Collection Validation

When working with collections, you might want to validate that all documents follow consistent rules:

```python
from mdp.document import Document
from mdp.utils import find_collection_members
from pathlib import Path

# Find all members of a collection
collection_docs = find_collection_members(
    directory=Path("./documents"),
    collection_name="User Manual",
    recursive=True
)

# Check that all have required fields
for mdp_file in collection_docs:
    # Check for required custom fields
    if "chapter" not in mdp_file.metadata:
        print(f"Missing 'chapter' field in {mdp_file.path}")
    
    # Check that positions are in sequence
    # Implementation depends on your specific needs
```

## Common Validation Errors

### Missing Required Fields

```
ValidationError: Missing required fields: title
```

**Solution**: Add the required fields to the metadata section.

### Invalid UUID Format

```
ValidationError: 'uuid' field is not a valid UUID
```

**Solution**: Use a proper UUID format (e.g., `f47ac10b-58cc-4372-a567-0e02b2c3d479`).

### Invalid Date Format

```
ValidationError: 'created_at' field is not a valid ISO date
```

**Solution**: Use ISO 8601 date format (YYYY-MM-DD) for dates:

```yaml
created_at: "2024-07-01"
```

### Invalid Relationship References

```
ValidationError: Relationship at index 0 is missing required field 'id'
```

**Solution**: Ensure all relationships contain the required fields according to their type:

```yaml
relationships:
  - type: related
    id: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    title: "Related Document"
```

## CLI Validation

The MDP CLI provides validation functionality through the dev command:

```bash
# Validate an MDP file
mdp dev --validate document.mdp
```

## Best Practices

1. **Validate Early and Often**: Validate documents during creation and before any processing
2. **Use Standard Fields**: Follow the MDP specification's standard fields when possible
3. **Document Custom Requirements**: When using custom validation, document your specific requirements
4. **Use Collection ID Types**: Specify the `collection_id_type` field when using collection IDs to ensure proper validation
5. **Custom Fields**: Prefix custom fields with `x-` to clearly identify them as extensions

## Extended Validation

For advanced validation features beyond the core specification, consider using the Datapack platform, which builds on MDP to provide:

- Content validation for Markdown
- Advanced relationship validation
- Schema inference and generation
- Bulk validation for large document collections
- Custom validation rule creation

## Conclusion

Validation is a critical component of working with MDP documents. By ensuring your documents adhere to the standard schema, you maintain the integrity and usability of your document base. The core MDP package provides the essential validation tools needed to work with the MDP format, while the Datapack platform offers extended validation capabilities for more advanced use cases. 