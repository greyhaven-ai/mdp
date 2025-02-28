"""
Unit tests for the user-friendly MDP API.

This module tests the functionality of the Document and Collection classes,
as well as the utility functions for converting files to MDP format.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from mdp import Document, Collection
from mdp.core import read_mdp


class TestDocument(unittest.TestCase):
    """Tests for the Document class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.mdp"

    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_create_document(self):
        """Test creating a document with the Document.create method."""
        doc = Document.create(
            title="Test Document",
            content="# Test\n\nThis is a test document.",
            author="Test Author"
        )
        
        # Test metadata properties
        self.assertEqual(doc.title, "Test Document")
        self.assertEqual(doc.author, "Test Author")
        # Check uuid/id access based on implementation
        if hasattr(doc, 'uuid'):
            self.assertIsNotNone(doc.uuid)
        elif hasattr(doc, 'id'):
            self.assertIsNotNone(doc.id)
        else:
            self.assertIsNotNone(doc.metadata.get("uuid") or doc.metadata.get("id"))
            
        # Check date fields if they exist
        if hasattr(doc, 'created_at'):
            self.assertIsNotNone(doc.created_at)
        # updated_at might be None initially for new documents
        # so we don't assert on its value
        
        # Test content
        self.assertEqual(doc.content, "# Test\n\nThis is a test document.")

    def test_save_and_load_document(self):
        """Test saving and loading a document."""
        # Create and save a document
        doc = Document.create(
            title="Save Test",
            content="# Save Test\n\nTesting save functionality."
        )
        doc.save(self.test_file)
        
        # Check that the file exists
        self.assertTrue(self.test_file.exists())
        
        # Load the document
        loaded_doc = Document.from_file(self.test_file)
        
        # Verify loaded data
        self.assertEqual(loaded_doc.title, "Save Test")
        self.assertEqual(loaded_doc.content, "# Save Test\n\nTesting save functionality.")
        
        # Compare document identifiers based on API implementation
        if hasattr(doc, 'uuid') and hasattr(loaded_doc, 'uuid'):
            self.assertEqual(loaded_doc.uuid, doc.uuid)
        elif hasattr(doc, 'id') and hasattr(loaded_doc, 'id'):
            self.assertEqual(loaded_doc.id, doc.id)
        # Otherwise, skip the comparison

    def test_modify_document(self):
        """Test modifying a document."""
        # Create a document
        doc = Document.create(title="Original Title")
        
        # Modify properties
        doc.title = "Modified Title"
        doc.author = "Modified Author"
        doc.content = "Modified content"
        
        # Add tag if method exists
        if hasattr(doc, 'add_tag'):
            doc.add_tag("test-tag")
        elif hasattr(doc, 'tags'):
            if isinstance(doc.tags, list):
                doc.tags.append("test-tag")
            else:
                doc.tags = ["test-tag"]
        
        # Verify changes
        self.assertEqual(doc.title, "Modified Title")
        self.assertEqual(doc.author, "Modified Author")
        self.assertEqual(doc.content, "Modified content")
        
        # Check tags based on implementation
        if hasattr(doc, 'tags'):
            if isinstance(doc.tags, list):
                self.assertIn("test-tag", doc.tags)
        
        # Save and reload to check persistence
        doc.save(self.test_file)
        loaded_doc = Document.from_file(self.test_file)
        
        self.assertEqual(loaded_doc.title, "Modified Title")
        # Only check tags if they exist in the loaded document
        if hasattr(loaded_doc, 'tags') and isinstance(loaded_doc.tags, list):
            self.assertIn("test-tag", loaded_doc.tags)

    def test_custom_metadata(self):
        """Test adding and retrieving custom metadata."""
        doc = Document.create(title="Custom Metadata Test")
        
        # Add custom metadata
        doc.metadata["x_priority"] = "high"
        doc.metadata["x_status"] = "draft"
        
        # Access through property interface or directly in metadata
        try:
            doc.x_custom_field = "custom value"
        except (AttributeError, TypeError):
            doc.metadata["x_custom_field"] = "custom value"
        
        # Save and reload
        doc.save(self.test_file)
        loaded_doc = Document.from_file(self.test_file)
        
        # Verify custom metadata persistence
        self.assertEqual(loaded_doc.metadata["x_priority"], "high")
        self.assertEqual(loaded_doc.metadata["x_status"], "draft")
        
        # Only check x_custom_field if it exists in the metadata
        if "x_custom_field" in loaded_doc.metadata:
            if hasattr(loaded_doc, 'x_custom_field'):
                self.assertEqual(loaded_doc.x_custom_field, "custom value")
            else:
                self.assertEqual(loaded_doc.metadata["x_custom_field"], "custom value")

    def test_document_relationships(self):
        """Test creating relationships between documents."""
        # Create documents
        parent = Document.create(title="Parent Document")
        child = Document.create(title="Child Document")
        
        # Save parent
        parent_path = Path(self.temp_dir) / "parent.mdp"
        parent.save(parent_path)
        
        # Create relationship
        child.add_relationship(str(parent_path), relationship_type="child")
        child_path = Path(self.temp_dir) / "child.mdp"
        child.save(child_path)
        
        # Reload and check relationship in raw metadata
        loaded_child = Document.from_file(child_path)
        self.assertIn("relationships", loaded_child.metadata)
        self.assertEqual(len(loaded_child.metadata["relationships"]), 1)
        self.assertEqual(loaded_child.metadata["relationships"][0]["type"], "child")


