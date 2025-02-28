import unittest
import uuid
from mdp.metadata import (
    create_collection_metadata,
    validate_metadata,
    is_valid_ipfs_cid,
    is_valid_uuid,
    VALID_COLLECTION_ID_TYPES
)

class TestCollectionIdTypes(unittest.TestCase):
    """Test the collection_id_type functionality in the MDP metadata module."""

    def test_collection_id_types_validation(self):
        """Test that collection_id_type validation works correctly."""
        # Valid collection_id_types
        for id_type in VALID_COLLECTION_ID_TYPES:
            metadata = create_collection_metadata(
                collection_name="Test Collection",
                collection_id_type=id_type,
                title="Test Document"
            )
            validation = validate_metadata(metadata)
            self.assertTrue(validation["valid"], f"Valid collection_id_type '{id_type}' failed validation")

        # Invalid collection_id_type
        try:
            create_collection_metadata(
                collection_name="Test Collection",
                collection_id_type="invalid_type",
                title="Test Document"
            )
            self.fail("Should have raised ValueError for invalid collection_id_type")
        except ValueError as e:
            self.assertIn("Invalid collection_id_type", str(e))

    def test_collection_id_uuid_type(self):
        """Test that UUID collection_id validation works correctly."""
        # Valid UUID
        valid_uuid = str(uuid.uuid4())
        metadata = create_collection_metadata(
            collection_name="Test Collection",
            collection_id=valid_uuid,
            collection_id_type="uuid",
            title="Test Document"
        )
        validation = validate_metadata(metadata)
        self.assertTrue(validation["valid"], "Valid UUID collection_id failed validation")
        self.assertEqual(metadata["collection_id_type"], "uuid")

        # Invalid UUID
        invalid_uuid = "not-a-uuid"
        try:
            create_collection_metadata(
                collection_name="Test Collection",
                collection_id=invalid_uuid,
                collection_id_type="uuid",
                title="Test Document"
            )
            self.fail("Should have raised ValueError for invalid UUID")
        except ValueError as e:
            self.assertIn("Invalid UUID format", str(e))

    def test_collection_id_uri_type(self):
        """Test that URI collection_id validation works correctly."""
        # Valid URI
        valid_uri = "mdp://organization/project/document"
        metadata = create_collection_metadata(
            collection_name="Test Collection",
            collection_id=valid_uri,
            collection_id_type="uri",
            title="Test Document"
        )
        validation = validate_metadata(metadata)
        self.assertTrue(validation["valid"], "Valid URI collection_id failed validation")
        self.assertEqual(metadata["collection_id_type"], "uri")

        # Invalid URI
        invalid_uri = "invalid-uri"
        try:
            create_collection_metadata(
                collection_name="Test Collection",
                collection_id=invalid_uri,
                collection_id_type="uri",
                title="Test Document"
            )
            self.fail("Should have raised ValueError for invalid URI")
        except ValueError as e:
            self.assertIn("Invalid URI format", str(e))

    def test_collection_id_cid_type(self):
        """Test that CID collection_id validation works correctly."""
        # Valid CIDv0
        valid_cid_v0 = "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"
        metadata = create_collection_metadata(
            collection_name="Test Collection",
            collection_id=valid_cid_v0,
            collection_id_type="cid",
            title="Test Document"
        )
        validation = validate_metadata(metadata)
        self.assertTrue(validation["valid"], "Valid CIDv0 collection_id failed validation")
        self.assertEqual(metadata["collection_id_type"], "cid")

        # Valid CIDv1
        valid_cid_v1 = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"
        metadata = create_collection_metadata(
            collection_name="Test Collection",
            collection_id=valid_cid_v1,
            collection_id_type="cid",
            title="Test Document"
        )
        validation = validate_metadata(metadata)
        self.assertTrue(validation["valid"], "Valid CIDv1 collection_id failed validation")

        # Invalid CID
        invalid_cid = "not-a-cid"
        try:
            create_collection_metadata(
                collection_name="Test Collection",
                collection_id=invalid_cid,
                collection_id_type="cid",
                title="Test Document"
            )
            self.fail("Should have raised ValueError for invalid CID")
        except ValueError as e:
            self.assertIn("Invalid IPFS CID format", str(e))

    def test_collection_id_string_type(self):
        """Test that string collection_id validation works correctly."""
        # Any string is valid for string type
        string_id = "my-custom-collection-id"
        metadata = create_collection_metadata(
            collection_name="Test Collection",
            collection_id=string_id,
            collection_id_type="string",
            title="Test Document"
        )
        validation = validate_metadata(metadata)
        self.assertTrue(validation["valid"], "String collection_id failed validation")
        self.assertEqual(metadata["collection_id_type"], "string")

    def test_default_collection_id_type(self):
        """Test that the default collection_id_type is 'string'."""
        string_id = "my-custom-collection-id"
        metadata = create_collection_metadata(
            collection_name="Test Collection",
            collection_id=string_id,
            title="Test Document"
        )
        self.assertEqual(metadata["collection_id_type"], "string")
        validation = validate_metadata(metadata)
        self.assertTrue(validation["valid"], "Default collection_id_type failed validation")

    def test_collection_id_type_in_metadata_validation(self):
        """Test that validate_metadata correctly validates collection_id based on collection_id_type."""
        # Create metadata directly (not using create_collection_metadata)
        metadata = {
            "title": "Test Document",
            "collection": "Test Collection",
            "collection_id": "not-a-uuid",
            "collection_id_type": "uuid"
        }
        
        # This should fail validation
        validation = validate_metadata(metadata)
        self.assertFalse(validation["valid"])
        self.assertIn("collection_id", validation["errors"])
        
        # Fix the UUID
        metadata["collection_id"] = str(uuid.uuid4())
        validation = validate_metadata(metadata)
        self.assertTrue(validation["valid"])
        
        # Test with invalid collection_id_type
        metadata["collection_id_type"] = "invalid_type"
        validation = validate_metadata(metadata)
        self.assertFalse(validation["valid"])
        self.assertIn("collection_id_type", validation["errors"])


if __name__ == "__main__":
    unittest.main() 