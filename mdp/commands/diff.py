"""
CLI commands for comparing and diffing MDP files.

The diff tool provides enhanced comparison capabilities for MDP files,
enabling structured diffs of metadata and content.
"""

import os
import sys
import json
import difflib
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import yaml

from ..core import MDPFile, read_mdp
from ..document import Document


def add_diff_parser(subparsers):
    """
    Add the diff command to the CLI.
    
    Args:
        subparsers: Subparsers object from the main parser
    """
    diff_parser = subparsers.add_parser(
        "diff",
        help="Compare MDP files and show differences"
    )
    
    # Files to compare
    diff_parser.add_argument(
        "file1",
        help="First MDP file"
    )
    
    diff_parser.add_argument(
        "file2",
        help="Second MDP file"
    )
    
    # Diff options
    diff_parser.add_argument(
        "--mode",
        choices=["unified", "context", "metadata", "content", "full"],
        default="unified",
        help="Diff mode"
    )
    
    diff_parser.add_argument(
        "--context", "-c",
        type=int,
        default=3,
        help="Number of context lines for unified and context diffs"
    )
    
    diff_parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Compare only metadata (equivalent to --mode=metadata)"
    )
    
    diff_parser.add_argument(
        "--content-only",
        action="store_true",
        help="Compare only content (equivalent to --mode=content)"
    )
    
    diff_parser.add_argument(
        "--include-fields",
        help="Comma-separated list of metadata fields to include in comparison"
    )
    
    diff_parser.add_argument(
        "--exclude-fields",
        help="Comma-separated list of metadata fields to exclude from comparison"
    )
    
    # Output options
    diff_parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format"
    )
    
    diff_parser.add_argument(
        "--output", "-o",
        help="Output file for diff results (default: stdout)"
    )
    
    diff_parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="When to use color in output"
    )


def handle_diff(args):
    """
    Handle the diff command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    file1_path = Path(args.file1)
    file2_path = Path(args.file2)
    
    # Check if files exist
    if not file1_path.exists():
        print(f"Error: File not found: {file1_path}", file=sys.stderr)
        return 1
    
    if not file2_path.exists():
        print(f"Error: File not found: {file2_path}", file=sys.stderr)
        return 1
    
    # Read files
    try:
        mdp_file1 = read_mdp(file1_path)
        mdp_file2 = read_mdp(file2_path)
    except Exception as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        return 1
    
    # Determine mode based on arguments
    if args.metadata_only:
        mode = "metadata"
    elif args.content_only:
        mode = "content"
    else:
        mode = args.mode
    
    # Generate diff
    diff_result = generate_diff(
        mdp_file1, 
        mdp_file2, 
        mode=mode,
        context_lines=args.context,
        include_fields=args.include_fields.split(',') if args.include_fields else None,
        exclude_fields=args.exclude_fields.split(',') if args.exclude_fields else None
    )
    
    # Output diff
    output_diff(
        diff_result, 
        format=args.format,
        output=args.output,
        color=args.color,
        filenames=(str(file1_path), str(file2_path))
    )
    
    # Return success
    return 0


def generate_diff(
    mdp_file1: MDPFile, 
    mdp_file2: MDPFile, 
    mode: str = "unified",
    context_lines: int = 3,
    include_fields: Optional[List[str]] = None,
    exclude_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a diff between two MDP files.
    
    Args:
        mdp_file1: First MDP file
        mdp_file2: Second MDP file
        mode: Diff mode (unified, context, metadata, content, full)
        context_lines: Number of context lines for unified and context diffs
        include_fields: Metadata fields to include in comparison
        exclude_fields: Metadata fields to exclude from comparison
        
    Returns:
        Dictionary with diff results
    """
    result = {
        "mode": mode,
        "has_differences": False
    }
    
    # Handle different modes
    if mode in ["metadata", "full"]:
        metadata_diff = diff_metadata(
            mdp_file1.metadata, 
            mdp_file2.metadata,
            include_fields=include_fields,
            exclude_fields=exclude_fields
        )
        result["metadata_diff"] = metadata_diff
        result["has_differences"] = result["has_differences"] or metadata_diff["has_differences"]
    
    if mode in ["content", "full", "unified", "context"]:
        content_diff = diff_content(
            mdp_file1.content, 
            mdp_file2.content,
            mode=mode if mode in ["unified", "context"] else "unified",
            context_lines=context_lines
        )
        result["content_diff"] = content_diff
        result["has_differences"] = result["has_differences"] or content_diff["has_differences"]
    
    return result


