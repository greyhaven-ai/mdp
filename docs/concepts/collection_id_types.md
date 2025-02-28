---
title: "Typed Collection Identifiers in MDP"
version: "1.0.0"
author: "Datapack Team"
created_at: "2024-07-15"
status: "Draft"
---

# Typed Collection Identifiers

MDP provides a flexible system for identifying collections of documents. With the `collection_id_type` field, you can specify the format and validation rules for collection identifiers.

## Overview

When organizing documents into collections, it's often necessary to reference collections across different systems or storage mechanisms. The `collection_id_type` field allows you to explicitly declare what type of identifier you're using, enabling proper validation and interoperability.

## Supported Identifier Types

MDP supports the following collection identifier types:

| Type | Description | Example | Validation |
|------|-------------|---------|------------|
| `uuid` | Universally Unique Identifier (UUID v4) | `550e8400-e29b-41d4-a716-446655440000` | Must be a valid UUID format |
| `uri` | URI reference (MDP or IPFS format) | `mdp://organization/project/collection` | Must be a valid URI format |
| `cid` | IPFS Content Identifier | `QmX5fAjbxbx8pbDcDmyNJS5gBXZcB3zrR9upt9yKvkX4vR` | Must be a valid IPFS CID format |
| `string` | Simple string identifier (default) | `my-collection-123` | No specific format validation |

## Using Typed Collection IDs

To specify a collection ID type in your MDP document, include both the `collection_id` and `collection_id_type` fields in your metadata:

```yaml
---
title: "Document with Typed Collection ID"
collection: "Technical Documentation"
collection_id: "550e8400-e29b-41d4-a716-446655440000"
collection_id_type: "uuid"
---
```

If you don't specify a `collection_id_type`, the system defaults to treating the identifier as a simple string without specific format validation.

## Validation

When a `collection_id_type` is specified, the MDP validator ensures that the `collection_id` conforms to the expected format:

- For `uuid` types, the string must be a valid UUID format
- For `uri` types, the string must be a valid URI format (MDP or IPFS)
- For `cid` types, the string must be a valid IPFS Content Identifier
- For `string` types, no specific validation is performed

If validation fails, an error is returned indicating the specific validation issue.

## Examples

### UUID Collection ID

```yaml
---
title: "Chapter 1: Introduction"
collection: "User Manual"
collection_id: "550e8400-e29b-41d4-a716-446655440000"
collection_id_type: "uuid"
position: 1
---
```

### URI Collection ID

```yaml
---
title: "API Documentation"
collection: "Developer Resources"
collection_id: "mdp://organization/tech-docs/api-collection"
collection_id_type: "uri"
---
```

### IPFS CID Collection ID

```yaml
---
title: "Distributed Storage Guide"
collection: "IPFS Documentation"
collection_id: "QmY7Yh4UquoXHLPFo2XbhXkhBvFoPwmQUSa92pxnxjQuPU"
collection_id_type: "cid"
---
```

### Default String Collection ID

```yaml
---
title: "Configuration Guide"
collection: "System Documentation"
collection_id: "sys-config-2023"
# collection_id_type: "string" is implied if not specified
---
```

## Python API Usage

The MDP Python library provides built-in support for typed collection identifiers:

```python
import mdp

# Create metadata with a UUID-typed collection ID
metadata = mdp.create_collection_metadata(
    collection_name="Technical Documentation",
    collection_id="550e8400-e29b-41d4-a716-446655440000",
    collection_id_type="uuid"
)

# Create metadata with a CID-typed collection ID
metadata = mdp.create_collection_metadata(
    collection_name="IPFS Documentation",
    collection_id="QmY7Yh4UquoXHLPFo2XbhXkhBvFoPwmQUSa92pxnxjQuPU",
    collection_id_type="cid"
)

# Validate existing metadata with typed collection ID
validation_result = mdp.validate_metadata(metadata)
if not validation_result["valid"]:
    print(f"Validation errors: {validation_result['errors']}")
```

## Best Practices

1. **Be Consistent**: Choose a single identifier type for all documents in the same collection
2. **Specify the Type**: Always include the `collection_id_type` field when using a `collection_id`
3. **Use UUIDs for Local Collections**: UUIDs are ideal for collections managed within a single system
4. **Use URIs for Cross-System References**: URIs provide more context for collections referenced across systems
5. **Use CIDs for Distributed Collections**: IPFS CIDs are perfect for collections stored in distributed systems

## Compatibility

The `collection_id_type` field is optional for backward compatibility with existing MDP documents. If not specified, the collection ID is treated as a simple string. 