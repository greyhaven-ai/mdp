"""
Tests for the summarize command module.

This module provides detailed testing for the summarize command functionality.
"""

import os
import tempfile
import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

from mdp.commands.summarize import (
    add_summarize_parser,
    handle_summarize
)


class TestSummarizeCommand:
    """Test class for summarize command functionality."""
    
    @pytest.fixture
    def temp_mdp_file(self):
        """Create a temporary MDP file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mdp", delete=False, mode="w+") as f:
            f.write("---\n")
            f.write("title: Test Document\n")
            f.write("description: A test document for summarize testing\n")
            f.write("tags: [test, summarize]\n")
            f.write("---\n\n")
            f.write("# Test Content\n\n")
            f.write("This is a test document for summarize command testing.\n")
            f.write("## Section 1\n\n")
            f.write("Some content in section 1.\n")
            f.write("## Section 2\n\n")
            f.write("Some content in section 2.\n")
            temp_path = f.name
        
        yield Path(temp_path)
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def temp_mdp_dir(self):
        """Create a temporary directory with multiple MDP files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a few MDP files
            for i in range(3):
                file_path = Path(temp_dir) / f"test_{i}.mdp"
                with open(file_path, "w") as f:
                    f.write("---\n")
                    f.write(f"title: Test Document {i}\n")
                    f.write(f"description: A test document {i} for summarize testing\n")
                    f.write(f"tags: [test, summarize, doc{i}]\n")
                    f.write("---\n\n")
                    f.write(f"# Test Content {i}\n\n")
                    f.write(f"This is test document {i} for summarize command testing.\n")
            
            yield Path(temp_dir)
    
    def test_handle_summarize_file(self, temp_mdp_file):
        """Test the handle_summarize function with a file."""
        class Args:
            target = str(temp_mdp_file)
            recursive = False
            format = "text"
            output = None
            include_headings = True
            include_metadata = True
            include_content = True
            include_relationships = True
            content_preview_length = 100
            sort_by = "title"
            filter_tags = None
            filter_authors = None
            modified_after = None
            modified_before = None
            type = "full"
        
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = handle_summarize(Args())
            assert result == 0
            output = mock_stdout.getvalue()
            assert "MDP Summary Report" in output
    
    def test_handle_summarize_directory(self, temp_mdp_dir):
        """Test the handle_summarize function with a directory."""
        class Args:
            target = str(temp_mdp_dir)
            recursive = True
            format = "text"
            output = None
            include_headings = True
            include_metadata = True
            include_content = True
            include_relationships = True
            content_preview_length = 100
            sort_by = "title"
            filter_tags = None
            filter_authors = None
            modified_after = None
            modified_before = None
            type = "full"
        
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = handle_summarize(Args())
            assert result == 0
            output = mock_stdout.getvalue()
            assert "MDP Summary Report" in output
    
    def test_handle_summarize_json_format(self, temp_mdp_file):
        """Test the handle_summarize function with JSON output."""
        class Args:
            target = str(temp_mdp_file)
            recursive = False
            format = "json"
            output = None
            include_headings = True
            include_metadata = True
            include_content = True
            include_relationships = True
            content_preview_length = 100
            sort_by = "title"
            filter_tags = None
            filter_authors = None
            modified_after = None
            modified_before = None
            type = "full"
        
        with patch("sys.stdout") as mock_stdout:
            # Prepare to capture JSON output
            output_data = []
            def mock_write(text):
                output_data.append(text)
                return len(text)
            
            mock_stdout.write.side_effect = mock_write
            
            result = handle_summarize(Args())
            assert result == 0
            
            # Combine captured output and parse as JSON
            try:
                output_json = "".join(output_data)
                json_data = json.loads(output_json)
                assert isinstance(json_data, dict)
                # Verify JSON data contains expected keys
                if "documents" in json_data:
                    assert len(json_data["documents"]) >= 1
                    doc = json_data["documents"][0]
                    assert "title" in doc
                    assert doc["title"] == "Test Document"
            except json.JSONDecodeError as e:
                pytest.fail(f"Output is not valid JSON: {e}\nOutput: {output_json}")
    
    def test_output_to_file(self, temp_mdp_file, tmp_path):
        """Test summarize with output to a file."""
        output_file = tmp_path / "summary.json"
        
        class Args:
            target = str(temp_mdp_file)
            recursive = False
            format = "json"
            output = str(output_file)
            include_headings = True
            include_metadata = True
            include_content = True
            include_relationships = True
            content_preview_length = 100
            sort_by = "title"
            filter_tags = None
            filter_authors = None
            modified_after = None
            modified_before = None
            type = "full"
        
        result = handle_summarize(Args())
        assert result == 0
        
        # Check that the output file exists and contains valid JSON
        assert output_file.exists()
        with open(output_file) as f:
            try:
                data = json.load(f)
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                pytest.fail("Output file does not contain valid JSON") 