def diff_metadata(
    metadata1: Dict[str, Any], 
    metadata2: Dict[str, Any],
    include_fields: Optional[List[str]] = None,
    exclude_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a diff between two metadata dictionaries.
    
    Args:
        metadata1: First metadata dictionary
        metadata2: Second metadata dictionary
        include_fields: Metadata fields to include in comparison
        exclude_fields: Metadata fields to exclude from comparison
        
    Returns:
        Dictionary with metadata diff results
    """
    # Filter fields based on include/exclude
    filtered_metadata1 = filter_metadata(metadata1, include_fields, exclude_fields)
    filtered_metadata2 = filter_metadata(metadata2, include_fields, exclude_fields)
    
    # Find added, removed, and changed fields
    added = {}
    removed = {}
    changed = {}
    
    # Find added and changed fields
    for key, value in filtered_metadata2.items():
        if key not in filtered_metadata1:
            added[key] = value
        elif filtered_metadata1[key] != value:
            changed[key] = {
                "old": filtered_metadata1[key],
                "new": value
            }
    
    # Find removed fields
    for key, value in filtered_metadata1.items():
        if key not in filtered_metadata2:
            removed[key] = value
    
    # Simple list fields
    list_fields_diff = {}
    
    # For key fields that are lists, provide a more detailed diff
    for key in ["tags", "authors", "keywords"]:
        if key in filtered_metadata1 and key in filtered_metadata2:
            if isinstance(filtered_metadata1[key], list) and isinstance(filtered_metadata2[key], list):
                old_set = set(filtered_metadata1[key])
                new_set = set(filtered_metadata2[key])
                
                if old_set != new_set:
                    list_fields_diff[key] = {
                        "added": list(new_set - old_set),
                        "removed": list(old_set - new_set)
                    }
    
    # Special handling for relationships
    relationships_diff = None
    if "relationships" in filtered_metadata1 and "relationships" in filtered_metadata2:
        if isinstance(filtered_metadata1["relationships"], list) and isinstance(filtered_metadata2["relationships"], list):
            relationships_diff = diff_relationships(
                filtered_metadata1["relationships"],
                filtered_metadata2["relationships"]
            )
    
    # Return the diff
    result = {
        "has_differences": bool(added or removed or changed or list_fields_diff or 
                               (relationships_diff and relationships_diff["has_differences"])),
        "added": added,
        "removed": removed,
        "changed": changed
    }
    
    if list_fields_diff:
        result["list_fields"] = list_fields_diff
    
    if relationships_diff:
        result["relationships"] = relationships_diff
    
    return result


def filter_metadata(
    metadata: Dict[str, Any],
    include_fields: Optional[List[str]] = None,
    exclude_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Filter metadata fields based on include/exclude lists.
    
    Args:
        metadata: Metadata dictionary
        include_fields: Fields to include (if None, include all)
        exclude_fields: Fields to exclude
        
    Returns:
        Filtered metadata dictionary
    """
    if include_fields:
        return {k: v for k, v in metadata.items() if k in include_fields}
    
    if exclude_fields:
        return {k: v for k, v in metadata.items() if k not in exclude_fields}
    
    return metadata


def diff_relationships(
    relationships1: List[Dict[str, Any]],
    relationships2: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate a diff between two relationship lists.
    
    Args:
        relationships1: First relationship list
        relationships2: Second relationship list
        
    Returns:
        Dictionary with relationship diff results
    """
    # Define a function to identify a relationship
    def rel_key(rel):
        # Create a tuple of the identifying fields
        # Prioritize id, then path, then uri
        key_parts = []
        
        # First the type
        key_parts.append(rel.get("type", ""))
        
        # Then the identifier
        for id_field in ["id", "path", "uri", "cid"]:
            if id_field in rel:
                key_parts.append(f"{id_field}:{rel[id_field]}")
                break
        else:
            key_parts.append("unknown")
        
        return tuple(key_parts)
    
    # Convert lists to dictionaries keyed by relationship identifier
    rel_dict1 = {rel_key(rel): rel for rel in relationships1}
    rel_dict2 = {rel_key(rel): rel for rel in relationships2}
    
    # Find added, removed, and changed relationships
    added_keys = set(rel_dict2.keys()) - set(rel_dict1.keys())
    removed_keys = set(rel_dict1.keys()) - set(rel_dict2.keys())
    common_keys = set(rel_dict1.keys()) & set(rel_dict2.keys())
    
    added = [rel_dict2[key] for key in added_keys]
    removed = [rel_dict1[key] for key in removed_keys]
    
    # Find changed relationships
    changed = []
    for key in common_keys:
        if rel_dict1[key] != rel_dict2[key]:
            changed.append({
                "old": rel_dict1[key],
                "new": rel_dict2[key]
            })
    
    # Return the diff
    return {
        "has_differences": bool(added or removed or changed),
        "added": added,
        "removed": removed,
        "changed": changed
    }


def diff_content(
    content1: str, 
    content2: str,
    mode: str = "unified",
    context_lines: int = 3
) -> Dict[str, Any]:
    """
    Generate a diff between two content strings.
    
    Args:
        content1: First content string
        content2: Second content string
        mode: Diff mode (unified or context)
        context_lines: Number of context lines
        
    Returns:
        Dictionary with content diff results
    """
    # Split into lines
    lines1 = content1.splitlines()
    lines2 = content2.splitlines()
    
    # Generate diff
    if mode == "unified":
        diff_lines = list(difflib.unified_diff(
            lines1, 
            lines2,
            n=context_lines,
            lineterm=''
        ))
    elif mode == "context":
        diff_lines = list(difflib.context_diff(
            lines1, 
            lines2,
            n=context_lines,
            lineterm=''
        ))
    else:
        # Fallback to unified diff
        diff_lines = list(difflib.unified_diff(
            lines1, 
            lines2,
            n=context_lines,
            lineterm=''
        ))
    
    # Return the diff
    return {
        "has_differences": len(diff_lines) > 0,
        "diff_lines": diff_lines,
        "diff_mode": mode
    }


def output_diff(
    diff_result: Dict[str, Any],
    format: str = "text",
    output: Optional[str] = None,
    color: str = "auto",
    filenames: Tuple[str, str] = ("a", "b")
):
    """
    Output the diff result.
    
    Args:
        diff_result: Diff result dictionary
        format: Output format (text, json, html)
        output: Output file (None for stdout)
        color: When to use color (auto, always, never)
        filenames: Tuple of filenames for display
    """
    # Determine if we should use color
    use_color = False
    if color == "always":
        use_color = True
    elif color == "auto":
        use_color = sys.stdout.isatty()
    
    # Open output file if specified
    out_file = None
    try:
        if output:
            out_file = open(output, "w")
        else:
            out_file = sys.stdout
        
        # Output in specified format
        if format == "json":
            output_json(diff_result, out_file)
        elif format == "html":
            output_html(diff_result, out_file, filenames)
        else:  # text
            output_text(diff_result, out_file, use_color, filenames)
    finally:
        if out_file and out_file != sys.stdout:
            out_file.close()


def output_json(diff_result: Dict[str, Any], output_file):
    """Output diff in JSON format."""
    json.dump(diff_result, output_file, indent=2)


def output_html(diff_result: Dict[str, Any], output_file, filenames: Tuple[str, str]):
    """Output diff in HTML format."""
    file1, file2 = filenames
    
    # HTML header
    output_file.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Diff: {file1} vs {file2}</title>
    <style>
        body {{ font-family: monospace; margin: 20px; }}
        .diff-header {{ font-weight: bold; margin-top: 20px; }}
        .diff-added {{ background-color: #e6ffed; color: #22863a; }}
        .diff-removed {{ background-color: #ffeef0; color: #cb2431; }}
        .diff-changed {{ background-color: #f1f8ff; }}
        .metadata-section {{ margin-bottom: 30px; }}
        .content-section {{ margin-top: 30px; }}
        .line-added {{ background-color: #e6ffed; }}
        .line-removed {{ background-color: #ffeef0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td {{ padding: 2px 5px; }}
    </style>
</head>
<body>
    <h1>MDP Diff: {file1} vs {file2}</h1>
""")
    
    # Check if there are differences
    if not diff_result["has_differences"]:
        output_file.write("<p>No differences found.</p>")
        output_file.write("</body></html>")
        return
    
    # Metadata diff
    if "metadata_diff" in diff_result:
        metadata_diff = diff_result["metadata_diff"]
        
        output_file.write('<div class="metadata-section">')
        output_file.write('<h2>Metadata Differences</h2>')
        
        if metadata_diff["has_differences"]:
            # Added fields
            if metadata_diff["added"]:
                output_file.write('<div class="diff-header">Added Fields:</div>')
                output_file.write('<table>')
                for key, value in metadata_diff["added"].items():
                    output_file.write(f'<tr class="diff-added"><td>{key}</td><td>{value}</td></tr>')
                output_file.write('</table>')
            
            # Removed fields
            if metadata_diff["removed"]:
                output_file.write('<div class="diff-header">Removed Fields:</div>')
                output_file.write('<table>')
                for key, value in metadata_diff["removed"].items():
                    output_file.write(f'<tr class="diff-removed"><td>{key}</td><td>{value}</td></tr>')
                output_file.write('</table>')
            
            # Changed fields
            if metadata_diff["changed"]:
                output_file.write('<div class="diff-header">Changed Fields:</div>')
                output_file.write('<table>')
                for key, value in metadata_diff["changed"].items():
                    output_file.write(f'<tr class="diff-changed"><td>{key}</td><td>{value["old"]} → {value["new"]}</td></tr>')
                output_file.write('</table>')
            
            # List fields
            if "list_fields" in metadata_diff:
                for field, changes in metadata_diff["list_fields"].items():
                    output_file.write(f'<div class="diff-header">Changes in {field}:</div>')
                    output_file.write('<table>')
                    
                    if changes["added"]:
                        for item in changes["added"]:
                            output_file.write(f'<tr class="diff-added"><td>+</td><td>{item}</td></tr>')
                    
                    if changes["removed"]:
                        for item in changes["removed"]:
                            output_file.write(f'<tr class="diff-removed"><td>-</td><td>{item}</td></tr>')
                    
                    output_file.write('</table>')
            
            # Relationships
            if "relationships" in metadata_diff and metadata_diff["relationships"]["has_differences"]:
                output_file.write('<div class="diff-header">Relationship Changes:</div>')
                
                rel_diff = metadata_diff["relationships"]
                if rel_diff["added"]:
                    output_file.write('<div>Added Relationships:</div>')
                    output_file.write('<table>')
                    for rel in rel_diff["added"]:
                        rel_type = rel.get("type", "unknown")
                        rel_id = rel.get("id", rel.get("path", rel.get("uri", "unknown")))
                        output_file.write(f'<tr class="diff-added"><td>{rel_type}</td><td>{rel_id}</td></tr>')
                    output_file.write('</table>')
                
                if rel_diff["removed"]:
                    output_file.write('<div>Removed Relationships:</div>')
                    output_file.write('<table>')
                    for rel in rel_diff["removed"]:
                        rel_type = rel.get("type", "unknown")
                        rel_id = rel.get("id", rel.get("path", rel.get("uri", "unknown")))
                        output_file.write(f'<tr class="diff-removed"><td>{rel_type}</td><td>{rel_id}</td></tr>')
                    output_file.write('</table>')
                
                if rel_diff["changed"]:
                    output_file.write('<div>Changed Relationships:</div>')
                    output_file.write('<table>')
                    for change in rel_diff["changed"]:
                        old_rel = change["old"]
                        new_rel = change["new"]
                        old_type = old_rel.get("type", "unknown")
                        new_type = new_rel.get("type", "unknown")
                        
                        rel_id = old_rel.get("id", old_rel.get("path", old_rel.get("uri", "unknown")))
                        output_file.write(f'<tr class="diff-changed"><td>{rel_id}</td><td>{old_type} → {new_type}</td></tr>')
                    output_file.write('</table>')
        else:
            output_file.write('<p>No metadata differences found.</p>')
        
        output_file.write('</div>')
    
    # Content diff
    if "content_diff" in diff_result:
        content_diff = diff_result["content_diff"]
        
        output_file.write('<div class="content-section">')
        output_file.write('<h2>Content Differences</h2>')
        
        if content_diff["has_differences"]:
            output_file.write('<pre>')
            
            for line in content_diff["diff_lines"]:
                if line.startswith('+'):
                    output_file.write(f'<div class="line-added">{html_escape(line)}</div>')
                elif line.startswith('-'):
                    output_file.write(f'<div class="line-removed">{html_escape(line)}</div>')
                else:
                    output_file.write(f'{html_escape(line)}\n')
            
            output_file.write('</pre>')
        else:
            output_file.write('<p>No content differences found.</p>')
        
        output_file.write('</div>')
    
    # HTML footer
    output_file.write("</body></html>")


def output_text(diff_result: Dict[str, Any], output_file, use_color: bool, filenames: Tuple[str, str]):
    """Output diff in text format."""
    file1, file2 = filenames
    
    # Define color codes if using color
    if use_color:
        RESET = "\033[0m"
        GREEN = "\033[32m"
        RED = "\033[31m"
        CYAN = "\033[36m"
        YELLOW = "\033[33m"
    else:
        RESET = GREEN = RED = CYAN = YELLOW = ""
    
    # Header
    output_file.write(f"MDP Diff: {file1} vs {file2}\n")
    output_file.write("=" * 60 + "\n\n")
    
    # Check if there are differences
    if not diff_result["has_differences"]:
        output_file.write("No differences found.\n")
        return
    
    # Metadata diff
    if "metadata_diff" in diff_result:
        metadata_diff = diff_result["metadata_diff"]
        
        output_file.write(f"{CYAN}Metadata Differences{RESET}\n")
        output_file.write("-" * 60 + "\n")
        
        if metadata_diff["has_differences"]:
            # Added fields
            if metadata_diff["added"]:
                output_file.write("Added Fields:\n")
                for key, value in metadata_diff["added"].items():
                    output_file.write(f"  {GREEN}+{key}: {value}{RESET}\n")
            
            # Removed fields
            if metadata_diff["removed"]:
                output_file.write("Removed Fields:\n")
                for key, value in metadata_diff["removed"].items():
                    output_file.write(f"  {RED}-{key}: {value}{RESET}\n")
            
            # Changed fields
            if metadata_diff["changed"]:
                output_file.write("Changed Fields:\n")
                for key, value in metadata_diff["changed"].items():
                    output_file.write(f"  {YELLOW}~{key}: {value['old']} → {value['new']}{RESET}\n")
            
            # List fields
            if "list_fields" in metadata_diff:
                for field, changes in metadata_diff["list_fields"].items():
                    output_file.write(f"Changes in {field}:\n")
                    
                    if changes["added"]:
                        for item in changes["added"]:
                            output_file.write(f"  {GREEN}+{item}{RESET}\n")
                    
                    if changes["removed"]:
                        for item in changes["removed"]:
                            output_file.write(f"  {RED}-{item}{RESET}\n")
            
            # Relationships
            if "relationships" in metadata_diff and metadata_diff["relationships"]["has_differences"]:
                output_file.write("Relationship Changes:\n")
                
                rel_diff = metadata_diff["relationships"]
                if rel_diff["added"]:
                    output_file.write("  Added Relationships:\n")
                    for rel in rel_diff["added"]:
                        rel_type = rel.get("type", "unknown")
                        rel_id = rel.get("id", rel.get("path", rel.get("uri", "unknown")))
                        output_file.write(f"    {GREEN}+{rel_type}: {rel_id}{RESET}\n")
                
                if rel_diff["removed"]:
                    output_file.write("  Removed Relationships:\n")
                    for rel in rel_diff["removed"]:
                        rel_type = rel.get("type", "unknown")
                        rel_id = rel.get("id", rel.get("path", rel.get("uri", "unknown")))
                        output_file.write(f"    {RED}-{rel_type}: {rel_id}{RESET}\n")
                
                if rel_diff["changed"]:
                    output_file.write("  Changed Relationships:\n")
                    for change in rel_diff["changed"]:
                        old_rel = change["old"]
                        new_rel = change["new"]
                        old_type = old_rel.get("type", "unknown")
                        new_type = new_rel.get("type", "unknown")
                        
                        rel_id = old_rel.get("id", old_rel.get("path", old_rel.get("uri", "unknown")))
                        output_file.write(f"    {YELLOW}~{rel_id}: {old_type} → {new_type}{RESET}\n")
        else:
            output_file.write("No metadata differences found.\n")
        
        output_file.write("\n")
    
    # Content diff
    if "content_diff" in diff_result:
        content_diff = diff_result["content_diff"]
        
        output_file.write(f"{CYAN}Content Differences{RESET}\n")
        output_file.write("-" * 60 + "\n")
        
        if content_diff["has_differences"]:
            for line in content_diff["diff_lines"]:
                if line.startswith('+'):
                    output_file.write(f"{GREEN}{line}{RESET}\n")
                elif line.startswith('-'):
                    output_file.write(f"{RED}{line}{RESET}\n")
                else:
                    output_file.write(f"{line}\n")
        else:
            output_file.write("No content differences found.\n")


def html_escape(text: str) -> str:
    """Escape HTML special characters in a string."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;')) 