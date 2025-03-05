"""
Additional tests for the core MDP file implementation.

This module provides additional tests for functions in the core.py module
to increase test coverage, focusing on functions that were identified as 
having low coverage.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import pytest

from mdp.core import (
    MDPFile,
    read_mdp,
    write_mdp,
    create_document,
    update_document,
    delete_document,
    list_documents,
    batch_update_documents,
    add_relationship,
    create_collection,
    add_document_to_collection,
    remove_document_from_collection,
    get_collection_documents,
    find_relationships,
    find_documents_by_metadata
)


class TestAdditionalCoreFunctions(unittest.TestCase):
    """Additional tests for core functions with low coverage."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_metadata = {
            "title": "Test Document",
            "description": "A test document",
            "tags": ["test", "coverage"]
        }
        self.test_content = "# Test Content\n\nThis is test content."
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_document(self):
        """Test creating a document with the create_document function."""
        # Create a test document
        test_path = os.path.join(self.temp_dir, "test_create.mdp")
        doc = create_document(
            title="Test Creation",
            content="# Test Creation\n\nCreated for testing.",
            path=test_path,
            author="Test Author",
            tags=["test", "create"],
            custom_field="custom value"
        )
        
        # Verify document was created
        self.assertTrue(os.path.exists(test_path))
        
        # Verify metadata
        self.assertEqual(doc.metadata["title"], "Test Creation")
        self.assertEqual(doc.metadata["author"], "Test Author")
        self.assertEqual(doc.metadata["tags"], ["test", "create"])
        self.assertEqual(doc.metadata["custom_field"], "custom value")
        
        # Verify content
        self.assertEqual(doc.content, "# Test Creation\n\nCreated for testing.")
    
    def test_update_document(self):
        """Test updating a document with the update_document function."""
        # Create a test document first
        test_path = os.path.join(self.temp_dir, "test_update.mdp")
        doc = create_document(
            title="Original Title",
            content="Original content",
            path=test_path
        )
        
        # Update the document
        updated_doc = update_document(
            path=test_path,
            content="Updated content",
            title="Updated Title",
            tags=["updated"]
        )
        
        # Verify updates
        self.assertEqual(updated_doc.metadata["title"], "Updated Title")
        self.assertEqual(updated_doc.metadata["tags"], ["updated"])
        self.assertEqual(updated_doc.content, "Updated content")
        
        # Check the file on disk
        read_doc = read_mdp(test_path)
        self.assertEqual(read_doc.metadata["title"], "Updated Title")
        self.assertEqual(read_doc.metadata["tags"], ["updated"])
        self.assertEqual(read_doc.content, "Updated content")
    
    def test_delete_document(self):
        """Test deleting a document with the delete_document function."""
        # Create a test document first
        test_path = os.path.join(self.temp_dir, "test_delete.mdp")
        create_document(
            title="To be deleted",
            content="This document will be deleted",
            path=test_path
        )
        
        # Verify it exists
        self.assertTrue(os.path.exists(test_path))
        
        # Delete the document
        result = delete_document(test_path)
        
        # Verify deletion
        self.assertTrue(result)
        self.assertFalse(os.path.exists(test_path))
        
        # Test deleting a non-existent document
        non_existent_path = os.path.join(self.temp_dir, "non_existent.mdp")
        result = delete_document(non_existent_path)
        self.assertFalse(result)
    
    def test_list_documents(self):
        """Test listing documents with the list_documents function."""
        # Create multiple test documents
        for i in range(3):
            test_path = os.path.join(self.temp_dir, f"test_list_{i}.mdp")
            create_document(
                title=f"Test Document {i}",
                content=f"Test content {i}",
                path=test_path
            )
        
        # Create a subdirectory with documents
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        for i in range(2):
            test_path = os.path.join(subdir, f"test_subdir_{i}.mdp")
            create_document(
                title=f"Subdir Document {i}",
                content=f"Subdir content {i}",
                path=test_path
            )
        
        # Test listing with recursion
        docs = list_documents(self.temp_dir, recursive=True)
        self.assertEqual(len(docs), 5)  # 3 in main dir + 2 in subdir
        
        # Test listing without recursion
        docs = list_documents(self.temp_dir, recursive=False)
        self.assertEqual(len(docs), 3)  # Only those in the main dir
    
    def test_batch_update_documents(self):
        """Test batch updating documents with the batch_update_documents function."""
        # Create multiple test documents
        for i in range(3):
            test_path = os.path.join(self.temp_dir, f"test_batch_{i}.mdp")
            create_document(
                title=f"Original Title {i}",
                content=f"Original content {i}",
                path=test_path
            )
        
        # Define an update function
        def update_func(mdp_file):
            mdp_file.metadata["status"] = "updated"
            mdp_file.content = mdp_file.content + "\n\nUpdated by batch process."
            return mdp_file
        
        # Perform batch update
        result = batch_update_documents(self.temp_dir, update_func, recursive=True)
        
        # Verify results
        self.assertEqual(len(result), 3)
        
        # Check that all documents were updated
        for i in range(3):
            test_path = os.path.join(self.temp_dir, f"test_batch_{i}.mdp")
            doc = read_mdp(test_path)
            self.assertEqual(doc.metadata["status"], "updated")
            self.assertIn("Updated by batch process", doc.content)
    
    def test_add_relationship(self):
        """Test adding a relationship between documents."""
        # Create two test documents
        source_path = os.path.join(self.temp_dir, "source.mdp")
        target_path = os.path.join(self.temp_dir, "target.mdp")
        
        create_document(
            title="Source Document",
            content="Source content",
            path=source_path
        )
        
        create_document(
            title="Target Document",
            content="Target content",
            path=target_path
        )
        
        # Add a relationship
        updated_doc = add_relationship(
            doc_path=source_path,
            rel_type="references",
            target_path=target_path,
            title="Reference Link",
            notes="This is a test reference"
        )
        
        # Verify the relationship was added
        self.assertIn("relationships", updated_doc.metadata)
        self.assertEqual(len(updated_doc.metadata["relationships"]), 1)
        
        rel = updated_doc.metadata["relationships"][0]
        self.assertEqual(rel["type"], "references")
        self.assertEqual(rel["title"], "Reference Link")
        self.assertEqual(rel["notes"], "This is a test reference")
        
        # Check the relationship target
        target_doc = read_mdp(target_path)
        self.assertNotIn("relationships", target_doc.metadata)  # Target shouldn't change
    
    def test_find_relationships(self):
        """Test finding relationships between documents."""
        # Create documents with relationships
        source_path = os.path.join(self.temp_dir, "source_rel.mdp")
        target1_path = os.path.join(self.temp_dir, "target1_rel.mdp")
        target2_path = os.path.join(self.temp_dir, "target2_rel.mdp")
        
        create_document(
            title="Source Document",
            content="Source content",
            path=source_path
        )
        
        create_document(
            title="Target1 Document",
            content="Target1 content",
            path=target1_path
        )
        
        create_document(
            title="Target2 Document",
            content="Target2 content",
            path=target2_path
        )
        
        # Add relationships
        add_relationship(
            doc_path=source_path,
            rel_type="references",
            target_path=target1_path,
            title="Reference to Target1"
        )
        
        add_relationship(
            doc_path=source_path,
            rel_type="includes",
            target_path=target2_path,
            title="Includes Target2"
        )
        
        # Find all relationships
        rels = find_relationships(source_path)
        self.assertEqual(len(rels), 2)
        
        # Find relationships by type
        refs = find_relationships(source_path, rel_type="references")
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0][0], target1_path)
        
        includes = find_relationships(source_path, rel_type="includes")
        self.assertEqual(len(includes), 1)
        self.assertEqual(includes[0][0], target2_path)
    
    def test_create_collection(self):
        """Test creating a collection with the create_collection function."""
        # Create a collection
        collection_path = os.path.join(self.temp_dir, "test_collection.mdp")
        collection = create_collection(
            collection_id="test-collection",
            name="Test Collection",
            path=collection_path,
            description="A test collection",
            creator="Test Creator",
            tags=["test", "collection"]
        )
        
        # Verify collection was created
        self.assertTrue(os.path.exists(collection_path))
        
        # Verify metadata
        self.assertEqual(collection.metadata["id"], "test-collection")
        self.assertEqual(collection.metadata["name"], "Test Collection")
        self.assertEqual(collection.metadata["description"], "A test collection")
        self.assertEqual(collection.metadata["creator"], "Test Creator")
        self.assertEqual(collection.metadata["tags"], ["test", "collection"])
        
        # Verify collection has documents array
        self.assertIn("documents", collection.metadata)
        self.assertEqual(len(collection.metadata["documents"]), 0)
    
    def test_add_document_to_collection(self):
        """Test adding documents to a collection."""
        # Create a collection
        collection_path = os.path.join(self.temp_dir, "test_collection_add.mdp")
        collection = create_collection(
            collection_id="test-collection-add",
            name="Test Collection Add",
            path=collection_path
        )
        
        # Create three test documents
        doc_paths = []
        for i in range(3):
            path = os.path.join(self.temp_dir, f"coll_doc_{i}.mdp")
            create_document(
                title=f"Collection Document {i}",
                content=f"This is document {i} for a collection",
                path=path
            )
            doc_paths.append(path)
        
        # Add documents to collection
        # First document with default position (append)
        updated_collection = add_document_to_collection(collection_path, doc_paths[0])
        self.assertEqual(len(updated_collection.metadata["documents"]), 1)
        
        # Second document with specific position
        updated_collection = add_document_to_collection(collection_path, doc_paths[1], position=0)
        self.assertEqual(len(updated_collection.metadata["documents"]), 2)
        
        # Verify the order (doc1 should now be first, doc0 second)
        self.assertEqual(updated_collection.metadata["documents"][0], doc_paths[1])
        self.assertEqual(updated_collection.metadata["documents"][1], doc_paths[0])
        
        # Add third document at the end
        updated_collection = add_document_to_collection(collection_path, doc_paths[2])
        self.assertEqual(len(updated_collection.metadata["documents"]), 3)
        
        # Verify the complete order
        self.assertEqual(updated_collection.metadata["documents"][0], doc_paths[1])
        self.assertEqual(updated_collection.metadata["documents"][1], doc_paths[0])
        self.assertEqual(updated_collection.metadata["documents"][2], doc_paths[2])
    
    def test_remove_document_from_collection(self):
        """Test removing a document from a collection."""
        # Create a collection
        collection_path = os.path.join(self.temp_dir, "test_collection_remove.mdp")
        collection = create_collection(
            collection_id="test-collection-remove",
            name="Test Collection Remove",
            path=collection_path
        )
        
        # Create three test documents
        doc_paths = []
        for i in range(3):
            path = os.path.join(self.temp_dir, f"remove_doc_{i}.mdp")
            create_document(
                title=f"Remove Document {i}",
                content=f"This is document {i} for removal test",
                path=path
            )
            doc_paths.append(path)
            
            # Add each document to collection
            collection = add_document_to_collection(collection_path, path)
        
        # Verify all documents are in the collection
        self.assertEqual(len(collection.metadata["documents"]), 3)
        
        # Remove the middle document
        updated_collection = remove_document_from_collection(collection_path, doc_paths[1])
        
        # Verify document was removed
        self.assertEqual(len(updated_collection.metadata["documents"]), 2)
        self.assertEqual(updated_collection.metadata["documents"][0], doc_paths[0])
        self.assertEqual(updated_collection.metadata["documents"][1], doc_paths[2])
        
        # Remove a document that's not in the collection (should not change anything)
        non_existent_path = os.path.join(self.temp_dir, "non_existent.mdp")
        updated_collection = remove_document_from_collection(collection_path, non_existent_path)
        self.assertEqual(len(updated_collection.metadata["documents"]), 2)
    
    def test_get_collection_documents(self):
        """Test retrieving documents from a collection."""
        # Create a collection
        collection_path = os.path.join(self.temp_dir, "test_collection_get.mdp")
        collection = create_collection(
            collection_id="test-collection-get",
            name="Test Collection Get",
            path=collection_path
        )
        
        # Create three test documents
        doc_paths = []
        for i in range(3):
            path = os.path.join(self.temp_dir, f"get_doc_{i}.mdp")
            create_document(
                title=f"Get Document {i}",
                content=f"This is document {i} for get test",
                path=path,
                priority=i  # Add a distinguishing metadata field
            )
            doc_paths.append(path)
            
            # Add each document to collection
            collection = add_document_to_collection(collection_path, path)
        
        # Get documents from collection
        documents = get_collection_documents(collection_path)
        
        # Verify correct documents were retrieved
        self.assertEqual(len(documents), 3)
        
        # Check that the documents match what was added
        doc_titles = [doc.metadata["title"] for doc in documents]
        self.assertIn("Get Document 0", doc_titles)
        self.assertIn("Get Document 1", doc_titles)
        self.assertIn("Get Document 2", doc_titles)
        
        # Check that metadata is preserved
        priorities = [doc.metadata.get("priority") for doc in documents]
        self.assertIn(0, priorities)
        self.assertIn(1, priorities)
        self.assertIn(2, priorities)
        
    def test_find_documents_by_metadata(self):
        """Test finding documents by metadata."""
        # Create actual test documents with different metadata
        doc_paths = []
        for i in range(5):
            path = os.path.join(self.temp_dir, f"meta_doc_{i}.mdp")
            tags = ["common"]
            if i % 2 == 0:
                tags.append("even")
            else:
                tags.append("odd")
                
            doc = create_document(
                title=f"Document {i}",
                content=f"Content {i}",
                path=path,
                tags=tags,
                priority=i
            )
            doc_paths.append(path)
        
        # Verify the documents were created
        for path in doc_paths:
            self.assertTrue(os.path.exists(path))
        
        # Test finding by tag "even" - should return docs 0, 2, 4
        even_docs = find_documents_by_metadata(self.temp_dir, {"tags": ["even"]})
        self.assertEqual(len(even_docs), 3)
        
        # Test finding by tag "odd" - should return docs 1, 3
        odd_docs = find_documents_by_metadata(self.temp_dir, {"tags": ["odd"]})
        self.assertEqual(len(odd_docs), 2)
        
        # Test finding by priority
        priority_docs = find_documents_by_metadata(self.temp_dir, {"priority": 2})
        self.assertEqual(len(priority_docs), 1)
        self.assertEqual(priority_docs[0].metadata["title"], "Document 2") 