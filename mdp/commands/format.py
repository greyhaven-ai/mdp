"""
CLI commands for formatting MDP files.

The format tool provides automatic formatting of MDP files according to 
configurable style guides, ensuring consistent structure and styling across
all MDP documents.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
import textwrap

from ..core import MDPFile, read_mdp, write_mdp, extract_metadata
from ..document import Document


def add_format_parser(subparsers):
    """
    Add the format command to the CLI.
    
    Args:
        subparsers: Subparsers object from the main parser
    """
    format_parser = subparsers.add_parser(
        "format",
        help="Format MDP files according to style guidelines"
    )
    
    # Target to format
    format_parser.add_argument(
        "target",
        help="File or directory to format"
    )
    
    # Format options
    format_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively format directories"
    )
    
    format_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be formatted without making changes"
    )
    
    format_parser.add_argument(
        "--config",
        help="Path to formatting configuration file"
    )
    
    # Metadata options
    format_parser.add_argument(
        "--metadata-order",
        help="Comma-separated list of metadata fields in desired order"
    )
    
    format_parser.add_argument(
        "--sort-tags",
        action="store_true",
        help="Sort tags alphabetically"
    )
    
    format_parser.add_argument(
        "--sort-relationships",
        action="store_true",
        help="Sort relationships by type and then ID/path"
    )
    
    format_parser.add_argument(
        "--wrap-metadata",
        type=int,
        help="Wrap metadata string values at specified column"
    )
    
    format_parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Number of spaces for YAML indentation"
    )
    
    # Content options
    format_parser.add_argument(
        "--normalize-headings",
        action="store_true",
        help="Normalize heading levels in content"
    )
    
    format_parser.add_argument(
        "--wrap-content",
        type=int,
        help="Wrap Markdown content at specified column"
    )
    
    format_parser.add_argument(
        "--fix-links",
        action="store_true",
        help="Fix and normalize Markdown links"
    )


def handle_format(args):
    """
    Handle the format command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    target_path = Path(args.target)
    
    # Check if the target exists
    if not target_path.exists():
        print(f"Error: Target not found: {target_path}", file=sys.stderr)
        return 1
    
    # Load configuration
    config = {}
    if args.config:
        config = load_format_config(args.config)
    
    # Override configuration with command-line arguments
    if args.metadata_order:
        config["metadata_order"] = args.metadata_order.split(',')
    
    if args.sort_tags:
        config["sort_tags"] = True
    
    if args.sort_relationships:
        config["sort_relationships"] = True
    
    if args.wrap_metadata is not None:
        config["wrap_metadata"] = args.wrap_metadata
    
    if args.indent != 2:
        config["indent"] = args.indent
    
    if args.normalize_headings:
        config["normalize_headings"] = True
    
    if args.wrap_content is not None:
        config["wrap_content"] = args.wrap_content
    
    if args.fix_links:
        config["fix_links"] = True
    
    # Format files
    if target_path.is_dir():
        # Format files in directory
        return format_directory(
            target_path,
            recursive=args.recursive,
            dry_run=args.dry_run,
            config=config
        )
    else:
        # Format a single file
        try:
            result = format_file(
                target_path,
                dry_run=args.dry_run,
                **config
            )
            
            if args.dry_run:
                if result:
                    print(f"Would format: {target_path}")
                else:
                    print(f"No changes needed: {target_path}")
            else:
                if result:
                    print(f"Formatted: {target_path}")
                else:
                    print(f"No changes needed: {target_path}")
            
            return 0
        except Exception as e:
            print(f"Error formatting {target_path}: {e}", file=sys.stderr)
            return 1


def load_format_config(config_path) -> Dict[str, Any]:
    """
    Load formatting configuration from a file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    if isinstance(config_path, dict):
        # Allow passing a dictionary directly for internal API use
        return config_path
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
            # Ensure we have a dictionary
            if not isinstance(config, dict):
                print(f"Warning: Invalid configuration in {config_path}, using defaults", file=sys.stderr)
                return {}
            
            return config
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        return {}


def format_directory(
    directory_path: Path,
    recursive: bool = False,
    dry_run: bool = False,
    config: Dict[str, Any] = None
) -> int:
    """
    Format all MDP files in a directory.
    
    Args:
        directory_path: Directory path
        recursive: Whether to format files in subdirectories
        dry_run: Whether to show what would be formatted without making changes
        config: Formatting configuration
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if config is None:
        config = {}
    
    # Find all MDP files
    mdp_files = []
    
    if recursive:
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.mdp'):
                    mdp_files.append(Path(root) / file)
    else:
        for file in directory_path.iterdir():
            if file.is_file() and file.suffix == '.mdp':
                mdp_files.append(file)
    
    # Format each file
    success = True
    formatted_count = 0
    
    for file_path in mdp_files:
        try:
            result = format_file(
                file_path,
                dry_run=dry_run,
                **config
            )
            
            if result:
                formatted_count += 1
                if dry_run:
                    print(f"Would format: {file_path}")
                else:
                    print(f"Formatted: {file_path}")
        except Exception as e:
            print(f"Error formatting {file_path}: {e}", file=sys.stderr)
            success = False
    
    # Print summary
    if dry_run:
        print(f"Would format {formatted_count} of {len(mdp_files)} files")
    else:
        print(f"Formatted {formatted_count} of {len(mdp_files)} files")
    
    return 0 if success else 1


