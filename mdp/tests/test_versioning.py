"""
Tests for the MDP versioning system.

These tests validate the functionality of the semantic versioning system
for MDP documents, including version creation, comparison, and branching.
"""

import os
import datetime
import tempfile
import shutil
from pathlib import Path
import unittest

from mdp.document import Document
from mdp.versioning import Version, VersionManager, get_version_manager
from mdp.metadata import is_semantic_version, compare_semantic_versions, next_version


class TestSemanticVersion(unittest.TestCase):
    """Test the semantic versioning utilities."""
    
    def test_version_validation(self):
        """Test validation of semantic version strings."""
        # Valid versions
        self.assertTrue(is_semantic_version("0.1.0"))
        self.assertTrue(is_semantic_version("1.0.0"))
        self.assertTrue(is_semantic_version("2.3.4"))
        self.assertTrue(is_semantic_version("10.20.30"))
        
        # Invalid versions
        self.assertFalse(is_semantic_version("1.0"))
        self.assertFalse(is_semantic_version("1"))
        self.assertFalse(is_semantic_version("1.0.0-beta"))
        self.assertFalse(is_semantic_version("v1.0.0"))
        self.assertFalse(is_semantic_version("1.0.0.0"))
        self.assertFalse(is_semantic_version("latest"))
    
    def test_version_comparison(self):
        """Test comparison of semantic versions."""
        # Equal versions
        self.assertEqual(compare_semantic_versions("1.0.0", "1.0.0"), 0)
        
        # First version less than second
        self.assertEqual(compare_semantic_versions("1.0.0", "1.0.1"), -1)
        self.assertEqual(compare_semantic_versions("1.0.0", "1.1.0"), -1)
        self.assertEqual(compare_semantic_versions("1.0.0", "2.0.0"), -1)
        
        # First version greater than second
        self.assertEqual(compare_semantic_versions("1.0.1", "1.0.0"), 1)
        self.assertEqual(compare_semantic_versions("1.1.0", "1.0.0"), 1)
        self.assertEqual(compare_semantic_versions("2.0.0", "1.0.0"), 1)
        
        # Complex comparisons
        self.assertEqual(compare_semantic_versions("2.1.0", "2.0.9"), 1)
        self.assertEqual(compare_semantic_versions("2.0.10", "2.0.9"), 1)
        self.assertEqual(compare_semantic_versions("10.0.0", "2.0.0"), 1)
    
    def test_next_version(self):
        """Test calculating the next version."""
        # Major version bump
        self.assertEqual(next_version("1.2.3", "major"), "2.0.0")
        self.assertEqual(next_version("0.1.0", "major"), "1.0.0")
        
        # Minor version bump
        self.assertEqual(next_version("1.2.3", "minor"), "1.3.0")
        self.assertEqual(next_version("0.1.0", "minor"), "0.2.0")
        
        # Patch version bump
        self.assertEqual(next_version("1.2.3", "patch"), "1.2.4")
        self.assertEqual(next_version("0.1.0", "patch"), "0.1.1")
        
        # Invalid version type
        with self.assertRaises(ValueError):
            next_version("1.0.0", "invalid")


class TestVersionClass(unittest.TestCase):
    """Test the Version class for version parsing and comparison."""
    
    def test_version_parsing(self):
        """Test parsing of semantic versions."""
        # Valid versions
        v1 = Version("1.2.3")
        self.assertEqual(v1.major, 1)
        self.assertEqual(v1.minor, 2)
        self.assertEqual(v1.patch, 3)
        
        v2 = Version("0.0.1")
        self.assertEqual(v2.major, 0)
        self.assertEqual(v2.minor, 0)
        self.assertEqual(v2.patch, 1)
        
        # Invalid versions
        with self.assertRaises(ValueError):
            Version("invalid")
        
        with self.assertRaises(ValueError):
            Version("1.0")
    
    def test_version_comparison_operators(self):
        """Test version comparison operators."""
        v1 = Version("1.0.0")
        v2 = Version("1.0.0")
        v3 = Version("1.1.0")
        v4 = Version("2.0.0")
        
        # Equality
        self.assertEqual(v1, v2)
        self.assertNotEqual(v1, v3)
        
        # Less than
        self.assertLess(v1, v3)
        self.assertLess(v3, v4)
        
        # Greater than
        self.assertGreater(v3, v1)
        self.assertGreater(v4, v3)
        
        # Less than or equal
        self.assertLessEqual(v1, v2)
        self.assertLessEqual(v1, v3)
        
        # Greater than or equal
        self.assertGreaterEqual(v2, v1)
        self.assertGreaterEqual(v3, v1)
    
    def test_version_next_methods(self):
        """Test methods for generating next versions."""
        v = Version("1.2.3")
        
        # Next major version
        next_major = v.next_major()
        self.assertEqual(str(next_major), "2.0.0")
        
        # Next minor version
        next_minor = v.next_minor()
        self.assertEqual(str(next_minor), "1.3.0")
        
        # Next patch version
        next_patch = v.next_patch()
        self.assertEqual(str(next_patch), "1.2.4")


