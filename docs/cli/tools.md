# MDP Tools and Utilities

The MDP toolkit provides a comprehensive set of tools for working with Markdown Data Pack files. These tools help with creating, validating, formatting, and analyzing MDP documents, enabling a more structured and robust document workflow.

## Command-Line Interface

The MDP toolkit provides a command-line interface (CLI) accessible via the `mdp` command. The CLI offers a wide range of functionality:

### Core Commands

- `mdp info <file>`: Display information about an MDP file
- `mdp create <title>`: Create a new MDP document
- `mdp content <file>`: Extract content or metadata from an MDP file
- `mdp dev`: Access development and debugging commands
  - `mdp dev --validate <file>`: Validate an MDP file
  - `mdp dev --metadata-schema`: Print the metadata schema

### Collection Management

- `mdp collection create <directory> <name>`: Create a collection from MDP files
- `mdp collection list <collection>`: List documents in a collection

### Version Control

- `mdp version create <file>`: Create a new version of a document
- `mdp version list <file>`: List all versions of a document
- `mdp version show <file> <version>`: Show a specific version of a document
- `mdp version compare <file> <version1> <version2>`: Compare two versions of a document
- `mdp version rollback <file> <version>`: Roll back to a previous version
- `mdp version branch <file> <name>`: Create a branch of a document
- `mdp version merge <branch> <target>`: Merge a branch into another document

### Conflict Resolution

- `mdp conflicts check <local> <remote>`: Check for conflicts between two documents
- `mdp conflicts merge <local> <remote>`: Automatically merge changes from two documents
- `mdp conflicts create-resolution-file <local> <remote>`: Create a file for manual conflict resolution
- `mdp conflicts apply-resolution <resolution_file>`: Apply a manually resolved conflict file
- `mdp conflicts check-concurrent <file>`: Check if a document has been modified concurrently

### Advanced Tools

#### MDP Doctor

The `doctor` tool provides comprehensive checking and diagnosis for MDP files.

```bash
mdp doctor <target>
```

Options:
- `--recursive`, `-r`: Recursively check directories
- `--profile`: Validation profile to use (minimal, standard, publication, collection, archival)
- `--fix`: Automatically fix common issues
- `--check-relationships`: Check relationship integrity
- `--check-versions`: Check version integrity
- `--with-lint`: Run linter as part of doctor checks
- `--format`: Output format (text, json)
- `--output`, `-o`: Output file for results

Example:
```bash
# Check a directory with all checks enabled
mdp doctor docs/ --recursive --check-relationships --check-versions --with-lint
```

#### MDP Lint

The `lint` tool checks MDP files for issues with metadata and content.

```bash
mdp lint <target>
```

Options:
- `--recursive`, `-r`: Recursively lint directories
- `--fix`: Automatically fix fixable issues
- `--config`: Path to lint configuration file
- `--format`: Output format (text, json, summary)
- `--output`, `-o`: Output file for results
- `--severity`: Minimum severity level to report
- `--category`: Only check rules in this category
- `--include-rule`: Include only specific rules
- `--exclude-rule`: Exclude specific rules

Example:
```bash
# Lint a directory and fix issues
mdp lint src/ --recursive --fix --category=metadata
```

#### MDP Format

The `format` tool automatically formats MDP files according to style guides.

```bash
mdp format <target>
```

Options:
- `--recursive`, `-r`: Recursively format directories
- `--dry-run`: Show what would be changed without making changes
- `--config`: Path to formatting configuration file
- `--metadata-order`: Comma-separated list of metadata fields in desired order
- `--sort-tags`: Sort tags alphabetically
- `--sort-relationships`: Sort relationships by type and then ID/path
- `--wrap-metadata`: Wrap metadata string values at specified column
- `--indent`: Number of spaces for YAML indentation
- `--normalize-headings`: Normalize heading levels in content
- `--wrap-content`: Wrap Markdown content at specified column
- `--fix-links`: Fix and normalize Markdown links

Example:
```bash
# Format with specific options
mdp format docs/ --recursive --sort-tags --normalize-headings
```

#### MDP Summarize

The `summarize` tool generates reports about MDP files and collections.

```bash
mdp summarize <target>
```

Options:
- `--recursive`, `-r`: Recursively summarize directories
- `--type`: Type of summary to generate (metadata, content, relationships, full, statistics)
- `--format`: Output format (text, json, yaml, csv)
- `--output`, `-o`: Output file for summary
- `--filter-tag`: Only include documents with specified tag(s)
- `--filter-author`: Only include documents with specified author(s)
- `--modified-after`: Only include documents modified after specified date
- `--modified-before`: Only include documents modified before specified date
- `--content-preview-length`: Length of content preview in characters
- `--sort-by`: Sort documents by specified field

Example:
```bash
# Generate a statistics report for all files by a specific author
mdp summarize docs/ --recursive --type=statistics --filter-author="Jane Doe" --format=json --output=report.json
```

#### MDP Diff

The `diff` tool compares MDP files and shows differences.

```bash
mdp diff <file1> <file2>
```

Options:
- `--mode`: Diff mode (unified, context, metadata, content, full)
- `--context`, `-c`: Number of context lines for unified and context diffs
- `--metadata-only`: Compare only metadata
- `--content-only`: Compare only content
- `--include-fields`: Comma-separated list of metadata fields to include in comparison
- `--exclude-fields`: Comma-separated list of metadata fields to exclude from comparison
- `--format`: Output format (text, json, html)
- `--output`, `-o`: Output file for diff results
- `--color`: When to use color in output (auto, always, never)

Example:
```bash
# Compare only metadata in HTML format
mdp diff old.mdp new.mdp --metadata-only --format=html --output=diff.html
```

#### Language Server Protocol (LSP)

The MDP package includes a Language Server Protocol implementation that provides rich editing capabilities for MDP files in compatible editors and IDEs.

```bash
mdp-language-server
```

Options:
- `--debug`: Enable debug logging
- `--log-file`: Path to the log file (default: ~/.mdp/lsp.log)
- `--tcp`: Use TCP server instead of stdio (not fully implemented yet)
- `--host`: TCP server host (default: 127.0.0.1)
- `--port`: TCP server port (default: 2087)

The LSP server provides:
- Syntax validation and diagnostics
- Autocompletion for metadata fields and Markdown elements
- Hover information for fields and values
- Document outline for navigation
- Automatic formatting

For detailed information about the LSP features and configuration, see the [LSP documentation](lsp.md).

Example:
```bash
# Start the LSP server with debug logging
mdp-language-server --debug
```

## Programmatic Usage

The MDP tools can also be used programmatically in Python code:

```python
import mdp
from mdp.lint import MDPLinter
from mdp.commands.doctor import DoctorReport

# Load a document
doc = mdp.Document.from_file("document.mdp")

# Use the linter
linter = MDPLinter()
result = linter.lint_file("document.mdp")
print(f"Found {result.error_count} errors, {result.warning_count} warnings")

# Run format
from mdp.commands.format import format_file, load_format_config
config = load_format_config({"sort_tags": True, "normalize_headings": True})
format_file("document.mdp", config)
```

## Configuration

Many MDP tools support configuration files to customize their behavior. Configuration files can be specified with the `--config` option and are typically in YAML or JSON format.

Example configuration for the format tool:

```yaml
metadata_order:
  - title
  - uuid
  - version
  - author
  - created_at
  - updated_at
  - tags
  - relationships
sort_tags: true
normalize_headings: true
wrap_content: 80
fix_links: true
```

## Getting Help

For more information about any command, use the `--help` option:

```bash
mdp --help
mdp doctor --help
mdp lint --help
``` 