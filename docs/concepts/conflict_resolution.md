# MDP Conflict Resolution

This document describes the conflict resolution system in MDP (Markdown Data Pack) for handling concurrent modifications to documents. The system provides both automatic and manual conflict resolution mechanisms.

## Understanding Document Conflicts

Conflicts occur when two or more users modify the same document independently, starting from a common ancestor version. The types of conflicts that can arise include:

1. **Metadata conflicts**: When the same metadata field is modified differently by different users
2. **Content conflicts**: When the same region of document content is modified differently

The MDP conflict resolution system handles both types automatically when possible, and provides tools for manual resolution when necessary.

## Conflict Detection

The conflict detection process works by comparing a local document with a remote document that have diverged from a common ancestor version:

1. The system identifies the common ancestor (base version)
2. It compares the local and remote changes against the base version
3. Conflicts are detected when the same part of the document is modified differently

```python
from mdp.document import Document

# Load documents
local_doc = Document.from_file("local.mdp")
remote_doc = Document.from_file("remote.mdp")

# Check for conflicts
has_conflicts, conflict_summary = local_doc.check_for_conflicts(remote_doc)

if has_conflicts:
    print("Conflicts detected!")
    print("Metadata conflicts:", conflict_summary["metadata_conflicts"])
    print("Content conflicts:", conflict_summary["content_conflicts"])
else:
    print("No conflicts detected")
```

## Conflict Resolution Approaches

### 1. Automatic Merging

For non-conflicting changes, the system can automatically merge both versions:

```python
# Attempt automatic merge
try:
    merged_doc = local_doc.auto_merge(remote_doc, "merged.mdp")
    print("Successfully merged documents")
except ConflictError:
    print("Cannot auto-merge due to conflicts")
```

Automatic merging is successful when:
- The changes in both documents affect different parts of content
- The changes modify different metadata fields
- One document has changes that the other doesn't have

### 2. Manual Resolution

When automatic merging fails, you can create a conflict resolution file for manual editing:

```python
# Create a conflict resolution file
resolution_path = local_doc.create_conflict_resolution_file(remote_doc, "resolution.mdp")

# After manually resolving conflicts in the file, apply the resolution:
resolved_doc = Document.resolve_from_conflict_file("resolution.mdp", "resolved.mdp")
```

The resolution file contains conflict markers in both metadata and content sections:

```
<<<<<<< LOCAL
Content from local document
=======
Content from remote document
>>>>>>> REMOTE
```

## Concurrent Modification Detection

To prevent unintended overwrites, the system can detect if a document has been modified concurrently:

```python
# Check if the document has been modified since we last read it
if doc.detect_concurrent_modification():
    print("Warning: Document has been modified by another user!")
```

This check is useful before saving a document that may have been edited by others in the meantime.

## Command Line Interface

The MDP CLI provides commands for conflict resolution:

```bash
# Check for conflicts
mdp conflicts check local.mdp remote.mdp

# Attempt automatic merge
mdp conflicts merge local.mdp remote.mdp --output merged.mdp

# Create a conflict resolution file
mdp conflicts create-resolution-file local.mdp remote.mdp --output resolution.mdp

# Apply a manually resolved conflict file
mdp conflicts apply-resolution resolution.mdp --output resolved.mdp

# Check for concurrent modifications
mdp conflicts check-concurrent document.mdp
```

## Three-way Merge Algorithm

The conflict resolution system uses a three-way merge algorithm:

1. **Base Version**: The common ancestor document from which both versions diverged
2. **Local Version**: The local copy of the document with changes
3. **Remote Version**: The remote copy of the document with different changes

The merge logic:
- Changes made only in one version are preserved
- Non-conflicting changes from both versions are combined
- Conflicting changes require manual resolution

## Conflict Resolution Workflow

A typical workflow for handling conflicts:

1. **Detect conflicts**: Use `check_for_conflicts()` or `mdp conflicts check`
2. **Try automatic merge**: Use `auto_merge()` or `mdp conflicts merge`
3. **If auto-merge fails**:
   - Create a resolution file
   - Edit the file manually to resolve conflicts
   - Apply the resolved file

## Conflict File Format

The conflict resolution file has two sections:

1. **Metadata Section**: YAML frontmatter with conflict markers for metadata fields
2. **Content Section**: Markdown content with conflict markers for content regions

Example metadata conflict:

```yaml
---
title: "Document Title"
author: <<<<<<< LOCAL
"Local Author"
=======
"Remote Author"
>>>>>>> REMOTE
---
```

Example content conflict:

```markdown
# Introduction

<<<<<<< LOCAL
This is the local version of the content.
=======
This is the remote version of the content.
>>>>>>> REMOTE
```

## Best Practices

1. **Use version control**: Regularly create versions of important documents
2. **Check for concurrent modifications**: Before saving, check if others have modified the document
3. **Perform auto-merge first**: Always try automatic merging before manual resolution
4. **Preserve intent**: When resolving conflicts manually, ensure the original intent of both changes is preserved when possible
5. **Validate after resolution**: Verify the resolved document behaves as expected
6. **Document conflicts**: When resolving significant conflicts, document the decisions made in version history

## Integration with Version Control Systems

The MDP conflict resolution system can be integrated with version control systems:

```python
# Example workflow with Git
local_doc = Document.from_file("document.mdp")
remote_doc = Document.from_file("document.mdp.remote")  # From git merge conflict

if local_doc.check_for_conflicts(remote_doc)[0]:
    # Create resolution file
    resolution_path = local_doc.create_conflict_resolution_file(remote_doc, "document.mdp.resolution")
    
    # After manual resolution:
    Document.resolve_from_conflict_file("document.mdp.resolution", "document.mdp")
```

## Programmatic Conflict Resolution

For applications that need to resolve conflicts programmatically:

```python
from mdp.conflict import Conflict, ConflictManager

# Create conflict manager
manager = ConflictManager()

# Check for conflicts
has_conflicts, conflict = manager.check_for_conflicts("local.mdp", "remote.mdp")

if has_conflicts and conflict:
    # Resolve specific metadata conflicts
    conflict.resolve_metadata_conflict("author", "Custom Author Value")
    
    # Resolve content conflicts
    conflict.resolve_content_conflict(0, conflict.content_conflicts[0]["local"])
    
    # Save merged document
    conflict.save_merged("merged.mdp")
```

## Limitations

- The current conflict detection algorithm may not handle complex content structures optimally
- Very large documents may experience performance issues during conflict detection
- The system does not currently support partial resolution (all conflicts must be resolved)

## Future Enhancements

Future versions of the conflict resolution system may include:
- Enhanced visualization of conflicts in graphical interfaces
- Intelligent conflict resolution suggestions
- Support for resolving conflicts across multiple documents
- Partial conflict resolution with state tracking 