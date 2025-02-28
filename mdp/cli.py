"""
Command-line interface for MDP file format utilities.

This module provides a CLI for working with MDP files and collections,
focusing on core operations for the Markdown Data Package format.
The module is streamlined to focus on essential file format operations
and excludes conversion functionality which is available in the Datapack platform.
"""

import argparse
import os
import sys
import json
from pathlib import Path
from typing import Optional, List

# Use direct imports from local modules
from .document import Document
from .collection import Collection
from .utils import find_mdp_files
from .versioning import get_version_manager

# Import command modules
from .commands.doctor import add_doctor_parser, handle_doctor
from .commands.lint import add_lint_parser, handle_lint
from .commands.format import add_format_parser, handle_format
from .commands.summarize import add_summarize_parser, handle_summarize
from .commands.diff import add_diff_parser, handle_diff


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.
    
    Returns:
        An ArgumentParser object
    """
    parser = argparse.ArgumentParser(
        description="MDP (Markdown Data Pack) command-line tools",
        prog="mdp"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Display information about MDP files")
    info_parser.add_argument("file", help="MDP file path")
    info_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new MDP file")
    create_parser.add_argument("title", help="Document title")
    create_parser.add_argument("--output", "-o", required=True, help="Output file path")
    create_parser.add_argument("--author", help="Document author")
    create_parser.add_argument("--tags", help="Comma-separated list of tags")
    create_parser.add_argument("--content", help="Document content (use - for stdin)")
    create_parser.add_argument("--content-file", help="File containing document content")
    
    # Versioning commands
    version_parser = subparsers.add_parser("version", help="Work with document versions")
    version_subparsers = version_parser.add_subparsers(dest="version_command", help="Version command")
    
    # Create version
    version_create_parser = version_subparsers.add_parser("create", help="Create a new version of a document")
    version_create_parser.add_argument("file", help="Document file path")
    version_create_parser.add_argument("--version", "-v", help="Version number (e.g., 1.0.0)")
    version_create_parser.add_argument("--author", "-a", help="Author of this version")
    version_create_parser.add_argument("--description", "-d", help="Description of changes")
    version_create_parser.add_argument("--bump", choices=["major", "minor", "patch"], 
                                    default="patch", help="Bump version (if --version not specified)")
    
    # List versions
    version_list_parser = version_subparsers.add_parser("list", help="List all versions of a document")
    version_list_parser.add_argument("file", help="Document file path")
    version_list_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Show version
    version_show_parser = version_subparsers.add_parser("show", help="Show a specific version of a document")
    version_show_parser.add_argument("file", help="Document file path")
    version_show_parser.add_argument("version", help="Version number to show")
    version_show_parser.add_argument("--metadata-only", action="store_true", help="Show only metadata")
    version_show_parser.add_argument("--content-only", action="store_true", help="Show only content")
    
    # Compare versions
    version_compare_parser = version_subparsers.add_parser("compare", help="Compare two versions of a document")
    version_compare_parser.add_argument("file", help="Document file path")
    version_compare_parser.add_argument("version1", help="First version to compare")
    version_compare_parser.add_argument("version2", help="Second version to compare")
    version_compare_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Rollback version
    version_rollback_parser = version_subparsers.add_parser("rollback", help="Roll back to a previous version")
    version_rollback_parser.add_argument("file", help="Document file path")
    version_rollback_parser.add_argument("version", help="Version to roll back to")
    version_rollback_parser.add_argument("--no-backup", action="store_true", help="Don't create a backup before rollback")
    
    # Branching
    branch_parser = version_subparsers.add_parser("branch", help="Create a branch of a document")
    branch_parser.add_argument("file", help="Document file path")
    branch_parser.add_argument("name", help="Branch name")
    branch_parser.add_argument("--base-version", help="Base version for the branch (defaults to latest)")
    
    # Merging
    merge_parser = version_subparsers.add_parser("merge", help="Merge a branch into another document")
    merge_parser.add_argument("branch", help="Branch document file path")
    merge_parser.add_argument("target", help="Target document file path")
    merge_parser.add_argument("--no-backup", action="store_true", help="Don't create a backup before merge")
    
    # Collection commands
    collection_parser = subparsers.add_parser("collection", help="Work with collections of MDP files")
    collection_subparsers = collection_parser.add_subparsers(dest="collection_command", help="Collection command")
    
    # Create collection
    coll_create_parser = collection_subparsers.add_parser("create", help="Create a collection from MDP files")
    coll_create_parser.add_argument("directory", help="Directory containing MDP files")
    coll_create_parser.add_argument("name", help="Collection name")
    coll_create_parser.add_argument("--output", "-o", required=True, help="Output JSON file")
    coll_create_parser.add_argument("--recursive", "-r", action="store_true", help="Search directories recursively")
    
    # List collection
    coll_list_parser = collection_subparsers.add_parser("list", help="List documents in a collection")
    coll_list_parser.add_argument("collection", help="Collection JSON file")
    coll_list_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Development and debugging commands
    dev_parser = subparsers.add_parser("dev", help="Development and debugging commands")
    dev_parser.add_argument("--metadata-schema", action="store_true", help="Print metadata schema")
    dev_parser.add_argument("--validate", help="Validate an MDP file")
    
    # Content extraction
    content_parser = subparsers.add_parser("content", help="Extract content from an MDP file")
    content_parser.add_argument("file", help="MDP file path")
    content_parser.add_argument("--metadata-only", action="store_true", help="Extract only metadata")
    content_parser.add_argument("--content-only", action="store_true", help="Extract only content")
    
    # Conflict resolution commands
    conflict_parser = subparsers.add_parser("conflicts", help="Work with document conflicts")
    conflict_subparsers = conflict_parser.add_subparsers(dest="conflict_command", help="Conflict command")
    
    # Check for conflicts
    check_parser = conflict_subparsers.add_parser("check", help="Check for conflicts between two documents")
    check_parser.add_argument("local", help="Path to local document")
    check_parser.add_argument("remote", help="Path to remote document")
    check_parser.add_argument("--base-version", help="Base version for comparison (optional)")
    check_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Auto-merge
    merge_parser = conflict_subparsers.add_parser("merge", help="Automatically merge changes from two documents")
    merge_parser.add_argument("local", help="Path to local document")
    merge_parser.add_argument("remote", help="Path to remote document")
    merge_parser.add_argument("--output", "-o", help="Output path for merged document (default: overwrite local)")
    merge_parser.add_argument("--base-version", help="Base version for comparison (optional)")
    
    # Create conflict resolution file
    resolve_parser = conflict_subparsers.add_parser("create-resolution-file", help="Create a file for manual conflict resolution")
    resolve_parser.add_argument("local", help="Path to local document")
    resolve_parser.add_argument("remote", help="Path to remote document")
    resolve_parser.add_argument("--output", "-o", required=True, help="Output path for resolution file")
    resolve_parser.add_argument("--base-version", help="Base version for comparison (optional)")
    
    # Apply resolved conflicts
    apply_parser = conflict_subparsers.add_parser("apply-resolution", help="Apply a manually resolved conflict file")
    apply_parser.add_argument("resolution_file", help="Path to the resolved conflict file")
    apply_parser.add_argument("--output", "-o", required=True, help="Output path for resolved document")
    
    # Check for concurrent modifications
    concurrent_parser = conflict_subparsers.add_parser("check-concurrent", help="Check if a document has been modified concurrently")
    concurrent_parser.add_argument("file", help="Path to the document")
    concurrent_parser.add_argument("--expected-version", help="Expected version (optional)")
    
    # Add new tool commands
    add_doctor_parser(subparsers)
    add_lint_parser(subparsers)
    add_format_parser(subparsers)
    add_summarize_parser(subparsers)
    add_diff_parser(subparsers)
    
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command-line arguments (if None, uses sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        return 1
    
    try:
        if parsed_args.command == "info":
            return _handle_info(parsed_args)
        elif parsed_args.command == "create":
            return _handle_create(parsed_args)
        elif parsed_args.command == "collection":
            return _handle_collection(parsed_args)
        elif parsed_args.command == "dev":
            return _handle_dev(parsed_args)
        elif parsed_args.command == "content":
            return _handle_content(parsed_args)
        elif parsed_args.command == "version":
            return _handle_version(parsed_args)
        elif parsed_args.command == "conflicts":
            return _handle_conflicts(parsed_args)
        elif parsed_args.command == "doctor":
            return handle_doctor(parsed_args)
        elif parsed_args.command == "lint":
            return handle_lint(parsed_args)
        elif parsed_args.command == "format":
            return handle_format(parsed_args)
        elif parsed_args.command == "summarize":
            return handle_summarize(parsed_args)
        elif parsed_args.command == "diff":
            return handle_diff(parsed_args)
        else:
            print(f"Unknown command: {parsed_args.command}")
            return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _handle_info(args):
    """Handle the info command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Load the document
        doc = Document.from_file(file_path)
        
        if args.json:
            # Output as JSON
            info = {
                "title": doc.title,
                "author": doc.author,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
                "path": str(doc.path),
                "tags": doc.tags,
                "metadata": doc.metadata
            }
            print(json.dumps(info, indent=2))
        else:
            # Output as text
            print(f"Title: {doc.title}")
            if doc.author:
                print(f"Author: {doc.author}")
            if doc.created_at:
                print(f"Created: {doc.created_at}")
            if doc.updated_at:
                print(f"Updated: {doc.updated_at}")
            if doc.tags:
                print(f"Tags: {', '.join(doc.tags)}")
            
            # Display metadata count
            meta_count = len(doc.metadata)
            print(f"Metadata: {meta_count} fields")
            
            # Display content stats
            content_lines = doc.content.count("\n") + 1
            content_words = len(doc.content.split())
            print(f"Content: {content_lines} lines, {content_words} words")
        
        return 0
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        return 1


