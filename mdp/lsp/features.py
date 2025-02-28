"""
LSP feature implementations for MDP.

This module provides implementations for LSP features such as completions,
diagnostics, hover information, and more.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple, Any, Union

from ..metadata import STANDARD_METADATA_FIELDS, VALID_RELATIONSHIP_TYPES, validate_date_format
from ..lint import LintError, LintSeverity
from ..core import extract_metadata

logger = logging.getLogger("mdp-lsp.features")


def get_diagnostics_from_lint_result(lint_result) -> List[Dict[str, Any]]:
    """
    Convert a LintResult to LSP diagnostics.
    
    Args:
        lint_result: The lint result to convert
    
    Returns:
        List[Dict[str, Any]]: List of LSP diagnostic objects
    """
    diagnostics = []
    
    if not lint_result:
        return diagnostics
    
    for error in lint_result.errors:
        # Map our severity to LSP severity
        severity = 1  # Error
        if error.severity == LintSeverity.WARNING:
            severity = 2  # Warning
        elif error.severity == LintSeverity.INFO:
            severity = 3  # Information
        
        # Create a diagnostic with as much information as we have
        diagnostic = {
            "severity": severity,
            "message": error.message,
            "source": "mdp-lint",
            "code": error.rule_id
        }
        
        # Add location information if available
        if error.location:
            start_line = error.location.get("line", 0)
            start_char = error.location.get("character", 0)
            end_line = error.location.get("end_line", start_line)
            end_char = error.location.get("end_character", start_char + 1)
            
            diagnostic["range"] = {
                "start": {"line": start_line, "character": start_char},
                "end": {"line": end_line, "character": end_char}
            }
        else:
            # Default to beginning of file
            diagnostic["range"] = {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 1}
            }
        
        # Add related information if we have it
        if hasattr(error, "related_information") and error.related_information:
            diagnostic["relatedInformation"] = error.related_information
        
        diagnostics.append(diagnostic)
    
    return diagnostics


def get_completion_items_for_metadata(
    prefix: str, 
    line_text: str, 
    yaml_level: int = 0
) -> List[Dict[str, Any]]:
    """
    Get completion items for metadata fields.
    
    Args:
        prefix: The prefix text to use for filtering completions
        line_text: The full line text for context
        yaml_level: The current YAML indentation level
    
    Returns:
        List[Dict[str, Any]]: List of completion items
    """
    completion_items = []
    
    # Determine if we're trying to complete a field name or value
    is_field_name = ":" not in line_text
    
    if is_field_name:
        # Completing field names
        for field, info in STANDARD_METADATA_FIELDS.items():
            if prefix.lower() in field.lower():
                completion_items.append({
                    "label": field,
                    "kind": 14,  # Property
                    "detail": info.get("description", ""),
                    "documentation": {
                        "kind": "markdown",
                        "value": f"**{field}** ({info.get('type', Any).__name__})\n\n{info.get('description', '')}"
                    },
                    "insertText": f"{field}: ",
                    "sortText": f"0_{field}" if info.get("required", False) else f"1_{field}"
                })
    else:
        # Check which field we're completing a value for
        field_match = re.match(r'^\s*([a-zA-Z_]+):\s*(.*)$', line_text)
        if field_match:
            field_name = field_match.group(1)
            current_value = field_match.group(2).strip()
            
            # Handle specific fields with known values
            if field_name == "status":
                for status in ["draft", "published", "archived", "deprecated"]:
                    completion_items.append({
                        "label": status,
                        "kind": 12,  # Value
                        "insertText": status
                    })
            elif field_name == "collection_id_type":
                for id_type in ["uuid", "uri", "cid", "string"]:
                    completion_items.append({
                        "label": id_type,
                        "kind": 12,  # Value
                        "insertText": id_type
                    })
            elif field_name == "relationships":
                # Start a new relationship
                if yaml_level == 0:
                    completion_items.append({
                        "label": "relationships",
                        "kind": 15,  # Snippet
                        "insertText": "relationships:\n  - type: related\n    id: \"\"\n    title: \"\"",
                        "insertTextFormat": 2  # Snippet
                    })
                elif yaml_level == 1:
                    # Add a new relationship item
                    completion_items.append({
                        "label": "- type: ...",
                        "kind": 15,  # Snippet
                        "insertText": "- type: related\n  id: \"\"\n  title: \"\"",
                        "insertTextFormat": 2  # Snippet
                    })
                elif yaml_level == 2 and line_text.strip().startswith("type"):
                    # Relationship types
                    for rel_type in VALID_RELATIONSHIP_TYPES:
                        completion_items.append({
                            "label": rel_type,
                            "kind": 12,  # Value
                            "insertText": rel_type
                        })
            elif field_name == "tags" and yaml_level == 1:
                # Tag completions
                completion_items.append({
                    "label": "- tag",
                    "kind": 12,  # Value
                    "insertText": "- "
                })
    
    return completion_items


def get_yaml_schema_completions(document_text: str, position: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Get schema-based completions for the YAML section.
    
    Args:
        document_text: The entire document text
        position: The position object with line and character
    
    Returns:
        List[Dict[str, Any]]: List of completion items
    """
    line = position["line"]
    character = position["character"]
    
    # Get the current line
    lines = document_text.split('\n')
    if line >= len(lines):
        return []
    
    current_line = lines[line]
    line_prefix = current_line[:character]
    
    # Check if we're in the YAML frontmatter section
    in_frontmatter = False
    yaml_start_line = -1
    yaml_end_line = -1
    
    for i, line_text in enumerate(lines):
        if line_text.strip() == '---':
            if yaml_start_line == -1:
                yaml_start_line = i
            elif yaml_end_line == -1:
                yaml_end_line = i
                break
    
    if yaml_start_line != -1 and (yaml_end_line == -1 or line < yaml_end_line):
        in_frontmatter = yaml_start_line < line
    
    if not in_frontmatter:
        return []
    
    # Determine the YAML indentation level
    indentation = len(line_prefix) - len(line_prefix.lstrip())
    yaml_level = indentation // 2
    
    # Get the prefix for completion
    prefix = line_prefix.strip()
    
    # Get completions for metadata fields
    return get_completion_items_for_metadata(prefix, current_line, yaml_level)


