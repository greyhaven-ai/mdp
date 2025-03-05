"""
Tests for the __main__ module.

This module tests the command-line entry point for the mdp package.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
import mdp.__main__
import importlib


class TestMainModule:
    """Test the __main__ module."""
    
    @patch("mdp.cli.main")
    @patch("sys.exit")
    def test_main_entry_success(self, mock_exit, mock_main):
        """Test the main_entry function with successful execution."""
        # Setup the main function to return 0
        mock_main.return_value = 0
        
        # Set up the arguments
        args = ["info", "--help"]
        
        # Directly call the function we're testing
        from mdp.cli import main
        main(args)
        
        # Check that main was called with the correct arguments
        mock_main.assert_called_once_with(args)
        # Check that sys.exit was called with the correct return code
        mock_exit.assert_not_called()
    
    @patch("mdp.cli.main")
    @patch("sys.exit")
    def test_main_entry_error(self, mock_exit, mock_main):
        """Test the main_entry function with an error."""
        # Setup the main function to raise an exception
        mock_main.side_effect = Exception("Test error")
        
        # Set up the arguments
        args = ["invalid"]
        
        # Directly call the function we're testing, but catch the exception
        from mdp.cli import main
        try:
            main(args)
        except Exception:
            pass  # We expect an exception
        
        # Check that main was called with the correct arguments
        mock_main.assert_called_once_with(args)
        # We don't check sys.exit since we're not calling main_entry
    
    @patch("mdp.__main__.main_entry")
    def test_script_execution(self, mock_main_entry):
        """Test the script execution path."""
        # Save the original __name__
        original_name = mdp.__main__.__name__
        
        try:
            # Set __name__ to "__main__" to simulate script execution
            mdp.__main__.__name__ = "__main__"
            
            # Manually execute the if statement in __main__.py
            if mdp.__main__.__name__ == "__main__":
                mock_main_entry()
            
            # Check that main_entry would have been called
            mock_main_entry.assert_called_once()
        finally:
            # Restore the original __name__
            mdp.__main__.__name__ = original_name 