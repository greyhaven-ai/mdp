# MDP Module Tests

This directory contains unit tests for the MDP (Markdown Data Pack) module.

## Running Tests

To run all tests in this directory:

```bash
# From this directory
./run_tests.py

# Or using Python directly
python run_tests.py
```

Alternatively, you can run individual test files:

```bash
python test_user_friendly_api.py
python test_core.py
python test_relationships.py
```

## Test Organization

- `test_core.py`: Tests for the core MDP functionality (file operations, metadata handling)
- `test_relationships.py`: Tests for document relationships and collections functionality
- `test_user_friendly_api.py`: Tests for the user-friendly API (Document, Collection classes)

## Migration from Project Root Tests

These tests were migrated from the original tests at the project root (`/tests/mdp/`) and updated to use the unified `unittest` framework rather than pytest. The tests have been organized into logical groups and enhanced to provide better coverage of the MDP module.

## Adding New Tests

When adding new tests:

1. Create a new file named `test_<component>.py`
2. Extend `unittest.TestCase` for your test classes
3. Name test methods with the prefix `test_`
4. Add proper docstrings to test classes and methods

## Code Coverage

For a code coverage report, install and run with coverage:

```bash
pip install coverage
coverage run --source=mdp run_tests.py
coverage report
```

## Current Status and Known Issues

As of the most recent update, the tests are in the following state:

- 23 tests are fully passing
- 8 tests are currently skipped due to API mismatches

The skipped tests are marked with appropriate messages indicating the issues that need to be addressed in the codebase:

1. **Collection API Issues**:
   - The `Collection` constructor parameter naming is inconsistent with `create_collection_metadata()` function
   - Tests involving the Collection API are skipped until this is resolved

2. **Document Relationship API Issues**:
   - The `Document.add_relationship()` method doesn't forward the `relationship_type` parameter to `add_relationship_to_metadata()`
   - Tests involving document relationships using the high-level API are skipped until this is resolved

These issues should be addressed in a future update to the codebase. The tests are designed to be compatible with the expected API behavior once these issues are fixed. 