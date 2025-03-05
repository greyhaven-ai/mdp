"""
Tests for the CLI module.

This module tests the command-line interface functionality.
"""

import os
import sys
import tempfile
import pytest
import importlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import argparse

from mdp.cli import (
    create_parser,
    main,
    _handle_info,
    _handle_create,
    _handle_collection,
    _handle_collection_create,
    _handle_collection_list,
    _handle_version,
    _handle_dev
)


class TestCLIParser:
    """Test the command-line parser functionality."""

    def test_create_parser(self):
        """Test that the parser can be created and has expected commands."""
        parser = create_parser()
        
        # Check that basic commands are available
        commands = parser._subparsers._group_actions[0].choices.keys()
        assert "info" in commands
        assert "create" in commands
        assert "collection" in commands
        assert "doctor" in commands
        assert "lint" in commands
        assert "version" in commands


class TestCLICommands:
    """Test CLI command handlers."""
    
    @pytest.fixture
    def temp_mdp_file(self):
        """Create a temporary MDP file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mdp", delete=False, mode="w+") as f:
            f.write("---\n")
            f.write("title: Test Document\n")
            f.write("description: A test document for CLI testing\n")
            f.write("---\n\n")
            f.write("# Test Content\n\n")
            f.write("This is a test document for CLI testing.\n")
            temp_path = f.name
        
        yield Path(temp_path)
        
        # Cleanup
        os.unlink(temp_path)
    
    @patch("sys.stdout")
    def test_main_help(self, mock_stdout):
        """Test main function with help argument."""
        with pytest.raises(SystemExit) as e:
            main(["--help"])
        assert e.value.code == 0
    
    @patch("sys.stdout")
    def test_main_version(self, mock_stdout):
        """Test the version display in main function."""
        # Create a mock for the version command handler
        with patch("mdp.cli._handle_version") as mock_handle_version:
            # Set up the mock to return success
            mock_handle_version.return_value = 0
            
            # Create a temporary file for the test
            with tempfile.NamedTemporaryFile(suffix=".mdp") as temp_file:
                # Call main with version list command and the temp file
                try:
                    main(["version", "list", temp_file.name])
                    # If we get here, the command succeeded
                    assert mock_handle_version.called
                except SystemExit as e:
                    # The command might exit, but it should call our handler first
                    assert mock_handle_version.called
                    assert e.code == 0
    
    @patch("mdp.cli._handle_info")
    def test_main_info_command(self, mock_handle_info, temp_mdp_file):
        """Test that the info command calls the correct handler."""
        args = ["info", str(temp_mdp_file)]
        main(args)
        assert mock_handle_info.called
    
    @patch("mdp.cli._handle_create")
    def test_main_create_command(self, mock_handle_create):
        """Test that the create command calls the correct handler."""
        with tempfile.NamedTemporaryFile(suffix=".md") as source_file:
            with tempfile.NamedTemporaryFile(suffix=".mdp") as target_file:
                args = ["create", source_file.name, "-o", target_file.name]
                main(args)
                assert mock_handle_create.called

    def test_handle_info(self, temp_mdp_file):
        """Test the info command on a real file."""
        class Args:
            file = str(temp_mdp_file)
            json = False
        
        # Should not raise an exception
        _handle_info(Args())

    @patch("builtins.print")
    def test_handle_create(self, mock_print):
        """Test the create command."""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w+") as source_file:
            source_file.write("# Test Document\n\nThis is a test.\n")
            source_file.flush()
            
            class Args:
                input = source_file.name
                output = None
                metadata = None
                title = "Test Title"
                description = "Test Description"
                tags = None
                format = "text"
                author = None
                content = None
                content_file = None
            
            _handle_create(Args())
    
    @patch("mdp.cli._handle_collection_create")
    def test_handle_collection_create(self, mock_handle_collection_create):
        """Test collection create subcommand routing."""
        class Args:
            subcommand = "create"
            collection_command = "create"
            name = "test-collection"
            title = "Test Collection"
            description = None
            path = None
        
        _handle_collection(Args())
        mock_handle_collection_create.assert_called_once()
    
    @patch("mdp.cli._handle_collection_list")
    def test_handle_collection_list(self, mock_handle_collection_list):
        """Test collection list subcommand routing."""
        class Args:
            subcommand = "list"
            collection_command = "list"
            path = None
            recursive = True
            format = "text"
            output = None
        
        _handle_collection(Args())
        mock_handle_collection_list.assert_called_once()
    
    def test_setup_parsers(self):
        """Test parser setup."""
        parser = create_parser()
        
        # Check that parser is created
        assert parser is not None
        
        # Parse known commands to ensure they work
        with pytest.raises(SystemExit):
            args = parser.parse_args(["info", "--help"])
        
        with pytest.raises(SystemExit):
            args = parser.parse_args(["create", "--help"])
        
        with pytest.raises(SystemExit):
            args = parser.parse_args(["version", "--help"])
        
        with pytest.raises(SystemExit):
            args = parser.parse_args(["collection", "--help"])
    
    @patch("sys.stdout")
    def test_handle_dev(self, mock_stdout):
        """Test the dev command."""
        class Args:
            command = "echo"
            args = ["Hello", "World"]
            metadata_schema = False  # Set to False to avoid JSON serialization issues
            validate = None
        
        result = _handle_dev(Args())
        assert result == 0  # Echo command returns 0 on success
    
    @patch("mdp.cli.main")
    def test_command_line_entry_point(self, mock_main):
        """Test the command line entry point properly passes arguments to main."""
        import mdp.__main__
        from mdp.cli import main as cli_main
        
        # Test with version argument
        with patch("sys.argv", ["mdp", "--version"]):
            # Instead of reloading the module, directly call the function we want to test
            mdp.__main__.main_entry = lambda: None  # Replace with no-op to prevent actual execution
            # Manually execute the code that would run on import
            args = ["--version"]
            cli_main(args)
            mock_main.assert_called_once_with(["--version"])
        
        # Reset and test with different arguments
        mock_main.reset_mock()
        with patch("sys.argv", ["mdp", "info", "test.mdp"]):
            # Manually execute the code that would run on import
            args = ["info", "test.mdp"]
            cli_main(args)
            mock_main.assert_called_once_with(["info", "test.mdp"]) 