def _handle_create(args):
    """Handle the create command."""
    # Parse tags
    tag_list = None
    if args.tags:
        tag_list = [tag.strip() for tag in args.tags.split(",")]
    
    # Get content
    content = ""
    if args.content == "-":
        # Read from stdin
        content = sys.stdin.read()
    elif args.content:
        content = args.content
    elif args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()
    
    try:
        # Create document
        doc = Document.create(
            title=args.title,
            content=content,
            author=args.author,
            tags=tag_list
        )
        
        # Save document
        doc.save(args.output)
        print(f"Document created: {args.output}")
        return 0
    except Exception as e:
        print(f"Error creating document: {e}", file=sys.stderr)
        return 1


def _handle_collection(args):
    """Handle the collection command."""
    if not args.collection_command:
        print("Error: A collection command is required", file=sys.stderr)
        return 1
    
    if args.collection_command == "create":
        return _handle_collection_create(args)
    elif args.collection_command == "list":
        return _handle_collection_list(args)
    else:
        print(f"Unknown collection command: {args.collection_command}", file=sys.stderr)
        return 1


def _handle_collection_create(args):
    """Handle the collection create command."""
    dir_path = Path(args.directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"Error: Directory not found: {dir_path}", file=sys.stderr)
        return 1
    
    try:
        # Create collection
        collection = Collection(args.name)
        
        # Find MDP files
        mdp_files = find_mdp_files(dir_path, recursive=args.recursive)
        
        # Add documents to collection
        for file_path in mdp_files:
            try:
                doc = Document.from_file(file_path)
                collection.add_document(doc)
            except Exception as e:
                print(f"Warning: Could not add {file_path}: {e}", file=sys.stderr)
        
        # Save collection
        collection.save(args.output)
        print(f"Created collection '{args.name}' with {len(collection.documents)} documents: {args.output}")
        return 0
    except Exception as e:
        print(f"Error creating collection: {e}", file=sys.stderr)
        return 1


