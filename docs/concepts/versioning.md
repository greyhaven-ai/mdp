# MDP Document Versioning

This document describes the versioning system for MDP (Markdown Data Pack) documents. The versioning system provides robust support for tracking document changes over time, including version history, branching, and merging.

## Semantic Versioning

MDP documents use semantic versioning, following the pattern `MAJOR.MINOR.PATCH` (e.g., `1.2.3`):

- `MAJOR`: Incremented for backward-incompatible changes
- `MINOR`: Incremented for backward-compatible feature additions
- `PATCH`: Incremented for backward-compatible bug fixes

### Version Format

Valid version strings must follow these rules:
- Must contain exactly three numeric segments separated by periods
- Each segment must contain only digits (0-9)
- No leading zeros in any segment (except when the segment is exactly "0")
- No prefixes (e.g., "v1.0.0" is invalid)
- No suffixes (e.g., "1.0.0-beta" is invalid)

Examples of valid versions:
- `0.1.0`
- `1.0.0`
- `2.3.4`
- `10.20.30`

Examples of invalid versions:
- `1.0` (missing patch segment)
- `v1.0.0` (has prefix)
- `1.0.0-beta` (has suffix)
- `01.2.3` (leading zero)

## Version Storage

Version information is stored in two locations:

1. **Document Metadata**: Each document contains its current version in the metadata
2. **Version History**: A hidden `.versions` directory stores historical versions of documents

### Metadata Fields

The following metadata fields are related to versioning:

- `version`: The current semantic version of the document
- `latest_version`: The latest known version (useful for detecting concurrent modifications)
- `version_history`: An array of past versions with metadata

Example version history entry:
```json
{
  "version_history": [
    {
      "version": "1.0.0",
      "date": "2023-01-01T12:00:00Z",
      "author": "John Doe",
      "description": "Initial release"
    },
    {
      "version": "1.1.0",
      "date": "2023-02-15T09:30:00Z",
      "author": "Jane Smith",
      "description": "Added new section on widgets"
    }
  ]
}
```

## Versioning Operations

### Creating Versions

Versions can be created:
- Explicitly, by calling `create_version()` 
- Automatically, when certain operations occur (like merging branches)

When creating a version, you can specify:
- A specific version number (must be greater than current)
- A version bump type (major, minor, patch)
- Author information
- A description of changes

### Listing Versions

You can retrieve the version history of a document using:
- `get_versions()` on a Document instance
- `list_versions()` on a VersionManager instance
- The CLI command `mdp version list <file>`

### Comparing Versions

The versioning system supports comparing two versions to see:
- Metadata differences (added, removed, modified fields)
- Content differences (using intelligent text diff)

### Rollback

Documents can be rolled back to previous versions while preserving the version history.
Rolling back creates a new version with the content from the specified earlier version.

## Branching and Merging

### Branches

Branches create independent copies of documents that can evolve separately.
Each branch:
- Has its own version history
- Maintains a reference to its parent document
- Can be independently modified

### Branch Metadata

Branch documents contain additional metadata:
- `branch_name`: Name of the branch
- `branched_from`: Information about the parent document and version
- `relationships`: A relationship to the parent document

### Merging

Branches can be merged back into their parent document.
The merge process:
1. Applies content changes from the branch to the parent
2. Updates metadata with relevant fields from the branch
3. Updates the parent's version (typically a minor version bump)
4. Records merge information in `merge_history`

## Command Line Interface

The versioning system includes CLI commands:

```bash
# Create a new version
mdp version create path/to/document.mdp --bump minor --author "Jane Smith" --description "Added new section"

# List all versions
mdp version list path/to/document.mdp

# Show a specific version
mdp version show path/to/document.mdp 1.2.0

# Compare two versions
mdp version compare path/to/document.mdp 1.1.0 1.2.0

# Rollback to a previous version
mdp version rollback path/to/document.mdp 1.1.0

# Create a branch
mdp version branch path/to/document.mdp feature-branch

# Merge a branch
mdp version merge path/to/branch.mdp path/to/document.mdp
```

## Programmatic Usage

### Document Class

The Document class provides version-related methods:

```python
# Get current version
version = doc.version

# Update version
doc.version = "1.1.0"  # Must be valid semantic version

# Bump version
doc.bump_version("minor")  # Increments to next minor version

# Create version
doc.create_version(description="Added new content")

# Get version history
versions = doc.get_versions()

# Compare with version
diff = doc.compare_with_version("1.0.0")

# Rollback
doc.rollback_to_version("1.0.0")

# Create branch
branch = doc.create_branch("feature-branch")

# Merge from branch
doc.merge_from_branch(branch_doc)
```

### VersionManager Class

For lower-level operations, use the VersionManager class:

```python
from mdp.versioning import get_version_manager

# Get version manager for a document
vm = get_version_manager("path/to/document.mdp")

# Create version
vm.create_version(
    document_path="path/to/document.mdp",
    version="1.1.0",
    author="Jane Smith",
    description="Added new section"
)

# List versions
versions = vm.list_versions("path/to/document.mdp")

# Get specific version
version_doc = vm.get_version("path/to/document.mdp", "1.0.0")

# Compare versions
diff = vm.compare_versions("path/to/document.mdp", "1.0.0", "1.1.0")

# Rollback
vm.rollback_to_version("path/to/document.mdp", "1.0.0")

# Branch operations
branch_path = vm.create_branch("path/to/document.mdp", "feature-branch")
vm.merge_branch(branch_path, "path/to/document.mdp")
```

## Version Validation

The versioning system includes validation functions:

```python
from mdp.metadata import is_semantic_version, compare_semantic_versions, next_version

# Check if string is valid semantic version
is_valid = is_semantic_version("1.2.3")  # True

# Compare versions
result = compare_semantic_versions("1.0.0", "1.1.0")  # -1 (less than)

# Calculate next version
next_ver = next_version("1.2.3", "minor")  # "1.3.0"
``` 