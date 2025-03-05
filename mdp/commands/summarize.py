"""
CLI commands for summarizing MDP files.

The summarize tool extracts key information from MDP files and collections,
generating concise reports on content, metadata, relationships, and other
aspects of the documents.
"""

import os
import sys
import json
import yaml
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import Counter, defaultdict

from ..core import MDPFile, read_mdp
from ..document import Document


def add_summarize_parser(subparsers):
    """
    Add the summarize command to the CLI.
    
    Args:
        subparsers: Subparsers object from the main parser
    """
    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Generate summaries of MDP files and collections"
    )
    
    # File/directory to summarize
    summarize_parser.add_argument(
        "target",
        help="File or directory to summarize"
    )
    
    # General options
    summarize_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively summarize directories"
    )
    
    # Type of summary
    summarize_parser.add_argument(
        "--type",
        choices=["metadata", "content", "relationships", "full", "statistics"],
        default="full",
        help="Type of summary to generate"
    )
    
    # Output options
    summarize_parser.add_argument(
        "--format",
        choices=["text", "json", "yaml", "csv"],
        default="text",
        help="Output format"
    )
    
    summarize_parser.add_argument(
        "--output", "-o",
        help="Output file for summary (default: stdout)"
    )
    
    # Filtering options
    summarize_parser.add_argument(
        "--filter-tag",
        action="append",
        dest="filter_tags",
        help="Only include documents with specified tag(s)"
    )
    
    summarize_parser.add_argument(
        "--filter-author",
        action="append",
        dest="filter_authors",
        help="Only include documents with specified author(s)"
    )
    
    summarize_parser.add_argument(
        "--modified-after",
        help="Only include documents modified after specified date (YYYY-MM-DD)"
    )
    
    summarize_parser.add_argument(
        "--modified-before",
        help="Only include documents modified before specified date (YYYY-MM-DD)"
    )
    
    # Additional options
    summarize_parser.add_argument(
        "--content-preview-length",
        type=int,
        default=200,
        help="Length of content preview in characters"
    )
    
    summarize_parser.add_argument(
        "--sort-by",
        choices=["title", "author", "date", "file"],
        default="title",
        help="Sort documents by specified field"
    )