def _handle_collection_list(args):
    """Handle the collection list command."""
    collection_path = Path(args.collection)
    
    if not collection_path.exists():
        print(f"Error: Collection file not found: {collection_path}", file=sys.stderr)
        return 1
    
    try:
        # Load collection
        collection = Collection.load(args.collection)
        
        if args.json:
            # Output as JSON
            doc_list = [
                {
                    "title": doc.title,
                    "uuid": doc.metadata.get("uuid"),
                    "position": doc.metadata.get("position"),
                    "path": str(doc.path) if doc.path else None
                }
                for doc in collection.documents
            ]
            print(json.dumps(doc_list, indent=2))
        else:
            # Output as text
            print(f"Collection: {collection.name}")
            print(f"Documents: {len(collection.documents)}")
            print()
            
            for doc in collection.documents:
                title = doc.title
                pos = doc.metadata.get("position", "")
                pos_str = f" ({pos})" if pos else ""
                path_str = f" - {doc.path}" if doc.path else ""
                print(f"- {title}{pos_str}{path_str}")
        
        return 0
    except Exception as e:
        print(f"Error listing collection: {e}", file=sys.stderr)
        return 1


def _handle_dev(args):
    """Handle the dev command."""
    if args.metadata_schema:
        from .metadata import get_standard_fields
        schema = get_standard_fields()
        print(json.dumps(schema, indent=2))
        return 0
    
    if args.validate:
        file_path = Path(args.validate)
        
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return 1
        
        try:
            # Just loading the document will validate it
            Document.from_file(file_path)
            print(f"Valid MDP file: {file_path}")
            return 0
        except Exception as e:
            print(f"Invalid MDP file: {file_path}", file=sys.stderr)
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    print("No dev command specified. Use --metadata-schema or --validate.", file=sys.stderr)
    return 1


