#!/usr/bin/env python3
"""
Test runner for MDP module tests.

This script automatically discovers and runs all unit tests in the current directory.
"""

import unittest
import sys
import os


def main():
    """Discover and run all tests in the current directory."""
    # Get the current directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the project root to the Python path to ensure imports work correctly
    project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
    sys.path.insert(0, project_root)
    
    # Discover all test modules in the current directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(current_dir, pattern="test_*.py")
    
    # Create a test runner that will print results to the console
    test_runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = test_runner.run(test_suite)
    
    # Return a non-zero exit code if there were test failures
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main()) 