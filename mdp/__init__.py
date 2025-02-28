"""
MDP (Markdown Data Pack) is a file format and toolkit for working with
documents that combine Markdown content with structured metadata.
"""

# Direct imports for convenience
from .document import Document
from .collection import Collection
from .core import MDPFile, read_mdp, write_mdp
from .metadata import create_metadata, get_standard_fields
from .utils import find_mdp_files

# Define version
__version__ = "0.2.0"

# CLI entry point
def cli():
    """Command-line interface entry point."""
    from .cli import main
    main()

# LSP entry point
def lsp_server():
    """Language Server entry point."""
    from .lsp.cli import main
    main()

# What to import with "from mdp import *"
__all__ = [
    "Document",
    "Collection",
    "MDPFile",
    "read_mdp",
    "write_mdp",
    "create_metadata",
    "get_standard_fields",
    "find_mdp_files"
]

# Features available in this version:
# - Document creation and manipulation
# - Collection management
# - Metadata validation
# - Schema validation
# - Versioning
# - Conflict resolution
# - Document linting (mdp-lint)
# - Health checks (mdp-doctor)
# - Format standardization (mdp format)
# - Document summarization (mdp summarize)
# - Enhanced diff (mdp diff)
# - Language Server Protocol support (LSP) 