def _handle_content(args):
    """Handle the content command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Load the document
        doc = Document.from_file(file_path)
        
        if args.metadata_only:
            # Extract only metadata
            print(json.dumps(doc.metadata, indent=2))
        elif args.content_only:
            # Extract only content
            print(doc.content)
        else:
            # Extract both
            print("=== METADATA ===")
            print(json.dumps(doc.metadata, indent=2))
            print("\n=== CONTENT ===")
            print(doc.content)
        
        return 0
    except Exception as e:
        print(f"Error extracting content: {e}", file=sys.stderr)
        return 1


def _handle_version(args):
    """Handle versioning commands."""
    if not args.version_command:
        print("Error: A version command is required", file=sys.stderr)
        return 1
    
    if args.version_command == "create":
        return _handle_version_create(args)
    elif args.version_command == "list":
        return _handle_version_list(args)
    elif args.version_command == "show":
        return _handle_version_show(args)
    elif args.version_command == "compare":
        return _handle_version_compare(args)
    elif args.version_command == "rollback":
        return _handle_version_rollback(args)
    elif args.version_command == "branch":
        return _handle_version_branch(args)
    elif args.version_command == "merge":
        return _handle_version_merge(args)
    else:
        print(f"Unknown version command: {args.version_command}", file=sys.stderr)
        return 1


def _handle_version_create(args):
    """Handle the version create command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Get version manager
        vm = get_version_manager(file_path)
        
        # Determine version
        version = args.version
        if not version:
            # Read the document to get current version
            doc = Document.from_file(file_path)
            current_version = doc.metadata.get("version", "0.0.0")
            
            # Use the next version based on bump type
            from .metadata import is_semantic_version, next_version
            if not is_semantic_version(current_version):
                version = "0.1.0"  # Start at 0.1.0 if current version isn't semantic
            else:
                version = next_version(current_version, args.bump)
        
        # Create version
        version_path = vm.create_version(
            document_path=file_path,
            version=version,
            author=args.author,
            description=args.description
        )
        
        print(f"Created version {version}: {version_path}")
        return 0
    except Exception as e:
        print(f"Error creating version: {e}", file=sys.stderr)
        return 1


