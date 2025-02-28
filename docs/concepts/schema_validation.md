# MDP Schema Validation

This document describes the enhanced schema validation system for MDP (Markdown Data Pack) documents. The validation system ensures that document metadata adheres to the expected structure and constraints.

## Overview

The MDP schema validation system provides:

1. **JSON Schema Validation**: Validates metadata against a JSON schema
2. **Custom Validation Rules**: Applies additional validation logic beyond JSON schema
3. **Validation Profiles**: Supports different validation levels for different use cases
4. **Conditional Validation**: Validates fields based on the presence of other fields
5. **Relationship Validation**: Ensures relationships between documents are valid

## JSON Schema

The core of the validation system is a JSON schema that defines the structure and constraints for document metadata. The schema is located at `mdp/schema/mdp_schema_enhanced.json`.

### Key Schema Properties

The schema defines the following key properties:

- `title`: Document title (required)
- `version`: Semantic version string (MAJOR.MINOR.PATCH)
- `created_at`: ISO 8601 date string for creation time
- `updated_at`: ISO 8601 date string for last update time
- `author`: Author name or identifier
- `tags`: Array of tag strings
- `uuid`: Universally unique identifier
- `uri`: URI for the document
- `cid`: Content identifier (typically a hash)
- `context`: Contextual information about the document
- `relationships`: Array of relationships to other documents
- `version_history`: Array of version history entries
- `branch_name`: Name of the branch (for branched documents)
- `branched_from`: Information about the parent document (for branches)
- `merge_history`: Array of merge history entries

Custom fields can be added with the `x_` prefix (e.g., `x_custom_field`).

## Validation Profiles

The validation system supports different validation profiles to accommodate various use cases:

- **minimal**: Validates only the most essential fields (title)
- **standard**: Default validation level for typical documents
- **publication**: Stricter validation for documents intended for publication
- **collection**: Validation for documents that are part of a collection
- **archival**: Strict validation for documents intended for long-term archival

Each profile enforces different requirements:

```python
# Example of using validation profiles
from mdp.schema.validation import validate_metadata

# Validate with minimal profile
errors = validate_metadata(metadata, profile="minimal")

# Validate with publication profile
errors = validate_metadata(metadata, profile="publication")
```

## Custom Validation Rules

Beyond JSON schema validation, the system applies custom validation rules:

- **Semantic Version**: Ensures version strings follow the MAJOR.MINOR.PATCH format
- **Date Format**: Validates that dates are in ISO 8601 format
- **UUID Format**: Checks that UUIDs are properly formatted
- **Relationship Integrity**: Validates that relationships reference valid documents
- **Conditional Fields**: Ensures required fields are present based on conditions

Custom rules are applied after JSON schema validation:

```python
# Example of custom validation rules
from mdp.schema.validation import validate_metadata_with_rules

# Apply custom validation rules
errors = validate_metadata_with_rules(metadata, custom_rules={
    "require_author_for_publication": lambda m: "author" in m if m.get("status") == "published" else True
})
```

## Relationship Validation

The validation system includes special handling for document relationships:

- **Relationship Types**: Validates that relationship types are recognized
- **Target Existence**: Optionally checks that target documents exist
- **Bidirectional Relationships**: Ensures reciprocal relationships are valid

```python
# Example of relationship validation
from mdp.schema.validation import validate_relationships_advanced

# Validate relationships
errors = validate_relationships_advanced(
    metadata,
    document_exists_func=lambda uri: os.path.exists(uri),
    load_document_func=lambda uri: Document.from_file(uri)
)
```

## Programmatic Usage

### Basic Validation

```python
from mdp.schema.validation import validate_metadata

# Validate metadata against the default schema
errors = validate_metadata(metadata)

if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    print("Metadata is valid")
```

### Advanced Validation

```python
from mdp.schema.validation import (
    validate_metadata_with_schema,
    validate_metadata_with_rules,
    validate_relationships_advanced
)

# Step 1: Validate against JSON schema
schema_errors = validate_metadata_with_schema(metadata, schema_path="custom_schema.json")

# Step 2: Apply custom validation rules
rule_errors = validate_metadata_with_rules(metadata, custom_rules={
    "check_title_length": lambda m: len(m.get("title", "")) <= 100
})

# Step 3: Validate relationships
relationship_errors = validate_relationships_advanced(metadata)

# Combine all errors
all_errors = schema_errors + rule_errors + relationship_errors
```

### Using Validation Profiles

```python
from mdp.schema.validation import validate_metadata

# For draft documents
draft_errors = validate_metadata(metadata, profile="minimal")

# For documents being published
publication_errors = validate_metadata(metadata, profile="publication")
```

## CLI Usage

The validation system is integrated with the MDP CLI:

```bash
# Validate a document with the default profile
mdp dev validate path/to/document.mdp

# Validate with a specific profile
mdp dev validate path/to/document.mdp --profile publication

# Validate against a custom schema
mdp dev validate path/to/document.mdp --schema path/to/custom_schema.json
```

## Custom Schemas

You can create custom schemas for specific document types:

1. Create a JSON schema file based on the default schema
2. Add or modify properties as needed
3. Use the custom schema in validation:

```python
from mdp.schema.validation import validate_metadata_with_schema

errors = validate_metadata_with_schema(metadata, schema_path="path/to/custom_schema.json")
```

## Error Reporting

Validation errors are reported with detailed information:

- **Error Type**: The type of validation error (schema, rule, relationship)
- **Field Path**: The path to the field with the error
- **Message**: A human-readable error message
- **Context**: Additional context about the error

Example error format:

```python
{
    "type": "schema_error",
    "path": "metadata.version",
    "message": "Invalid semantic version format",
    "context": {
        "value": "1.0",
        "expected_pattern": "^\\d+\\.\\d+\\.\\d+$"
    }
}
```

## Integration with Document Class

The validation system is integrated with the Document class:

```python
from mdp.document import Document

# Create a document
doc = Document.create(title="Test Document")

# Validate the document
is_valid, errors = doc.validate(profile="standard")

if not is_valid:
    for error in errors:
        print(f"Error in {error['path']}: {error['message']}")
```

## Performance Considerations

The validation system includes performance optimizations:

- **Schema Caching**: Loaded schemas are cached to avoid repeated parsing
- **Selective Validation**: Only validates fields that are relevant to the profile
- **Early Termination**: Stops validation when critical errors are found

For large documents or batch processing, consider using the minimal profile for initial validation and the full profile for final validation. 