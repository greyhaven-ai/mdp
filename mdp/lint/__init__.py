"""
MDP-Lint: Linter for Markdown Data Pack (MDP) files.

This module provides linting capabilities for MDP files, including:
- YAML frontmatter validation
- Markdown content linting
- Metadata field validation
- Relationship validation
"""

from .linter import MDPLinter, LintResult, LintError, LintSeverity
from .rules import (
    Rule,
    MetadataRule,
    ContentRule,
    RelationshipRule,
    load_default_rules,
    load_custom_rules,
)

__all__ = [
    'MDPLinter',
    'LintResult',
    'LintError',
    'LintSeverity',
    'Rule',
    'MetadataRule',
    'ContentRule',
    'RelationshipRule',
    'load_default_rules',
    'load_custom_rules',
] 