def handle_summarize(args):
    """
    Handle the summarize command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    target = Path(args.target)
    
    # Check if target exists
    if not target.exists():
        print(f"Error: Target not found: {target}", file=sys.stderr)
        return 1
    
    # Find MDP files to summarize
    files_to_summarize = []
    
    if target.is_file():
        if not target.name.endswith('.mdp'):
            print(f"Error: {target} is not an MDP file", file=sys.stderr)
            return 1
        files_to_summarize.append(target)
    else:  # Directory
        if args.recursive:
            files_to_summarize = list(target.rglob("*.mdp"))
        else:
            files_to_summarize = list(target.glob("*.mdp"))
    
    if not files_to_summarize:
        print("No MDP files found to summarize.")
        return 0
    
    # Read all files and filter according to options
    mdp_files = []
    error_count = 0
    
    for file_path in files_to_summarize:
        try:
            mdp_file = read_mdp(file_path)
            # Apply filters
            if should_include_file(mdp_file, file_path, args):
                mdp_files.append((file_path, mdp_file))
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            error_count += 1
    
    if not mdp_files:
        print("No MDP files match the specified filters.")
        return 0
    
    # Sort files according to option
    sort_files(mdp_files, args.sort_by)
    
    # Generate summary
    summary = generate_summary(mdp_files, args)
    
    # Output summary
    output_summary(summary, args)
    
    if error_count > 0:
        print(f"Encountered errors in {error_count} files.", file=sys.stderr)
        return 1
    
    return 0


def should_include_file(mdp_file: MDPFile, file_path: Path, args) -> bool:
    """
    Check if a file should be included based on filter options.
    
    Args:
        mdp_file: MDPFile to check
        file_path: Path to the file
        args: Parsed command-line arguments
        
    Returns:
        True if the file should be included, False otherwise
    """
    metadata = mdp_file.metadata
    
    # Check tag filters
    if args.filter_tags:
        file_tags = metadata.get("tags", [])
        if not any(tag in file_tags for tag in args.filter_tags):
            return False
    
    # Check author filters
    if args.filter_authors:
        file_author = metadata.get("author", "")
        if file_author not in args.filter_authors:
            return False
    
    # Check date filters
    if args.modified_after or args.modified_before:
        updated_at = metadata.get("updated_at")
        
        if not updated_at:
            # If no updated_at, check created_at
            updated_at = metadata.get("created_at")
        
        if not updated_at:
            # If neither date is available, exclude file if date filtering is requested
            return False
        
        # Parse date
        try:
            if isinstance(updated_at, str):
                file_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            elif isinstance(updated_at, datetime):
                file_date = updated_at
            else:
                return False
            
            # Check modified after
            if args.modified_after:
                filter_date = datetime.fromisoformat(args.modified_after)
                if file_date < filter_date:
                    return False
            
            # Check modified before
            if args.modified_before:
                filter_date = datetime.fromisoformat(args.modified_before)
                if file_date > filter_date:
                    return False
        
        except ValueError:
            # If date parsing fails, exclude file
            return False
    
    return True


def sort_files(mdp_files: List[Tuple[Path, MDPFile]], sort_by: str):
    """
    Sort files according to specified field.
    
    Args:
        mdp_files: List of (file_path, mdp_file) tuples to sort
        sort_by: Field to sort by (title, author, date, file)
    """
    if sort_by == "title":
        mdp_files.sort(key=lambda x: x[1].metadata.get("title", "").lower())
    
    elif sort_by == "author":
        mdp_files.sort(key=lambda x: x[1].metadata.get("author", "").lower())
    
    elif sort_by == "date":
        def get_date(mdp_file):
            updated_at = mdp_file.metadata.get("updated_at")
            if not updated_at:
                updated_at = mdp_file.metadata.get("created_at")
            
            if not updated_at:
                return datetime.min
            
            try:
                if isinstance(updated_at, str):
                    return datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                elif isinstance(updated_at, datetime):
                    return updated_at
                else:
                    return datetime.min
            except ValueError:
                return datetime.min
        
        mdp_files.sort(key=lambda x: get_date(x[1]))
    
    elif sort_by == "file":
        mdp_files.sort(key=lambda x: str(x[0]))


def generate_summary(mdp_files: List[Tuple[Path, MDPFile]], args) -> Dict[str, Any]:
    """
    Generate summary of MDP files.
    
    Args:
        mdp_files: List of (file_path, mdp_file) tuples to summarize
        args: Parsed command-line arguments
        
    Returns:
        Dictionary containing summary information
    """
    summary_type = args.type
    content_preview_length = args.content_preview_length
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "file_count": len(mdp_files),
        "files": []
    }
    
    # Generate specific summary according to type
    if summary_type == "metadata" or summary_type == "full":
        # Gather metadata
        for file_path, mdp_file in mdp_files:
            file_summary = {
                "path": str(file_path),
                "metadata": mdp_file.metadata
            }
            summary["files"].append(file_summary)
    
    elif summary_type == "content":
        # Gather content previews
        for file_path, mdp_file in mdp_files:
            content_preview = mdp_file.content[:content_preview_length]
            if len(mdp_file.content) > content_preview_length:
                content_preview += "..."
            
            file_summary = {
                "path": str(file_path),
                "title": mdp_file.metadata.get("title", ""),
                "content_preview": content_preview,
                "content_length": len(mdp_file.content)
            }
            summary["files"].append(file_summary)
    
    elif summary_type == "relationships":
        # Gather relationship information
        relationship_map = {}
        
        for file_path, mdp_file in mdp_files:
            file_id = mdp_file.metadata.get("uuid", str(file_path))
            relationships = mdp_file.metadata.get("relationships", [])
            
            outgoing_rels = []
            for rel in relationships:
                if isinstance(rel, dict):
                    outgoing_rels.append(rel)
            
            relationship_map[file_id] = {
                "path": str(file_path),
                "title": mdp_file.metadata.get("title", ""),
                "outgoing_relationships": outgoing_rels,
                "incoming_relationships": []
            }
        
        # Find incoming relationships
        for file_id, rel_info in relationship_map.items():
            for rel in rel_info["outgoing_relationships"]:
                if "id" in rel and rel["id"] in relationship_map:
                    target_id = rel["id"]
                    incoming_rel = {
                        "type": rel.get("type", ""),
                        "from_id": file_id,
                        "from_title": rel_info["title"],
                        "from_path": rel_info["path"]
                    }
                    relationship_map[target_id]["incoming_relationships"].append(incoming_rel)
        
        # Add to summary
        summary["relationship_map"] = relationship_map
        
        file_summaries = []
        for file_id, rel_info in relationship_map.items():
            file_summary = {
                "path": rel_info["path"],
                "title": rel_info["title"],
                "outgoing_count": len(rel_info["outgoing_relationships"]),
                "incoming_count": len(rel_info["incoming_relationships"]),
                "relationships": {
                    "outgoing": rel_info["outgoing_relationships"],
                    "incoming": rel_info["incoming_relationships"]
                }
            }
            file_summaries.append(file_summary)
        
        summary["files"] = file_summaries
    
    elif summary_type == "statistics":
        # Calculate various statistics
        stats = {
            "total_content_length": 0,
            "avg_content_length": 0,
            "total_word_count": 0,
            "avg_word_count": 0,
            "total_heading_count": 0,
            "avg_heading_count": 0,
            "total_link_count": 0,
            "avg_link_count": 0,
            "tag_frequency": Counter(),
            "author_frequency": Counter(),
            "relationship_type_frequency": Counter(),
            "creation_date_frequency": Counter()
        }
        
        for file_path, mdp_file in mdp_files:
            # Content statistics
            content = mdp_file.content
            stats["total_content_length"] += len(content)
            
            words = re.findall(r'\b\w+\b', content)
            stats["total_word_count"] += len(words)
            
            headings = re.findall(r'^#+\s+.+$', content, re.MULTILINE)
            stats["total_heading_count"] += len(headings)
            
            links = re.findall(r'\[.+?\]\(.+?\)', content)
            stats["total_link_count"] += len(links)
            
            # Metadata statistics
            tags = mdp_file.metadata.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    stats["tag_frequency"][tag] += 1
            
            author = mdp_file.metadata.get("author", "")
            if author:
                stats["author_frequency"][author] += 1
            
            created_at = mdp_file.metadata.get("created_at", "")
            if created_at and isinstance(created_at, str):
                # Extract just the date part (YYYY-MM-DD)
                date_match = re.match(r'(\d{4}-\d{2}-\d{2})', created_at)
                if date_match:
                    stats["creation_date_frequency"][date_match.group(1)] += 1
            
            # Relationship statistics
            relationships = mdp_file.metadata.get("relationships", [])
            if isinstance(relationships, list):
                for rel in relationships:
                    if isinstance(rel, dict) and "type" in rel:
                        stats["relationship_type_frequency"][rel["type"]] += 1
        
        # Calculate averages
        if len(mdp_files) > 0:
            stats["avg_content_length"] = stats["total_content_length"] / len(mdp_files)
            stats["avg_word_count"] = stats["total_word_count"] / len(mdp_files)
            stats["avg_heading_count"] = stats["total_heading_count"] / len(mdp_files)
            stats["avg_link_count"] = stats["total_link_count"] / len(mdp_files)
        
        # Convert counters to dictionaries for JSON serialization
        stats["tag_frequency"] = dict(stats["tag_frequency"])
        stats["author_frequency"] = dict(stats["author_frequency"])
        stats["relationship_type_frequency"] = dict(stats["relationship_type_frequency"])
        stats["creation_date_frequency"] = dict(stats["creation_date_frequency"])
        
        summary["statistics"] = stats
    
    elif summary_type == "full":
        # Include everything
        metadata_summary = generate_summary(mdp_files, type("Args", (), {"type": "metadata"}))
        content_summary = generate_summary(mdp_files, type("Args", (), {
            "type": "content", 
            "content_preview_length": content_preview_length
        }))
        relationship_summary = generate_summary(mdp_files, type("Args", (), {"type": "relationships"}))
        stats_summary = generate_summary(mdp_files, type("Args", (), {"type": "statistics"}))
        
        summary["metadata"] = metadata_summary
        summary["content"] = content_summary
        summary["relationships"] = relationship_summary
        summary["statistics"] = stats_summary["statistics"]
    
    return summary


def output_summary(summary: Dict[str, Any], args):
    """
    Output the summary in the specified format.
    
    Args:
        summary: Summary dictionary
        args: Parsed command-line arguments
    """
    output = None
    
    try:
        # Open output file if specified
        if args.output:
            output = open(args.output, "w")
        else:
            output = sys.stdout
        
        # Format and output summary
        if args.format == "json":
            output_json(summary, output)
        elif args.format == "yaml":
            output_yaml(summary, output)
        elif args.format == "csv":
            output_csv(summary, output)
        else:  # text
            output_text(summary, args.type, output)
    
    finally:
        # Close output file if we opened one
        if output is not None and output != sys.stdout:
            output.close()


def output_json(summary: Dict[str, Any], output=sys.stdout):
    """Output summary in JSON format."""
    json.dump(summary, output, indent=2)


def output_yaml(summary: Dict[str, Any], output=sys.stdout):
    """Output summary in YAML format."""
    yaml.dump(summary, output, sort_keys=False)


def output_csv(summary: Dict[str, Any], output=sys.stdout):
    """
    Output summary in CSV format.
    
    CSV format is only useful for certain summary types.
    """
    writer = csv.writer(output)
    
    # Write header and data based on summary type
    if "files" in summary and summary["files"] and "metadata" in summary["files"][0]:
        # Metadata summary
        header = ["path", "title", "author", "version", "created_at", "updated_at", "tags"]
        writer.writerow(header)
        
        for file_info in summary["files"]:
            metadata = file_info["metadata"]
            row = [
                file_info["path"],
                metadata.get("title", ""),
                metadata.get("author", ""),
                metadata.get("version", ""),
                metadata.get("created_at", ""),
                metadata.get("updated_at", ""),
                ", ".join(metadata.get("tags", []))
            ]
            writer.writerow(row)
    
    elif "files" in summary and summary["files"] and "content_preview" in summary["files"][0]:
        # Content summary
        header = ["path", "title", "content_length", "content_preview"]
        writer.writerow(header)
        
        for file_info in summary["files"]:
            row = [
                file_info["path"],
                file_info["title"],
                file_info["content_length"],
                file_info["content_preview"].replace("\n", " ")
            ]
            writer.writerow(row)
    
    elif "files" in summary and summary["files"] and "outgoing_count" in summary["files"][0]:
        # Relationship summary
        header = ["path", "title", "outgoing_count", "incoming_count"]
        writer.writerow(header)
        
        for file_info in summary["files"]:
            row = [
                file_info["path"],
                file_info["title"],
                file_info["outgoing_count"],
                file_info["incoming_count"]
            ]
            writer.writerow(row)
    
    elif "statistics" in summary:
        # Statistics summary - multiple tables
        writer.writerow(["File Statistics"])
        writer.writerow(["Total Files", summary["file_count"]])
        writer.writerow(["Total Content Length", summary["statistics"]["total_content_length"]])
        writer.writerow(["Average Content Length", f"{summary['statistics']['avg_content_length']:.2f}"])
        writer.writerow(["Total Word Count", summary["statistics"]["total_word_count"]])
        writer.writerow(["Average Word Count", f"{summary['statistics']['avg_word_count']:.2f}"])
        writer.writerow(["Total Heading Count", summary["statistics"]["total_heading_count"]])
        writer.writerow(["Average Heading Count", f"{summary['statistics']['avg_heading_count']:.2f}"])
        writer.writerow(["Total Link Count", summary["statistics"]["total_link_count"]])
        writer.writerow(["Average Link Count", f"{summary['statistics']['avg_link_count']:.2f}"])
        
        # Tag frequency
        if summary["statistics"]["tag_frequency"]:
            writer.writerow([])
            writer.writerow(["Tag Frequency"])
            writer.writerow(["Tag", "Count"])
            
            for tag, count in sorted(summary["statistics"]["tag_frequency"].items(), key=lambda x: x[1], reverse=True):
                writer.writerow([tag, count])
        
        # Author frequency
        if summary["statistics"]["author_frequency"]:
            writer.writerow([])
            writer.writerow(["Author Frequency"])
            writer.writerow(["Author", "Count"])
            
            for author, count in sorted(summary["statistics"]["author_frequency"].items(), key=lambda x: x[1], reverse=True):
                writer.writerow([author, count])
        
        # Relationship type frequency
        if summary["statistics"]["relationship_type_frequency"]:
            writer.writerow([])
            writer.writerow(["Relationship Type Frequency"])
            writer.writerow(["Type", "Count"])
            
            for rel_type, count in sorted(summary["statistics"]["relationship_type_frequency"].items(), key=lambda x: x[1], reverse=True):
                writer.writerow([rel_type, count])


def output_text(summary: Dict[str, Any], summary_type: str = "full", output=sys.stdout):
    """
    Output summary in text format.
    
    Args:
        summary: Summary dictionary
        summary_type: Type of summary (default: "full")
        output: Output stream (default: sys.stdout)
    """
    output.write(f"MDP Summary Report\n")
    output.write("=" * 80 + "\n")
    output.write(f"Generated: {summary['generated_at']}\n")
    output.write(f"Files: {summary['file_count']}\n")
    output.write("\n")
    
    if summary_type == "metadata" or summary_type == "full":
        output.write("Metadata Summary\n")
        output.write("-" * 80 + "\n")
        
        for i, file_info in enumerate(summary["files"]):
            if i > 0:
                output.write("\n" + "-" * 40 + "\n")
            
            output.write(f"File: {file_info['path']}\n")
            metadata = file_info["metadata"]
            
            if "title" in metadata:
                output.write(f"Title: {metadata['title']}\n")
            
            if "author" in metadata:
                output.write(f"Author: {metadata['author']}\n")
            
            if "version" in metadata:
                output.write(f"Version: {metadata['version']}\n")
            
            if "created_at" in metadata:
                output.write(f"Created: {metadata['created_at']}\n")
            
            if "updated_at" in metadata:
                output.write(f"Updated: {metadata['updated_at']}\n")
            
            if "tags" in metadata and metadata["tags"]:
                output.write(f"Tags: {', '.join(metadata['tags'])}\n")
            
            if "relationships" in metadata and metadata["relationships"]:
                output.write(f"Relationships: {len(metadata['relationships'])}\n")
    
    elif summary_type == "content":
        output.write("Content Summary\n")
        output.write("-" * 80 + "\n")
        
        for i, file_info in enumerate(summary["files"]):
            if i > 0:
                output.write("\n" + "-" * 40 + "\n")
            
            output.write(f"File: {file_info['path']}\n")
            output.write(f"Title: {file_info['title']}\n")
            output.write(f"Content Length: {file_info['content_length']} characters\n")
            output.write(f"Preview: {file_info['content_preview']}\n")
    
    elif summary_type == "relationships":
        output.write("Relationship Summary\n")
        output.write("-" * 80 + "\n")
        
        for i, file_info in enumerate(summary["files"]):
            if i > 0:
                output.write("\n" + "-" * 40 + "\n")
            
            output.write(f"File: {file_info['path']}\n")
            output.write(f"Title: {file_info['title']}\n")
            output.write(f"Outgoing Relationships: {file_info['outgoing_count']}\n")
            output.write(f"Incoming Relationships: {file_info['incoming_count']}\n")
            
            if file_info["outgoing_count"] > 0:
                output.write("Outgoing:\n")
                for rel in file_info["relationships"]["outgoing"]:
                    rel_type = rel.get("type", "unknown")
                    rel_id = rel.get("id", "")
                    rel_path = rel.get("path", "")
                    rel_identifier = rel_id if rel_id else rel_path
                    output.write(f"  - {rel_type}: {rel_identifier}\n")
            
            if file_info["incoming_count"] > 0:
                output.write("Incoming:\n")
                for rel in file_info["relationships"]["incoming"]:
                    rel_type = rel.get("type", "unknown")
                    from_title = rel.get("from_title", "")
                    from_path = rel.get("from_path", "")
                    output.write(f"  - {rel_type} from: {from_title} ({from_path})\n")
    
    elif summary_type == "statistics":
        output.write("Statistics Summary\n")
        output.write("-" * 80 + "\n")
        
        stats = summary["statistics"]
        
        output.write("Content Statistics:\n")
        output.write(f"  Total Content Length: {stats['total_content_length']} characters\n")
        output.write(f"  Average Content Length: {stats['avg_content_length']:.2f} characters\n")
        output.write(f"  Total Word Count: {stats['total_word_count']} words\n")
        output.write(f"  Average Word Count: {stats['avg_word_count']:.2f} words\n")
        output.write(f"  Total Heading Count: {stats['total_heading_count']} headings\n")
        output.write(f"  Average Heading Count: {stats['avg_heading_count']:.2f} headings\n")
        output.write(f"  Total Link Count: {stats['total_link_count']} links\n")
        output.write(f"  Average Link Count: {stats['avg_link_count']:.2f} links\n")
        
        if stats["tag_frequency"]:
            output.write("\nTop Tags:\n")
            for tag, count in sorted(stats["tag_frequency"].items(), key=lambda x: x[1], reverse=True)[:10]:
                output.write(f"  {tag}: {count}\n")
        
        if stats["author_frequency"]:
            output.write("\nTop Authors:\n")
            for author, count in sorted(stats["author_frequency"].items(), key=lambda x: x[1], reverse=True)[:10]:
                output.write(f"  {author}: {count}\n")
        
        if stats["relationship_type_frequency"]:
            output.write("\nRelationship Types:\n")
            for rel_type, count in sorted(stats["relationship_type_frequency"].items(), key=lambda x: x[1], reverse=True):
                output.write(f"  {rel_type}: {count}\n")
    
    elif summary_type == "full":
        # Full summary is very long, so provide a table of contents
        output.write("Table of Contents:\n")
        output.write("1. Metadata Summary\n")
        output.write("2. Content Summary\n")
        output.write("3. Relationship Summary\n")
        output.write("4. Statistics Summary\n")
        output.write("\n" + "=" * 80 + "\n\n")
        
        # Call output_text for each section
        output.write("1. ")
        output_text({"generated_at": summary["generated_at"], "file_count": summary["file_count"], "files": summary["metadata"]["files"]}, output, "metadata")
        
        output.write("\n" + "=" * 80 + "\n\n")
        output.write("2. ")
        output_text({"generated_at": summary["generated_at"], "file_count": summary["file_count"], "files": summary["content"]["files"]}, output, "content")
        
        output.write("\n" + "=" * 80 + "\n\n")
        output.write("3. ")
        output_text({"generated_at": summary["generated_at"], "file_count": summary["file_count"], "files": summary["relationships"]["files"]}, output, "relationships")
        
        output.write("\n" + "=" * 80 + "\n\n")
        output.write("4. ")
        output_text({"generated_at": summary["generated_at"], "file_count": summary["file_count"], "statistics": summary["statistics"]}, output, "statistics") 