def get_markdown_completions(document_text: str, position: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Get completions for the Markdown section.
    
    Args:
        document_text: The entire document text
        position: The position object with line and character
    
    Returns:
        List[Dict[str, Any]]: List of completion items
    """
    # Extract just the prefix text for context
    line = position["line"]
    character = position["character"]
    
    # Get the current line
    lines = document_text.split('\n')
    if line >= len(lines):
        return []
    
    current_line = lines[line]
    line_prefix = current_line[:character]
    
    # Check if we're in the Markdown section (after frontmatter)
    in_markdown = False
    yaml_markers = 0
    
    for i, line_text in enumerate(lines):
        if line_text.strip() == '---':
            yaml_markers += 1
        if yaml_markers >= 2 and i < line:
            in_markdown = True
            break
    
    if not in_markdown:
        return []
    
    # Determine what we're trying to complete
    completion_items = []
    
    # Heading completions
    if line_prefix.strip() == "" or line_prefix.strip().startswith("#"):
        for i in range(1, 7):
            heading = "#" * i + " "
            completion_items.append({
                "label": heading + "Heading",
                "kind": 15,  # Snippet
                "insertText": heading,
                "filterText": "#" * i
            })
    
    # Link completions
    if "[" in line_prefix and "](" not in line_prefix:
        completion_items.append({
            "label": "[]() Link",
            "kind": 15,  # Snippet
            "insertText": "]()",
            "filterText": "]("
        })
    
    # List completions
    if line_prefix.strip() == "":
        completion_items.append({
            "label": "- Unordered list item",
            "kind": 15,  # Snippet
            "insertText": "- ",
            "filterText": "-"
        })
        
        completion_items.append({
            "label": "1. Ordered list item",
            "kind": 15,  # Snippet
            "insertText": "1. ",
            "filterText": "1"
        })
    
    # Code block completions
    if line_prefix.strip() == "```" or line_prefix.strip() == "``":
        languages = ["python", "javascript", "typescript", "json", "yaml", "markdown", "bash", "sh"]
        for lang in languages:
            completion_items.append({
                "label": "```" + lang,
                "kind": 15,  # Snippet
                "insertText": lang + "\n\n```",
                "filterText": lang
            })
    
    return completion_items


def get_hover_information(document_text: str, position: Dict[str, int]) -> Optional[Dict[str, Any]]:
    """
    Get hover information for a given position in a document.
    
    Args:
        document_text: The entire document text
        position: The position object with line and character
    
    Returns:
        Optional[Dict[str, Any]]: Hover information if available, None otherwise
    """
    line = position["line"]
    character = position["character"]
    
    # Get the current line
    lines = document_text.split('\n')
    if line >= len(lines):
        return None
    
    current_line = lines[line]
    
    # Check if we're in the YAML frontmatter section
    in_frontmatter = False
    yaml_start_line = -1
    yaml_end_line = -1
    
    for i, line_text in enumerate(lines):
        if line_text.strip() == '---':
            if yaml_start_line == -1:
                yaml_start_line = i
            elif yaml_end_line == -1:
                yaml_end_line = i
                break
    
    if yaml_start_line != -1 and (yaml_end_line == -1 or line < yaml_end_line):
        in_frontmatter = yaml_start_line < line
    
    if in_frontmatter:
        # Try to extract the field name from the current line
        field_match = re.match(r'^\s*([a-zA-Z_]+):', current_line)
        if field_match:
            field_name = field_match.group(1)
            
            if field_name in STANDARD_METADATA_FIELDS:
                field_info = STANDARD_METADATA_FIELDS[field_name]
                field_type = field_info.get('type', Any).__name__
                field_desc = field_info.get('description', '')
                required = field_info.get('required', False)
                format_info = field_info.get('format', '')
                
                # Build a detailed markdown hover
                markdown = f"**{field_name}**\n\n"
                markdown += f"Type: `{field_type}`\n\n"
                markdown += f"{field_desc}\n\n"
                
                if required:
                    markdown += "**Required field**\n\n"
                
                if format_info:
                    markdown += f"Format: {format_info}\n\n"
                
                if field_name == "relationships":
                    markdown += "**Valid relationship types:**\n\n"
                    for rel_type in VALID_RELATIONSHIP_TYPES:
                        markdown += f"- `{rel_type}`\n"
                
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": markdown
                    }
                }
    
    # Check for specific hover information in Markdown
    else:
        # Handle URL/link hover
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, current_line):
            link_start = match.start()
            link_end = match.end()
            
            if link_start <= character < link_end:
                link_text = match.group(1)
                url = match.group(2)
                
                markdown = f"**Link**: [{link_text}]({url})\n\n"
                markdown += f"URL: {url}"
                
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": markdown
                    }
                }
    
    return None


def get_document_symbols(document_text: str) -> List[Dict[str, Any]]:
    """
    Get document symbols for outline view.
    
    Args:
        document_text: The entire document text
    
    Returns:
        List[Dict[str, Any]]: List of document symbols
    """
    symbols = []
    
    # Extract metadata and content
    try:
        metadata, content = extract_metadata(document_text)
        
        # Add metadata fields as symbols
        for field, value in metadata.items():
            if isinstance(value, str) or isinstance(value, (int, float, bool)):
                symbols.append({
                    "name": field,
                    "kind": 7,  # Property
                    "location": {
                        "uri": "",  # Will be filled in by the server
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 0, "character": 0}
                        }
                    }
                })
        
        # Add headings as symbols
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Find headings
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2)
                
                symbols.append({
                    "name": heading_text,
                    "kind": 13,  # String
                    "location": {
                        "uri": "",  # Will be filled in by the server
                        "range": {
                            "start": {"line": i, "character": 0},
                            "end": {"line": i, "character": len(line)}
                        }
                    }
                })
    except Exception as e:
        logger.error(f"Error extracting symbols: {e}")
    
    return symbols 