class TestVersionManager(unittest.TestCase):
    """Test the VersionManager class for document versioning."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.versions_dir = os.path.join(self.test_dir, ".versions")
        
        # Create a test document
        self.doc_path = os.path.join(self.test_dir, "test_doc.mdp")
        self.doc = Document.create(
            title="Test Document",
            author="Test Author",
            content="# Test Document\n\nThis is a test document.",
            version="1.0.0"
        )
        self.doc.save(self.doc_path)
        
        # Create a version manager
        self.vm = VersionManager(self.versions_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_create_version(self):
        """Test creating a document version."""
        # Create a version
        version_path = self.vm.create_version(
            document_path=self.doc_path,
            version="1.1.0",
            author="Version Author",
            description="Test version"
        )
        
        # Check version file was created
        self.assertTrue(os.path.exists(version_path))
        
        # Load the version file
        version_doc = Document.from_file(version_path)
        
        # Check metadata was updated
        self.assertEqual(version_doc.version, "1.1.0")
        self.assertEqual(version_doc.author, "Version Author")
        
        # Check version_history was updated
        self.assertTrue("version_history" in version_doc.metadata)
        self.assertEqual(len(version_doc.version_history), 1)
        self.assertEqual(version_doc.version_history[0]["version"], "1.1.0")
        self.assertEqual(version_doc.version_history[0]["author"], "Version Author")
        self.assertEqual(version_doc.version_history[0]["description"], "Test version")
        
        # Check original document was updated
        updated_doc = Document.from_file(self.doc_path)
        self.assertEqual(updated_doc.version, "1.1.0")
        self.assertEqual(updated_doc.metadata.get("latest_version"), "1.1.0")
    
    def test_list_versions(self):
        """Test listing document versions."""
        # Create several versions
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.1.0",
            description="First update"
        )
        
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.2.0",
            description="Second update"
        )
        
        self.vm.create_version(
            document_path=self.doc_path,
            version="2.0.0",
            description="Major update"
        )
        
        # List versions
        versions = self.vm.list_versions(self.doc_path)
        
        # Check versions are returned in correct order (newest first)
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0]["version"], "2.0.0")
        self.assertEqual(versions[1]["version"], "1.2.0")
        self.assertEqual(versions[2]["version"], "1.1.0")
    
    def test_get_version(self):
        """Test retrieving a specific version."""
        # Create several versions
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.1.0"
        )
        
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.2.0",
            content="# Modified Document\n\nThis document has been modified."
        )
        
        # Get a specific version
        version_1_1 = self.vm.get_version(self.doc_path, "1.1.0")
        
        # Check version metadata
        self.assertEqual(version_1_1.metadata.get("version"), "1.1.0")
        
        # Check for non-existent version
        with self.assertRaises(FileNotFoundError):
            self.vm.get_version(self.doc_path, "0.9.0")
    
    def test_compare_versions(self):
        """Test comparing versions."""
        # Create a new version with different content and metadata
        original_doc = Document.from_file(self.doc_path)
        
        # Create initial version
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.0.0",
            description="Initial version"
        )
        
        # Modify the document
        modified_doc = Document.from_file(self.doc_path)
        modified_doc.content = "# Modified Document\n\nThis document has been modified."
        modified_doc.metadata["status"] = "published"
        modified_doc.save(self.doc_path)
        
        # Create version with modifications
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.1.0"
        )
        
        # Compare versions
        diff = self.vm.compare_versions(self.doc_path, "1.0.0", "1.1.0")
        
        # Check metadata differences
        self.assertIn("status", diff["metadata_diff"]["added"])
        self.assertEqual(diff["metadata_diff"]["added"]["status"], "published")
        
        # Check content differences
        content_changes = [d for d in diff["content_diff"] if d["op"] != "unchanged"]
        self.assertGreater(len(content_changes), 0)
    
    def test_rollback(self):
        """Test rolling back to a previous version."""
        # Create a modified version
        original_content = "# Original Document\n\nThis is the original content."
        modified_content = "# Modified Document\n\nThis is modified content."
        
        # Save original content
        original_doc = Document.from_file(self.doc_path)
        original_doc.content = original_content
        original_doc.save()
        
        # Create first version
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.1.0",
            description="Original content version"
        )
        
        # Modify the document
        modified_doc = Document.from_file(self.doc_path)
        modified_doc.content = modified_content
        modified_doc.tags = ["modified"]
        modified_doc.save()
        
        # Create second version
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.2.0",
            description="Modified content version"
        )
        
        # Rollback to first version
        self.vm.rollback_to_version(self.doc_path, "1.1.0")
        
        # Check document was rolled back
        rolled_back_doc = Document.from_file(self.doc_path)
        self.assertEqual(rolled_back_doc.content.strip(), original_content.strip())
        self.assertNotIn("tags", rolled_back_doc.metadata)
        
        # Check version was incremented
        self.assertNotEqual(rolled_back_doc.version, "1.1.0")
        self.assertTrue(rolled_back_doc.version > "1.2.0")  # Should be 1.2.1 or similar
    
    def test_branching(self):
        """Test creating branches."""
        # Create a version to branch from
        self.vm.create_version(
            document_path=self.doc_path,
            version="1.1.0",
            description="Version to branch from"
        )
        
        # Create a branch
        branch_path = self.vm.create_branch(
            document_path=self.doc_path,
            branch_name="feature-branch",
            base_version="1.1.0"
        )
        
        # Check branch was created
        self.assertTrue(os.path.exists(branch_path))
        
        # Load the branch
        branch_doc = Document.from_file(branch_path)
        
        # Check branch metadata
        self.assertEqual(branch_doc.metadata.get("branch_name"), "feature-branch")
        self.assertEqual(branch_doc.metadata.get("branched_from")["version"], "1.1.0")
        
        # Verify branch has different UUID
        self.assertNotEqual(branch_doc.metadata.get("uuid"), self.doc.metadata.get("uuid"))
        
        # Verify relationship to original document
        self.assertTrue("relationships" in branch_doc.metadata)
        self.assertEqual(branch_doc.metadata.get("relationships")[0]["type"], "parent")
    
    def test_branch_merging(self):
        """Test merging branches."""
        # Create a branch
        branch_path = self.vm.create_branch(
            document_path=self.doc_path,
            branch_name="feature-branch"
        )
        
        # Modify the branch
        branch_doc = Document.from_file(branch_path)
        branch_doc.content = "# Branched Document\n\nThis is a modified branch."
        branch_doc.metadata["status"] = "in_progress"
        branch_doc.version = "0.2.0"  # Branch starts with own version series
        branch_doc.save()
        
        # Merge branch back to original
        self.vm.merge_branch(branch_path, self.doc_path)
        
        # Check original was updated
        merged_doc = Document.from_file(self.doc_path)
        
        # Content should be from branch
        self.assertEqual(merged_doc.content.strip(), branch_doc.content.strip())
        
        # Metadata from branch should be in original
        self.assertEqual(merged_doc.metadata.get("status"), "in_progress")
        
        # Version should be incremented in minor version
        self.assertTrue(merged_doc.version > self.doc.version)
        
        # Merge history should be recorded
        self.assertTrue("merge_history" in merged_doc.metadata)
        self.assertEqual(merged_doc.metadata.get("merge_history")[0]["branch"], "feature-branch")
        self.assertEqual(merged_doc.metadata.get("merge_history")[0]["from_version"], "0.2.0")


class TestDocumentVersioning(unittest.TestCase):
    """Test document versioning through the Document class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test document
        self.doc_path = os.path.join(self.test_dir, "test_doc.mdp")
        self.doc = Document.create(
            title="Test Document",
            author="Test Author",
            content="# Test Document\n\nThis is a test document.",
            version="1.0.0"
        )
        self.doc.save(self.doc_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_document_versioning_methods(self):
        """Test versioning methods on the Document class."""
        # Test version property
        self.assertEqual(self.doc.version, "1.0.0")
        
        # Test bump_version
        self.doc.bump_version("minor")
        self.assertEqual(self.doc.version, "1.1.0")
        
        # Save changes
        self.doc.save()
        
        # Test create_version
        version_path = self.doc.create_version(description="Test version")
        self.assertTrue(os.path.exists(version_path))
        
        # Test get_versions
        versions = self.doc.get_versions()
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]["version"], "1.1.1")
        
        # Create another version with different content
        self.doc.content = "# Modified Document\n\nThis is a modified document."
        self.doc.bump_version()
        self.doc.save()
        
        # Create another version
        version_path2 = self.doc.create_version(description="Modified version")
        self.assertTrue(os.path.exists(version_path2))
        
        # Get current version for comparison
        current_version = self.doc.version
        
        # Test compare_with_version
        diff = self.doc.compare_with_version("1.1.1")
        self.assertIn("content_diff", diff)
        
        # Test compare_versions
        diff2 = self.doc.compare_versions("1.1.1", current_version)
        self.assertIn("content_diff", diff2)
        
        # Test create_branch
        branch_doc = self.doc.create_branch("feature-branch")
        self.assertEqual(branch_doc.metadata.get("branch_name"), "feature-branch")
        
        # Modify branch
        branch_doc.content = "# Branched Document\n\nThis is a branch document."
        branch_doc.save()
        
        # Test merge_from_branch
        self.doc.merge_from_branch(branch_doc)
        self.assertEqual(self.doc.content.strip(), branch_doc.content.strip())


class TestVersionManagerUtils(unittest.TestCase):
    """Test utility functions for version management."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.doc_path = os.path.join(self.test_dir, "test_doc.mdp")
        
        # Create a test document
        doc = Document.create(
            title="Test Document",
            content="# Test Document"
        )
        doc.save(self.doc_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_get_version_manager(self):
        """Test get_version_manager utility function."""
        # Get version manager
        vm = get_version_manager(self.doc_path)
        
        # Check it's a VersionManager instance
        self.assertIsInstance(vm, VersionManager)
        
        # Check versions directory is set correctly
        expected_versions_dir = os.path.join(os.path.dirname(self.doc_path), ".versions")
        self.assertEqual(str(vm.versions_dir), expected_versions_dir)


if __name__ == "__main__":
    unittest.main() 