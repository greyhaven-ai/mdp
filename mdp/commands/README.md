# MDP CLI Tools

This directory contains the CLI command modules for the MDP (Markdown Data Pack) toolkit. Each module provides specialized functionality to help you work more effectively with MDP files.

## Available Tools

### 1. mdp-doctor

The `doctor` tool checks MDP files and collections for issues, providing comprehensive diagnostics and suggested fixes.

```bash
# Basic usage
mdp doctor my-file.mdp

# Check a directory with all options
mdp doctor my-directory/ --recursive --check-relationships --check-versions --with-lint --profile=standard --fix
```

Key features:
- Basic metadata validation
- Relationship integrity checking
- Version history validation
- Integration with linter for in-depth analysis
- Automatic fixing of common issues
- Detailed suggestions for improvement

### 2. mdp-lint

The `lint` tool is a linter for MDP files that checks for issues with metadata, content structure, and relationships.

```bash
# Basic usage
mdp lint my-file.mdp

# Lint a directory and fix issues
mdp lint my-directory/ --recursive --fix --format=json
```

Key features:
- YAML frontmatter validation
- Required metadata field checking
- Metadata field type validation
- Semantic version format validation
- Markdown content structure validation
- Relationship integrity validation
- Configurable rules via JSON/YAML files

### 3. mdp format

The `format` tool automatically formats MDP files according to configurable style guides.

```bash
# Basic usage
mdp format my-file.mdp

# Format with specific options
mdp format my-directory/ --recursive --sort-tags --normalize-headings --wrap-content=80
```

Key features:
- Metadata field reordering
- Tag and relationship sorting
- Markdown content wrapping
- Heading level normalization
- Link fixing and normalization
- Configurable via command line or config file

### 4. mdp summarize

The `summarize` tool generates reports about MDP files and collections, providing insights about content, metadata, and relationships.

```bash
# Basic usage
mdp summarize my-file.mdp

# Generate a statistics report for all files by a specific author
mdp summarize my-directory/ --recursive --type=statistics --filter-author="Jane Doe" --format=json
```

Key features:
- Multiple report types (metadata, content, relationships, statistics, full)
- Filtering by tags, authors, and modification dates
- Multiple output formats (text, JSON, YAML, CSV)
- Content preview generation
- Statistical analysis of collections

### 5. mdp diff

The `diff` tool provides enhanced diff capabilities for comparing MDP files, with specialized handling for both metadata and content.

```bash
# Basic usage
mdp diff file1.mdp file2.mdp

# Compare only metadata in HTML format
mdp diff file1.mdp file2.mdp --metadata-only --format=html --output=diff.html
```

Key features:
- Specialized metadata comparison
- Detailed relationship diff
- Tag and list field difference highlighting
- Multiple output formats (text, JSON, HTML)
- Color-coded output
- Filtering of metadata fields to compare

## Integration with Main CLI

These commands are integrated into the main MDP CLI tool and can be accessed through the `mdp` command. Each module follows a consistent pattern:

1. An `add_X_parser` function that adds the command to the main CLI parser
2. A `handle_X` function that processes the command and returns an exit code
3. Helper functions for the specific functionality

## Configuration

Many of these tools support configuration files to customize their behavior. Configuration files can be specified with the `--config` option and are typically in YAML or JSON format.

## Common Options

Most commands share these common options:

- `--recursive`, `-r`: Process directories recursively
- `--output`, `-o`: Specify an output file
- `--format`: Specify output format (text, JSON, etc.)

## Contributing

To add a new CLI command:

1. Create a new module in this directory
2. Define the `add_X_parser` and `handle_X` functions
3. Update the `__init__.py` file to include the new module
4. Update the main CLI file (`mdp/cli.py`) to import and register the new command 