def _handle_version_list(args):
    """Handle the version list command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Get version manager
        vm = get_version_manager(file_path)
        
        # Get versions
        versions = vm.list_versions(file_path)
        
        if args.json:
            # Output as JSON
            print(json.dumps(versions, indent=2))
        else:
            # Output as text
            if not versions:
                print(f"No versions found for {file_path.name}")
                return 0
            
            print(f"Versions for {file_path.name}:")
            for v in versions:
                version = v.get("version", "Unknown")
                date = v.get("date", "Unknown date")
                author = v.get("author", "Unknown author")
                desc = v.get("description", "")
                
                print(f"  {version} ({date}) - {author}")
                if desc:
                    print(f"    {desc}")
        
        return 0
    except Exception as e:
        print(f"Error listing versions: {e}", file=sys.stderr)
        return 1


def _handle_version_show(args):
    """Handle the version show command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Get version manager
        vm = get_version_manager(file_path)
        
        # Get the requested version
        version_file = vm.get_version(file_path, args.version)
        
        # Convert to document
        doc = Document(
            metadata=version_file.metadata, 
            content=version_file.content,
            path=version_file.path
        )
        
        if args.metadata_only:
            # Show only metadata
            print(json.dumps(doc.metadata, indent=2))
        elif args.content_only:
            # Show only content
            print(doc.content)
        else:
            # Show document info and summary
            print(f"Version: {args.version}")
            print(f"Title: {doc.title}")
            if doc.author:
                print(f"Author: {doc.author}")
            if doc.metadata.get("created_at"):
                print(f"Created: {doc.metadata['created_at']}")
            if doc.metadata.get("updated_at"):
                print(f"Updated: {doc.metadata['updated_at']}")
            
            print("\nContent Preview:")
            content_lines = doc.content.splitlines()
            preview_lines = min(10, len(content_lines))
            for i in range(preview_lines):
                print(f"  {content_lines[i]}")
            
            if len(content_lines) > preview_lines:
                print(f"  ... ({len(content_lines) - preview_lines} more lines)")
        
        return 0
    except Exception as e:
        print(f"Error showing version: {e}", file=sys.stderr)
        return 1


def _handle_version_compare(args):
    """Handle the version compare command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Get version manager
        vm = get_version_manager(file_path)
        
        # Compare versions
        diff = vm.compare_versions(file_path, args.version1, args.version2)
        
        if args.json:
            # Output as JSON
            print(json.dumps(diff, indent=2))
        else:
            # Output as text
            print(f"Comparing {args.version1} to {args.version2} for {file_path.name}:")
            
            # Metadata differences
            metadata_diff = diff["metadata_diff"]
            
            if metadata_diff["added"]:
                print("\nFields added in newer version:")
                for key, value in metadata_diff["added"].items():
                    print(f"  + {key}: {value}")
            
            if metadata_diff["removed"]:
                print("\nFields removed in newer version:")
                for key, value in metadata_diff["removed"].items():
                    print(f"  - {key}: {value}")
            
            if metadata_diff["changed"]:
                print("\nFields changed in newer version:")
                for key, value in metadata_diff["changed"].items():
                    print(f"  ~ {key}: {value['old']} -> {value['new']}")
            
            # Content differences
            print("\nContent differences:")
            content_diff = diff["content_diff"]
            line_num = 0
            for entry in content_diff:
                if entry["op"] == "add":
                    print(f"  + {entry['text']}")
                elif entry["op"] == "remove":
                    print(f"  - {entry['text']}")
                else:
                    # Only show a few context lines
                    if line_num % 20 == 0:
                        print(f"  {entry['text']}")
                line_num += 1
            
            print(f"\nTotal changes: {len([d for d in content_diff if d['op'] != 'unchanged'])} lines")
        
        return 0
    except Exception as e:
        print(f"Error comparing versions: {e}", file=sys.stderr)
        return 1


def _handle_version_rollback(args):
    """Handle the version rollback command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Get version manager
        vm = get_version_manager(file_path)
        
        # Perform rollback
        create_backup = not args.no_backup
        updated_path = vm.rollback_to_version(file_path, args.version, create_backup)
        
        print(f"Successfully rolled back {file_path.name} to version {args.version}")
        if create_backup:
            print("A backup of the previous state was created")
        
        return 0
    except Exception as e:
        print(f"Error rolling back: {e}", file=sys.stderr)
        return 1


