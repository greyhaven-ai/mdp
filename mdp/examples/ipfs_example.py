#!/usr/bin/env python3
"""
Example script demonstrating IPFS integration with MDP.

This script shows how to:
1. Create a document with an IPFS CID
2. Create relationships between documents using IPFS CIDs
3. Validate IPFS CIDs
4. Create and parse IPFS URIs

Note: This example doesn't actually interact with IPFS, it just demonstrates
how to use the MDP API with IPFS CIDs.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the Python path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mdp import Document
from mdp.metadata import is_valid_ipfs_cid, create_uri, parse_uri


def main():
    """Run the IPFS integration example."""
    print("MDP IPFS Integration Example")
    print("============================\n")

    # Example IPFS CIDs
    cid_v0 = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
    cid_v1 = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"

    # Validate IPFS CIDs
    print(f"Validating CIDv0: {cid_v0}")
    print(f"Is valid: {is_valid_ipfs_cid(cid_v0)}\n")

    print(f"Validating CIDv1: {cid_v1}")
    print(f"Is valid: {is_valid_ipfs_cid(cid_v1)}\n")

    # Create IPFS URIs
    ipfs_uri_v0 = create_uri(scheme="ipfs", path=cid_v0)
    print(f"IPFS URI for CIDv0: {ipfs_uri_v0}")
    
    ipfs_uri_v1 = create_uri(scheme="ipfs", path=cid_v1)
    print(f"IPFS URI for CIDv1: {ipfs_uri_v1}\n")

    # Parse IPFS URIs
    components_v0 = parse_uri(ipfs_uri_v0)
    print(f"Parsed URI components for CIDv0: {components_v0}")
    
    components_v1 = parse_uri(ipfs_uri_v1)
    print(f"Parsed URI components for CIDv1: {components_v1}\n")

    # Create a document with an IPFS CID
    print("Creating a document with an IPFS CID...")
    doc = Document.create(
        title="IPFS Document Example",
        content="# IPFS Document Example\n\nThis document is stored on IPFS.",
        ipfs_cid=cid_v0
    )
    
    print(f"Document created with title: {doc.title}")
    print(f"Document IPFS CID: {doc.metadata['ipfs_cid']}\n")

    # Add a relationship to another document on IPFS
    print("Adding a relationship to another document on IPFS...")
    doc.add_relationship(
        id=ipfs_uri_v1,
        rel_type="reference",
        title="Referenced IPFS Document",
        description="Another document stored on IPFS"
    )
    
    print(f"Relationship added: {doc.relationships[0]}\n")

    # Save the document to a temporary file
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "ipfs_document.mdp"
        doc.save(file_path)
        
        print(f"Document saved to: {file_path}")
        
        # Read the document back
        loaded_doc = Document.load(file_path)
        print(f"Document loaded from file with title: {loaded_doc.title}")
        print(f"Document IPFS CID: {loaded_doc.metadata['ipfs_cid']}")
        print(f"Document relationships: {loaded_doc.relationships}\n")

    print("Example completed successfully!")


if __name__ == "__main__":
    main() 