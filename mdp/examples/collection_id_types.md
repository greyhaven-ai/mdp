# Collection ID Types in MDP

## Overview

The Markdown Data Pack (MDP) format supports collections of documents, allowing related documents to be grouped together. Each collection can be identified by a unique identifier, stored in the `collection_id` field. To enhance interoperability and provide stronger validation, MDP now supports typed collection identifiers through the `collection_id_type` field.

## Collection ID Types

The following collection ID types are supported:

1. **UUID** (`uuid`): A globally unique identifier that conforms to the UUID format.
2. **URI** (`uri`): A URI reference, which can be an MDP URI (`mdp://organization/project/path`) or IPFS URI (`ipfs://CID`).
3. **CID** (`cid`): An IPFS Content Identifier, which can be either CIDv0 or CIDv1 format.
4. **String** (`string`): A simple string identifier with no specific format requirements (default).

## Using Collection ID Types in Metadata

### Basic Example

```yaml
---
title: Example Document
collection: My Collection
collection_id: 550e8400-e29b-41d4-a716-446655440000
collection_id_type: uuid
---

Document content here...
```

### With Different ID Types

#### UUID Example

```yaml
---
title: Example Document
collection: My Collection
collection_id: 550e8400-e29b-41d4-a716-446655440000
collection_id_type: uuid
---
```

#### URI Example

```yaml
---
title: Example Document
collection: My Collection
collection_id: mdp://organization/project/collection
collection_id_type: uri
---
```

#### CID Example

```yaml
---
title: Example Document
collection: My Collection
collection_id: QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco
collection_id_type: cid
---
```

#### String Example (Default)

```yaml
---
title: Example Document
collection: My Collection
collection_id: my-custom-collection-id
collection_id_type: string  # This is the default if not specified
---
```

## Programmatic Creation

The `create_collection_metadata` function has been updated to support typed collection identifiers:

```python
from mdp.metadata import create_collection_metadata

# Create metadata with a UUID collection ID
metadata = create_collection_metadata(
    collection_name="My Collection",
    collection_id="550e8400-e29b-41d4-a716-446655440000",
    collection_id_type="uuid",
    title="Example Document"
)

# Create metadata with a CID collection ID
metadata = create_collection_metadata(
    collection_name="IPFS Collection",
    collection_id="QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco",
    collection_id_type="cid",
    title="Example Document"
)
```

## Validation

The metadata validation system has been enhanced to check that the `collection_id` matches the format specified by `collection_id_type`:

- For `uuid` type, the collection ID must be a valid UUID.
- For `uri` type, the collection ID must be a valid URI (either MDP or IPFS format).
- For `cid` type, the collection ID must be a valid IPFS CID (either CIDv0 or CIDv1).
- For `string` type, any string is accepted.

If no `collection_id_type` is specified but a `collection_id` is provided, it defaults to `string`.

## Benefits

Using typed collection identifiers provides several benefits:

1. **Type Safety**: Ensures that collection IDs match their intended format.
2. **Interoperability**: Makes it easier to reference collections across systems.
3. **Consistency**: Aligns collection identification with the document identification system.
4. **Clarity**: Clearly communicates the format and intended use of collection IDs.

## Example Code

Here's a complete example demonstrating how to create and validate documents with typed collection IDs:

```python
from mdp.metadata import create_collection_metadata, validate_metadata
import uuid

# Create a collection with a UUID identifier
collection_id = str(uuid.uuid4())
metadata = create_collection_metadata(
    collection_name="UUID Collection",
    collection_id=collection_id,
    collection_id_type="uuid",
    title="Example Document"
)

# Validate the metadata
validation_result = validate_metadata(metadata)
if validation_result["valid"]:
    print("Metadata is valid!")
else:
    print("Validation errors:", validation_result["errors"])
```

## Best Practices

1. **Use Consistent Types**: Within a collection, use the same `collection_id_type` for all documents.
2. **Choose Appropriate Types**: 
   - Use `uuid` for globally unique collections
   - Use `uri` for collections that need to be addressed via a URI
   - Use `cid` for collections stored on IPFS
   - Use `string` for simple, human-readable identifiers

3. **Validate Early**: Validate metadata when creating or updating documents to catch type mismatches early.
4. **Document Your Types**: In project documentation, clearly specify which collection ID types are used and why. 