def format_file(
    file_path: Path,
    dry_run: bool = False,
    metadata_order: Optional[List[str]] = None,
    sort_tags: bool = False,
    sort_relationships: bool = False,
    wrap_metadata: Optional[int] = None,
    indent: int = 2,
    normalize_headings: bool = False,
    wrap_content: Optional[int] = None,
    fix_links: bool = False
) -> bool:
    """
    Format an MDP file.
    
    Args:
        file_path: File path
        dry_run: Whether to show what would be formatted without making changes
        metadata_order: Order of metadata fields
        sort_tags: Whether to sort tags alphabetically
        sort_relationships: Whether to sort relationships by type and then ID/path
        wrap_metadata: Column width to wrap metadata string values
        indent: Number of spaces for YAML indentation
        normalize_headings: Whether to normalize heading levels in content
        wrap_content: Column width to wrap Markdown content
        fix_links: Whether to fix and normalize Markdown links
        
    Returns:
        bool: True if changes were made, False otherwise
    """
    # Read the file
    mdp_file = read_mdp(file_path)
    
    # Format the file contents
    formatted_text = format_string(
        mdp_file.to_string(),
        metadata_order=metadata_order,
        sort_tags=sort_tags,
        sort_relationships=sort_relationships,
        wrap_metadata=wrap_metadata,
        indent=indent,
        normalize_headings=normalize_headings,
        wrap_content=wrap_content,
        fix_links=fix_links
    )
    
    # Check if there are changes
    if formatted_text == mdp_file.to_string():
        return False
    
    # Apply changes if not dry run
    if not dry_run:
        with open(file_path, 'w') as f:
            f.write(formatted_text)
    
    return True


def format_string(
    content: str,
    metadata_order: Optional[List[str]] = None,
    sort_tags: bool = False,
    sort_relationships: bool = False,
    wrap_metadata: Optional[int] = None,
    indent: int = 2,
    normalize_headings: bool = False,
    wrap_content: Optional[int] = None,
    fix_links: bool = False
) -> str:
    """
    Format an MDP string.
    
    Args:
        content: MDP content as a string
        metadata_order: Order of metadata fields
        sort_tags: Whether to sort tags alphabetically
        sort_relationships: Whether to sort relationships by type and then ID/path
        wrap_metadata: Column width to wrap metadata string values
        indent: Number of spaces for YAML indentation
        normalize_headings: Whether to normalize heading levels in content
        wrap_content: Column width to wrap Markdown content
        fix_links: Whether to fix and normalize Markdown links
        
    Returns:
        str: Formatted MDP string
    """
    # Extract metadata and content
    metadata, markdown_content = extract_metadata(content)
    
    # Format metadata
    formatted_metadata = format_metadata(
        metadata,
        order=metadata_order,
        sort_tags=sort_tags,
        sort_relationships=sort_relationships,
        wrap_width=wrap_metadata,
        indent=indent
    )
    
    # Format content
    formatted_content = format_markdown_content(
        markdown_content,
        normalize_headings=normalize_headings,
        wrap_width=wrap_content,
        fix_links=fix_links
    )
    
    # Combine metadata and content
    return f"---\n{formatted_metadata}---\n\n{formatted_content}"


def format_metadata(
    metadata: Dict[str, Any],
    order: Optional[List[str]] = None,
    sort_tags: bool = False,
    sort_relationships: bool = False,
    wrap_width: Optional[int] = None,
    indent: int = 2
) -> str:
    """
    Format metadata dictionary as YAML.
    
    Args:
        metadata: Metadata dictionary
        order: Order of metadata fields
        sort_tags: Whether to sort tags alphabetically
        sort_relationships: Whether to sort relationships by type and then ID/path
        wrap_width: Column width to wrap string values
        indent: Number of spaces for indentation
        
    Returns:
        str: Formatted YAML string
    """
    # Make a copy of the metadata
    metadata = metadata.copy()
    
    # Sort tags if requested
    if sort_tags and "tags" in metadata and isinstance(metadata["tags"], list):
        metadata["tags"] = sorted(metadata["tags"])
    
    # Sort relationships if requested
    if sort_relationships and "relationships" in metadata and isinstance(metadata["relationships"], list):
        def relationship_key(rel):
            # Sort by type first, then by ID or path
            rel_type = rel.get("type", "")
            rel_id = rel.get("id", rel.get("path", rel.get("uri", "")))
            return (rel_type, rel_id)
        
        metadata["relationships"] = sorted(metadata["relationships"], key=relationship_key)
    
    # Reorder fields if order is specified
    ordered_metadata = {}
    
    if order:
        # Add fields in specified order
        for field in order:
            if field in metadata:
                ordered_metadata[field] = metadata[field]
        
        # Add remaining fields
        for field, value in metadata.items():
            if field not in ordered_metadata:
                ordered_metadata[field] = value
        
        metadata = ordered_metadata
    
    # Default order for common fields if no order specified
    elif not order:
        common_fields = [
            "title", "uuid", "version", "author", "created_at", "updated_at",
            "tags", "status", "collection", "collection_id"
        ]
        
        ordered_metadata = {}
        
        # Add common fields first
        for field in common_fields:
            if field in metadata:
                ordered_metadata[field] = metadata[field]
        
        # Add remaining fields
        for field, value in metadata.items():
            if field not in ordered_metadata:
                ordered_metadata[field] = value
        
        metadata = ordered_metadata
    
    # Format as YAML
    yaml_str = yaml.dump(
        metadata,
        default_flow_style=False,
        sort_keys=False,
        indent=indent,
        width=wrap_width
    )
    
    return yaml_str


