"""
Tests for IPFS integration with MDP.

This module tests the functionality related to IPFS CIDs in the MDP module,
including CID validation, URI creation with IPFS CIDs, and relationships
using IPFS CIDs.
"""

import unittest
from mdp.metadata import (
    validate_metadata,
    create_metadata,
    is_valid_ipfs_cid,
    create_uri,
    parse_uri,
    create_relationship,
    add_relationship_to_metadata
)
from mdp.document import Document
from mdp.core import MDPFile


class TestIPFSIntegration(unittest.TestCase):
    """Tests for IPFS integration with MDP."""

    def test_ipfs_cid_validation(self):
        """Test validation of IPFS CIDs."""
        # Valid CIDv0 (base58btc encoded)
        valid_cid_v0 = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
        self.assertTrue(is_valid_ipfs_cid(valid_cid_v0))
        
        # Valid CIDv1 (base32 encoded)
        valid_cid_v1 = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"
        self.assertTrue(is_valid_ipfs_cid(valid_cid_v1))
        
        # Invalid CIDs
        invalid_cids = [
            "not-a-cid",
            "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjG",  # Too short
            "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzd",  # Too short
            "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx1",  # Too long
            "1234567890123456789012345678901234567890",  # Not a CID format
        ]
        
        for invalid_cid in invalid_cids:
            self.assertFalse(is_valid_ipfs_cid(invalid_cid))

    def test_metadata_with_ipfs_cid(self):
        """Test creating and validating metadata with IPFS CID."""
        # Create metadata with IPFS CID
        valid_cid = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
        metadata = create_metadata(
            title="IPFS Test Document",
            ipfs_cid=valid_cid
        )
        
        # Validate the metadata - should not raise an exception
        try:
            validate_metadata(metadata)
            is_valid = True
        except ValueError:
            is_valid = False
        self.assertTrue(is_valid)
        self.assertEqual(metadata["ipfs_cid"], valid_cid)
        
        # Test with invalid CID
        invalid_metadata = create_metadata(
            title="Invalid IPFS Document",
            ipfs_cid="not-a-valid-cid"
        )
        
        # Should raise ValueError for invalid CID
        with self.assertRaises(ValueError) as context:
            validate_metadata(invalid_metadata)
        self.assertIn("Invalid IPFS CID format", str(context.exception))

    def test_ipfs_uri_functions(self):
        """Test URI creation and parsing with IPFS CIDs."""
        # Create a URI with an IPFS CID
        valid_cid = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
        
        # Create an IPFS URI
        ipfs_uri = create_uri(scheme="ipfs", path=valid_cid)
        self.assertEqual(ipfs_uri, f"ipfs://{valid_cid}")
        
        # Parse the IPFS URI
        components = parse_uri(ipfs_uri)
        self.assertEqual(components["scheme"], "ipfs")
        self.assertEqual(components["path"], valid_cid)
        
        # Test with invalid URI
        with self.assertRaises(ValueError):
            parse_uri("ipfs://invalid-cid")

    def test_ipfs_relationships(self):
        """Test creating relationships with IPFS CIDs."""
        # Create a relationship with an IPFS CID
        valid_cid = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
        ipfs_uri = f"ipfs://{valid_cid}"
        
        # Create a relationship
        rel = create_relationship(
            id=ipfs_uri,
            rel_type="reference",
            title="IPFS Document",
            description="A document stored on IPFS"
        )
        
        self.assertEqual(rel["type"], "reference")
        self.assertEqual(rel["id"], ipfs_uri)
        self.assertEqual(rel["title"], "IPFS Document")
        
        # Add the relationship to metadata
        metadata = create_metadata(title="Document with IPFS Relationship")
        updated_metadata = add_relationship_to_metadata(metadata, rel)
        
        self.assertIn("relationships", updated_metadata)
        self.assertIn(rel, updated_metadata["relationships"])

    def test_document_with_ipfs_cid(self):
        """Test creating a Document with an IPFS CID."""
        valid_cid = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
        
        # Create a document with an IPFS CID
        doc = Document.create(
            title="IPFS Document",
            content="# IPFS Document\n\nThis document is stored on IPFS.",
            ipfs_cid=valid_cid
        )
        
        self.assertEqual(doc.title, "IPFS Document")
        self.assertEqual(doc.metadata["ipfs_cid"], valid_cid)
        
        # Create a relationship to another IPFS document
        other_cid = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"
        doc.add_relationship(
            id=f"ipfs://{other_cid}",
            relationship_type="reference",
            title="Referenced IPFS Document"
        )
        
        # Check that the relationship was added correctly
        self.assertEqual(len(doc.relationships), 1)
        self.assertEqual(doc.relationships[0]["id"], f"ipfs://{other_cid}")
        self.assertEqual(doc.relationships[0]["type"], "reference")


if __name__ == "__main__":
    unittest.main() 