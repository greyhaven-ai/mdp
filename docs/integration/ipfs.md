# IPFS Integration with MDP

This document describes the integration of the InterPlanetary File System (IPFS) with the Markdown Data Pack (MDP) format.

## Overview

IPFS is a distributed system for storing and accessing files, websites, applications, and data. It provides a content-addressed storage model where files are identified by their content rather than their location. This makes IPFS a perfect complement to MDP's focus on metadata and relationships.

The integration of IPFS with MDP allows for:

1. Storing MDP documents on IPFS
2. Referencing IPFS-stored documents in MDP metadata
3. Creating relationships between documents using IPFS Content Identifiers (CIDs)
4. Validating IPFS CIDs in metadata and relationships

## IPFS Content Identifiers (CIDs)

IPFS uses Content Identifiers (CIDs) to uniquely identify content stored in the IPFS network. A CID is a self-describing content-addressed identifier that uses cryptographic hashing to ensure content integrity.

### CID Formats

IPFS supports two CID versions:

1. **CIDv0**: Base58btc encoded, starts with "Qm"
   - Example: `QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx`

2. **CIDv1**: Base32 encoded, starts with "b"
   - Example: `bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi`

Both formats are supported in MDP's IPFS integration.

## Metadata Integration

### The `ipfs_cid` Field

MDP metadata now includes an optional `ipfs_cid` field that can store the CID of the document when it's stored on IPFS.

Example metadata with an IPFS CID:

```yaml
---
title: IPFS Document Example
uuid: 550e8400-e29b-41d4-a716-446655440000
date: 2023-04-01
ipfs_cid: QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx
---
```

### Validation

The `ipfs_cid` field is validated to ensure it contains a valid IPFS CID. The validation checks:

1. The CID format (CIDv0 or CIDv1)
2. The encoding (Base58btc for CIDv0, Base32 for CIDv1)
3. The length of the CID

Invalid CIDs will cause validation errors when creating or updating MDP documents.

## URI Integration

### IPFS URI Format

MDP supports IPFS URIs in the format:

```
ipfs://<cid>
```

For example:
- `ipfs://QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx`
- `ipfs://bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi`

### Creating IPFS URIs

IPFS URIs can be created using the `create_uri` function:

```python
from mdp.metadata import create_uri

cid = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
ipfs_uri = create_uri(scheme="ipfs", path=cid)
# Result: "ipfs://QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
```

### Parsing IPFS URIs

IPFS URIs can be parsed using the `parse_uri` function:

```python
from mdp.metadata import parse_uri

components = parse_uri("ipfs://QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx")
# Result: {"scheme": "ipfs", "path": "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"}
```

## Relationship Integration

### Creating Relationships with IPFS CIDs

Relationships can be created using IPFS URIs as identifiers:

```python
from mdp.metadata import create_relationship

cid = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
ipfs_uri = f"ipfs://{cid}"

relationship = create_relationship(
    id=ipfs_uri,
    rel_type="reference",
    title="IPFS Document",
    description="A document stored on IPFS"
)
```

### Example Relationship in Metadata

```yaml
---
title: Document with IPFS Relationship
uuid: 550e8400-e29b-41d4-a716-446655440000
date: 2023-04-01
relationships:
  - id: ipfs://QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx
    type: reference
    title: IPFS Document
    description: A document stored on IPFS
---
```

## Document API Integration

### Creating Documents with IPFS CIDs

```python
from mdp import Document

doc = Document.create(
    title="IPFS Document Example",
    content="# IPFS Document Example\n\nThis document is stored on IPFS.",
    ipfs_cid="QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
)
```

### Adding IPFS Relationships to Documents

```python
doc.add_relationship(
    id="ipfs://QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx",
    rel_type="reference",
    title="Referenced IPFS Document"
)
```

## Working with IPFS

### Saving Documents to IPFS

While MDP doesn't include direct IPFS client functionality, you can use the `ipfshttpclient` library to interact with IPFS:

```python
import ipfshttpclient
from mdp import Document

# Create a document
doc = Document.create(
    title="IPFS Document",
    content="# IPFS Document\n\nThis document will be stored on IPFS."
)

# Convert to string
mdp_content = doc.to_string()

# Connect to IPFS daemon
with ipfshttpclient.connect() as client:
    # Add the document to IPFS
    result = client.add_str(mdp_content)
    cid = result["Hash"]
    
    # Update the document with the CID
    doc.metadata["ipfs_cid"] = cid
    
    print(f"Document stored on IPFS with CID: {cid}")
```

### Loading Documents from IPFS

```python
import ipfshttpclient
from mdp import Document
from mdp.core import MDPFile

# Connect to IPFS daemon
with ipfshttpclient.connect() as client:
    # Get the document from IPFS
    cid = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
    content = client.cat(cid).decode("utf-8")
    
    # Parse the MDP content
    mdp_file = MDPFile.from_string(content)
    
    # Create a Document from the MDPFile
    doc = Document.from_mdp_file(mdp_file)
    
    print(f"Loaded document: {doc.title}")
```

## Best Practices

1. **Always validate CIDs**: Use the `is_valid_ipfs_cid` function to validate CIDs before using them.
2. **Use URIs for relationships**: Always use the full `ipfs://` URI format when creating relationships.
3. **Store the CID in metadata**: When storing a document on IPFS, update its metadata with the CID.
4. **Consider pinning**: IPFS content may be garbage collected if not pinned. Consider pinning important documents.
5. **Handle network issues**: When working with IPFS, handle network connectivity issues gracefully.

## Limitations

1. MDP does not include a built-in IPFS client. You need to use a separate library like `ipfshttpclient`.
2. IPFS gateway access may be rate-limited. Consider using a dedicated gateway or running your own IPFS node.
3. IPFS content availability depends on the network. Content may not be immediately available after adding it.

## Future Enhancements

1. Built-in IPFS client functionality
2. Support for IPFS MFS (Mutable File System)
3. Integration with IPNS (InterPlanetary Name System)
4. Support for IPLD (InterPlanetary Linked Data)

## References

- [IPFS Documentation](https://docs.ipfs.io/)
- [IPFS CID Documentation](https://docs.ipfs.io/concepts/content-addressing/)
- [ipfshttpclient Documentation](https://ipfshttpclient.readthedocs.io/) 