def _handle_version_branch(args):
    """Handle the version branch command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Get version manager
        vm = get_version_manager(file_path)
        
        # Create branch
        branch_path = vm.create_branch(file_path, args.name, args.base_version)
        
        print(f"Created branch '{args.name}' at: {branch_path}")
        if args.base_version:
            print(f"Based on version: {args.base_version}")
        else:
            print("Based on current document")
        
        return 0
    except Exception as e:
        print(f"Error creating branch: {e}", file=sys.stderr)
        return 1


def _handle_version_merge(args):
    """Handle the version merge command."""
    branch_path = Path(args.branch)
    target_path = Path(args.target)
    
    if not branch_path.exists():
        print(f"Error: Branch file not found: {branch_path}", file=sys.stderr)
        return 1
    
    if not target_path.exists():
        print(f"Error: Target file not found: {target_path}", file=sys.stderr)
        return 1
    
    try:
        # Get version manager
        vm = get_version_manager(target_path)
        
        # Perform merge
        create_backup = not args.no_backup
        merged_path = vm.merge_branch(branch_path, target_path, create_backup)
        
        print(f"Successfully merged {branch_path.name} into {target_path.name}")
        if create_backup:
            print("A backup of the target document was created")
        
        return 0
    except Exception as e:
        print(f"Error merging branch: {e}", file=sys.stderr)
        return 1


def _handle_conflicts(args):
    """Handle conflict resolution commands."""
    if not args.conflict_command:
        print("Error: A conflict command is required", file=sys.stderr)
        return 1
    
    if args.conflict_command == "check":
        return _handle_conflict_check(args)
    elif args.conflict_command == "merge":
        return _handle_conflict_merge(args)
    elif args.conflict_command == "create-resolution-file":
        return _handle_conflict_resolution_file(args)
    elif args.conflict_command == "apply-resolution":
        return _handle_conflict_apply_resolution(args)
    elif args.conflict_command == "check-concurrent":
        return _handle_conflict_concurrent(args)
    else:
        print(f"Unknown conflict command: {args.conflict_command}", file=sys.stderr)
        return 1


def _handle_conflict_check(args):
    """Handle the conflict check command."""
    local_path = Path(args.local)
    remote_path = Path(args.remote)
    
    if not local_path.exists():
        print(f"Error: Local file not found: {local_path}", file=sys.stderr)
        return 1
    
    if not remote_path.exists():
        print(f"Error: Remote file not found: {remote_path}", file=sys.stderr)
        return 1
    
    try:
        # Load documents
        local_doc = Document.from_file(local_path)
        remote_doc = Document.from_file(remote_path)
        
        # Check for conflicts
        has_conflicts, conflict_summary = local_doc.check_for_conflicts(remote_doc)
        
        if args.json:
            # Output as JSON
            if conflict_summary:
                print(json.dumps(conflict_summary, indent=2))
            else:
                print(json.dumps({"has_conflicts": has_conflicts}, indent=2))
        else:
            if has_conflicts:
                print(f"Conflicts detected between {local_path.name} and {remote_path.name}")
                
                if conflict_summary:
                    # Print metadata conflicts
                    if conflict_summary.get("metadata_conflicts"):
                        print("\nMetadata conflicts:")
                        for field, values in conflict_summary["metadata_conflicts"].items():
                            print(f"  Field: {field}")
                            print(f"    Local value: {values['local']}")
                            print(f"    Remote value: {values['remote']}")
                            print(f"    Base value: {values['base']}")
                    
                    # Print content conflicts
                    if conflict_summary.get("content_conflicts"):
                        print(f"\nContent conflicts: {len(conflict_summary['content_conflicts'])}")
                        for i, conflict in enumerate(conflict_summary["content_conflicts"]):
                            print(f"\n  Conflict {i+1}:")
                            print(f"    Region: {conflict['region']}")
                            print(f"    Local: {conflict['local'][:50]}..." if len(conflict['local']) > 50 else f"    Local: {conflict['local']}")
                            print(f"    Remote: {conflict['remote'][:50]}..." if len(conflict['remote']) > 50 else f"    Remote: {conflict['remote']}")
            else:
                print(f"No conflicts detected between {local_path.name} and {remote_path.name}")
        
        return 0
    except Exception as e:
        print(f"Error checking for conflicts: {e}", file=sys.stderr)
        return 1


def _handle_conflict_merge(args):
    """Handle the conflict merge command."""
    local_path = Path(args.local)
    remote_path = Path(args.remote)
    
    if not local_path.exists():
        print(f"Error: Local file not found: {local_path}", file=sys.stderr)
        return 1
    
    if not remote_path.exists():
        print(f"Error: Remote file not found: {remote_path}", file=sys.stderr)
        return 1
    
    try:
        # Load documents
        local_doc = Document.from_file(local_path)
        remote_doc = Document.from_file(remote_path)
        
        # Determine output path
        output_path = args.output if args.output else local_path
        
        # Try to auto-merge
        from .conflict import ConflictError
        try:
            merged_doc = local_doc.auto_merge(remote_doc, output_path)
            print(f"Successfully merged documents to {output_path}")
            return 0
        except ConflictError as e:
            print(f"Cannot auto-merge: {e}", file=sys.stderr)
            print("Use 'mdp conflicts create-resolution-file' to create a file for manual resolution", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error merging documents: {e}", file=sys.stderr)
        return 1


def _handle_conflict_resolution_file(args):
    """Handle creating a conflict resolution file."""
    local_path = Path(args.local)
    remote_path = Path(args.remote)
    output_path = Path(args.output)
    
    if not local_path.exists():
        print(f"Error: Local file not found: {local_path}", file=sys.stderr)
        return 1
    
    if not remote_path.exists():
        print(f"Error: Remote file not found: {remote_path}", file=sys.stderr)
        return 1
    
    try:
        # Load documents
        local_doc = Document.from_file(local_path)
        remote_doc = Document.from_file(remote_path)
        
        # Create conflict resolution file
        resolution_path = local_doc.create_conflict_resolution_file(remote_doc, output_path)
        
        print(f"Created conflict resolution file: {resolution_path}")
        print("Edit this file to resolve conflicts, then use 'mdp conflicts apply-resolution' to apply the changes")
        return 0
    except Exception as e:
        print(f"Error creating conflict resolution file: {e}", file=sys.stderr)
        return 1


def _handle_conflict_apply_resolution(args):
    """Handle applying a resolved conflict file."""
    resolution_path = Path(args.resolution_file)
    output_path = Path(args.output)
    
    if not resolution_path.exists():
        print(f"Error: Resolution file not found: {resolution_path}", file=sys.stderr)
        return 1
    
    try:
        # Apply resolution
        from .conflict import ConflictError
        try:
            resolved_doc = Document.resolve_from_conflict_file(resolution_path, output_path)
            print(f"Successfully applied conflict resolution to {output_path}")
            return 0
        except ConflictError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("Make sure all conflicts are resolved in the resolution file", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error applying conflict resolution: {e}", file=sys.stderr)
        return 1


def _handle_conflict_concurrent(args):
    """Handle checking for concurrent modifications."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Load document
        doc = Document.from_file(file_path)
        
        # Check for concurrent modifications
        has_modifications = doc.detect_concurrent_modification(args.expected_version)
        
        if has_modifications:
            print(f"Document {file_path.name} has been modified concurrently")
            print(f"Expected version: {args.expected_version or doc.version}")
            print(f"Latest version: {doc.metadata.get('latest_version', doc.version)}")
        else:
            print(f"Document {file_path.name} has not been modified concurrently")
            print(f"Version: {doc.version}")
        
        return 0
    except Exception as e:
        print(f"Error checking for concurrent modifications: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 