def format_markdown_content(
    content: str,
    normalize_headings: bool = False,
    wrap_width: Optional[int] = None,
    fix_links: bool = False
) -> str:
    """
    Format Markdown content.
    
    Args:
        content: Markdown content
        normalize_headings: Whether to normalize heading levels
        wrap_width: Column width to wrap text
        fix_links: Whether to fix and normalize links
        
    Returns:
        str: Formatted Markdown content
    """
    # Normalize headings
    if normalize_headings:
        content = normalize_markdown_headings(content)
    
    # Fix links
    if fix_links:
        content = fix_markdown_links(content)
    
    # Wrap text
    if wrap_width:
        content = wrap_markdown_text(content, width=wrap_width)
    
    return content


def normalize_markdown_headings(content: str) -> str:
    """
    Normalize heading levels in Markdown content.
    
    Ensures that headings start at level 1 and are properly nested.
    
    Args:
        content: Markdown content
        
    Returns:
        str: Normalized Markdown content
    """
    lines = content.split('\n')
    heading_pattern = re.compile(r'^(#+)\s+(.+)$')
    
    # Find the minimum heading level
    min_level = 6
    for line in lines:
        match = heading_pattern.match(line)
        if match:
            level = len(match.group(1))
            min_level = min(min_level, level)
    
    # Adjust heading levels
    if min_level > 1:
        adjustment = min_level - 1
        
        for i, line in enumerate(lines):
            match = heading_pattern.match(line)
            if match:
                hashes = match.group(1)
                text = match.group(2)
                
                new_level = len(hashes) - adjustment
                new_hashes = '#' * new_level
                
                lines[i] = f"{new_hashes} {text}"
    
    return '\n'.join(lines)


def fix_markdown_links(content: str) -> str:
    """
    Fix and normalize Markdown links.
    
    Args:
        content: Markdown content
        
    Returns:
        str: Markdown content with fixed links
    """
    # Fix links with spaces
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    def replace_link(match):
        link_text = match.group(1)
        link_url = match.group(2).strip()
        
        # Replace spaces with %20
        link_url = link_url.replace(' ', '%20')
        
        return f"[{link_text}]({link_url})"
    
    content = link_pattern.sub(replace_link, content)
    
    return content


def wrap_markdown_text(content: str, width: int = 80) -> str:
    """
    Wrap Markdown text to a specified width.
    
    Args:
        content: Markdown content
        width: Column width to wrap at
        
    Returns:
        str: Wrapped Markdown content
    """
    lines = content.split('\n')
    wrapped_lines = []
    
    # Patterns to identify lines that shouldn't be wrapped
    heading_pattern = re.compile(r'^#+\s+')
    list_pattern = re.compile(r'^(\s*[-*+]|\s*\d+\.)\s+')
    code_block_pattern = re.compile(r'^```')
    
    in_code_block = False
    current_paragraph = []
    
    for line in lines:
        # Toggle code block state
        if code_block_pattern.match(line):
            in_code_block = not in_code_block
            
            # Flush current paragraph
            if current_paragraph:
                wrapped_text = textwrap.fill(
                    ' '.join(current_paragraph),
                    width=width,
                    break_long_words=False,
                    break_on_hyphens=False
                )
                wrapped_lines.append(wrapped_text)
                current_paragraph = []
            
            wrapped_lines.append(line)
            continue
        
        # Don't wrap inside code blocks
        if in_code_block:
            wrapped_lines.append(line)
            continue
        
        # Don't wrap headings, list items, or empty lines
        if (heading_pattern.match(line) or 
            list_pattern.match(line) or 
            line.strip() == ''):
            
            # Flush current paragraph
            if current_paragraph:
                wrapped_text = textwrap.fill(
                    ' '.join(current_paragraph),
                    width=width,
                    break_long_words=False,
                    break_on_hyphens=False
                )
                wrapped_lines.append(wrapped_text)
                current_paragraph = []
            
            wrapped_lines.append(line)
        else:
            # Add to current paragraph
            current_paragraph.append(line)
    
    # Flush final paragraph
    if current_paragraph:
        wrapped_text = textwrap.fill(
            ' '.join(current_paragraph),
            width=width,
            break_long_words=False,
            break_on_hyphens=False
        )
        wrapped_lines.append(wrapped_text)
    
    return '\n'.join(wrapped_lines) 