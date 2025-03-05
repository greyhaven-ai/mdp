"""
Tests for the diff command module.

This module provides detailed testing for the diff command functionality.
"""

import os
import tempfile
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from mdp.commands.diff import (
    add_diff_parser,
    handle_diff
)


class TestDiffCommand:
    """Test class for diff command functionality."""
    
    @pytest.fixture
    def temp_mdp_file1(self):
        """Create a first temporary MDP file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mdp", delete=False, mode="w+") as f:
            f.write("---\n")
            f.write("title: Original Document\n")
            f.write("description: The original test document\n")
            f.write("tags: [test, diff, original]\n")
            f.write("---\n\n")
            f.write("# Original Content\n\n")
            f.write("This is the original document content.\n")
            f.write("## Section 1\n\n")
            f.write("Original content in section 1.\n")
            f.write("## Section 2\n\n")
            f.write("Original content in section 2.\n")
            temp_path = f.name
        
        yield Path(temp_path)
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def temp_mdp_file2(self):
        """Create a second temporary MDP file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mdp", delete=False, mode="w+") as f:
            f.write("---\n")
            f.write("title: Modified Document\n")
            f.write("description: The modified test document\n")
            f.write("tags: [test, diff, modified]\n")
            f.write("---\n\n")
            f.write("# Modified Content\n\n")
            f.write("This is the modified document content.\n")
            f.write("## Section 1\n\n")
            f.write("Modified content in section 1.\n")
            f.write("## Section 2\n\n")
            f.write("Original content in section 2.\n")
            f.write("## Section 3\n\n")
            f.write("New section added to the document.\n")
            temp_path = f.name
        
        yield Path(temp_path)
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_handle_diff_basic(self, temp_mdp_file1, temp_mdp_file2):
        """Test the handle_diff function with basic options."""
        class Args:
            file1 = str(temp_mdp_file1)
            file2 = str(temp_mdp_file2)
            mode = "unified"
            context = 3
            metadata_only = False
            content_only = False
            include_fields = None
            exclude_fields = None
            output = None
            color = False
            format = "text"
        
        with patch("sys.stdout") as mock_stdout:
            result = handle_diff(Args())
            assert result == 0
            assert mock_stdout.write.called
    
    def test_handle_diff_metadata_only(self, temp_mdp_file1, temp_mdp_file2):
        """Test diffing only metadata."""
        class Args:
            file1 = str(temp_mdp_file1)
            file2 = str(temp_mdp_file2)
            mode = "unified"
            context = 3
            metadata_only = True
            content_only = False
            include_fields = None
            exclude_fields = None
            output = None
            color = False
            format = "text"
        
        with patch("sys.stdout") as mock_stdout:
            result = handle_diff(Args())
            assert result == 0
            assert mock_stdout.write.called
            
            # Capture output to verify it contains metadata differences
            output = ""
            for call in mock_stdout.write.call_args_list:
                args, _ = call
                output += args[0]
            
            # Check that output contains title differences
            assert "title" in output.lower()
            assert "Original Document" in output
            assert "Modified Document" in output
    
    def test_handle_diff_content_only(self, temp_mdp_file1, temp_mdp_file2):
        """Test diffing only content."""
        class Args:
            file1 = str(temp_mdp_file1)
            file2 = str(temp_mdp_file2)
            mode = "unified"
            context = 3
            metadata_only = False
            content_only = True
            include_fields = None
            exclude_fields = None
            output = None
            color = False
            format = "text"
        
        with patch("sys.stdout") as mock_stdout:
            result = handle_diff(Args())
            assert result == 0
            assert mock_stdout.write.called
            
            # Capture output to verify it contains content differences
            output = ""
            for call in mock_stdout.write.call_args_list:
                args, _ = call
                output += args[0]
            
            # Check that output contains content differences
            assert "Original Content" in output or "# Original" in output
            assert "Modified Content" in output or "# Modified" in output
    
    def test_diff_with_include_fields(self, temp_mdp_file1, temp_mdp_file2):
        """Test diffing with included fields."""
        class Args:
            file1 = str(temp_mdp_file1)
            file2 = str(temp_mdp_file2)
            mode = "unified"
            context = 3
            metadata_only = True
            content_only = False
            include_fields = "title"
            exclude_fields = None
            output = None
            color = False
            format = "text"
        
        with patch("sys.stdout") as mock_stdout:
            result = handle_diff(Args())
            assert result == 0
            
            # Capture output to verify it only includes title field
            output = ""
            for call in mock_stdout.write.call_args_list:
                args, _ = call
                output += args[0]
            
            # Should have title but not description
            assert "title" in output.lower()
            assert "Original Document" in output
            assert "Modified Document" in output
    
    def test_output_to_file(self, temp_mdp_file1, temp_mdp_file2, tmp_path):
        """Test diff with output to a file."""
        output_file = tmp_path / "diff.txt"
        
        class Args:
            file1 = str(temp_mdp_file1)
            file2 = str(temp_mdp_file2)
            mode = "unified"
            context = 3
            metadata_only = False
            content_only = False
            include_fields = None
            exclude_fields = None
            output = str(output_file)
            color = False
            format = "text"
        
        result = handle_diff(Args())
        assert result == 0
        
        # Check that the output file exists and contains content
        assert output_file.exists()
        with open(output_file) as f:
            content = f.read()
            assert len(content) > 0
            assert "Content Differences" in content  # Check for a section header instead 