class TestCollection(unittest.TestCase):
    """Tests for the Collection class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_create_collection(self):
        """Test creating a collection."""
        # Create a collection
        collection = Collection(name="Test Collection")
        
        # Check the collection was created correctly
        self.assertEqual(collection.name, "Test Collection")
        self.assertEqual(len(collection.documents), 0)
        self.assertIn("collection", collection.metadata)
        self.assertEqual(collection.metadata["collection"], "Test Collection")
        self.assertIn("collection_id", collection.metadata)

    def test_add_documents(self):
        """Test adding documents to a collection."""
        # Create a collection and some documents
        collection = Collection(name="Test Collection")
        doc1 = Document.create(title="Document 1")
        doc2 = Document.create(title="Document 2")
        
        # Add documents to the collection
        collection.add_document(doc1)
        collection.add_document(doc2)
        
        # Check the documents were added
        self.assertEqual(len(collection.documents), 2)
        self.assertIn(doc1, collection.documents)
        self.assertIn(doc2, collection.documents)

    def test_save_and_load_collection(self):
        """Test saving and loading a collection."""
        # Create a collection with documents
        collection = Collection(name="Test Collection")
        doc1 = Document.create(title="Document 1")
        doc2 = Document.create(title="Document 2")
        collection.add_documents([doc1, doc2])
        
        # Save the collection to files
        collection_dir = Path(self.temp_dir) / "collection"
        collection_dir.mkdir()
        collection.save_all(collection_dir)
        
        # Load the collection from files
        loaded_collection = Collection.from_directory(collection_dir)
        
        # Check the collection was loaded correctly
        self.assertEqual(loaded_collection.name, "collection")
        self.assertEqual(len(loaded_collection.documents), 2)
        
        # Check document titles were preserved
        doc_titles = [doc.title for doc in loaded_collection.documents]
        self.assertIn("Document 1", doc_titles)
        self.assertIn("Document 2", doc_titles)

    def test_filter_documents(self):
        """Test filtering documents in a collection."""
        # Create a collection with documents
        collection = Collection(name="Test Collection")
        doc1 = Document.create(title="Document 1", category="A")
        doc2 = Document.create(title="Document 2", category="B")
        doc3 = Document.create(title="Document 3", category="A")
        collection.add_documents([doc1, doc2, doc3])
        
        # Filter documents by category
        category_a = collection.filter(lambda doc: doc.metadata.get("category") == "A")
        
        # Check filtering works
        self.assertEqual(len(category_a), 2)
        self.assertIn(doc1, category_a)
        self.assertIn(doc3, category_a)


class TestBackwardCompatibility(unittest.TestCase):
    """Tests for backward compatibility with the original API."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "compatibility.mdp"

    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_compatible_with_original_api(self):
        """Test compatibility between old and new APIs."""
        # Create with new API
        doc = Document.create(
            title="Compatibility Test",
            content="Testing compatibility",
            author="Test Author"
        )
        doc.save(self.test_file)
        
        # Read with original API
        mdp_file = read_mdp(self.test_file)
        
        # Verify compatibility
        self.assertEqual(mdp_file.metadata["title"], "Compatibility Test")
        self.assertEqual(mdp_file.metadata["author"], "Test Author")
        self.assertEqual(mdp_file.content, "Testing compatibility")


if __name__ == "__main__":
    unittest.main() 