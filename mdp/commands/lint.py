"""
CLI commands for the MDP-Lint tool.

This module provides the CLI interface for linting MDP files.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..lint import MDPLinter, LintResult, LintSeverity, load_custom_rules


def add_lint_parser(subparsers):
    """
    Add the lint command to the CLI.
    
    Args:
        subparsers: Subparsers object from the main parser
    """
    lint_parser = subparsers.add_parser(
        "lint",
        help="Lint MDP files for issues"
    )
    
    # File/directory to lint
    lint_parser.add_argument(
        "target",
        help="File or directory to lint"
    )
    
    # General options
    lint_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively lint directories"
    )
    
    lint_parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix fixable issues"
    )
    
    lint_parser.add_argument(
        "--config",
        help="Path to lint configuration file (JSON/YAML)"
    )
    
    # Output options
    lint_parser.add_argument(
        "--format",
        choices=["text", "json", "summary"],
        default="text",
        help="Output format"
    )
    
    lint_parser.add_argument(
        "--output", "-o",
        help="Output file for results (default: stdout)"
    )
    
    # Filter options
    lint_parser.add_argument(
        "--severity",
        choices=["error", "warning", "info"],
        help="Minimum severity level to report"
    )
    
    lint_parser.add_argument(
        "--category",
        choices=["metadata", "content", "relationship"],
        help="Only check rules in this category"
    )
    
    lint_parser.add_argument(
        "--include-rule",
        action="append",
        dest="include_rules",
        metavar="RULE_ID",
        help="Include only these rules (can be specified multiple times)"
    )
    
    lint_parser.add_argument(
        "--exclude-rule",
        action="append",
        dest="exclude_rules",
        metavar="RULE_ID",
        help="Exclude these rules (can be specified multiple times)"
    )


def handle_lint(args):
    """
    Handle the lint command.
    
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
    
    # Create linter with configuration
    linter = create_linter(args)
    
    # Perform linting
    results = perform_lint(linter, target, args)
    
    # Handle output
    output_results(results, args)
    
    # Return exit code based on results
    for result in results.values():
        if result.has_errors:
            return 1
    
    return 0


def create_linter(args) -> MDPLinter:
    """
    Create a linter based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Configured MDPLinter instance
    """
    # Create base linter
    linter = MDPLinter()
    
    # Load custom rules if config file provided
    if args.config:
        try:
            custom_rules = load_custom_rules(args.config)
            linter = MDPLinter(custom_rules)
        except (FileNotFoundError, ValueError) as e:
            print(f"Warning: {e}", file=sys.stderr)
            print("Using default rules instead.", file=sys.stderr)
    
    # Filter rules based on category
    if args.category:
        linter.rules = linter.get_rules_by_category(args.category)
    
    # Filter rules based on include/exclude lists
    if args.include_rules:
        rule_ids = set(args.include_rules)
        linter.rules = [rule for rule in linter.rules if rule.id in rule_ids]
    
    if args.exclude_rules:
        rule_ids = set(args.exclude_rules)
        linter.rules = [rule for rule in linter.rules if rule.id not in rule_ids]
    
    return linter


def perform_lint(linter: MDPLinter, target: Path, args) -> Dict[Path, LintResult]:
    """
    Perform linting on target file or directory.
    
    Args:
        linter: Configured linter
        target: Target file or directory
        args: Parsed command-line arguments
        
    Returns:
        Dictionary mapping file paths to LintResults
    """
    results = {}
    
    if target.is_file():
        # Lint a single file
        result = linter.lint_file(target)
        results[target] = result
        
        # Apply fixes if requested
        if args.fix and result.get_fixable_errors():
            try:
                fixed_file, applied_fixes = linter.fix_file(target)
                
                # Save the fixed file
                fixed_file.save()
                
                # Update result to remove fixed errors
                fixed_error_ids = {error.rule_id for error in applied_fixes}
                result.errors = [error for error in result.errors 
                                if error.rule_id not in fixed_error_ids]
                
                print(f"Applied {len(applied_fixes)} fixes to {target}")
            except Exception as e:
                print(f"Error applying fixes to {target}: {e}", file=sys.stderr)
    
    elif target.is_dir():
        # Lint a directory
        results = linter.lint_directory(target, recursive=args.recursive)
        
        # Apply fixes if requested
        if args.fix:
            for file_path, result in results.items():
                if result.get_fixable_errors():
                    try:
                        fixed_file, applied_fixes = linter.fix_file(file_path)
                        
                        # Save the fixed file
                        fixed_file.save()
                        
                        # Update result to remove fixed errors
                        fixed_error_ids = {error.rule_id for error in applied_fixes}
                        result.errors = [error for error in result.errors 
                                        if error.rule_id not in fixed_error_ids]
                        
                        print(f"Applied {len(applied_fixes)} fixes to {file_path}")
                    except Exception as e:
                        print(f"Error applying fixes to {file_path}: {e}", file=sys.stderr)
    
    # Filter results by severity if requested
    if args.severity:
        severity_level = LintSeverity(args.severity)
        severity_levels = {
            LintSeverity.ERROR: 0,
            LintSeverity.WARNING: 1,
            LintSeverity.INFO: 2
        }
        threshold = severity_levels[severity_level]
        
        for path, result in results.items():
            result.errors = [
                error for error in result.errors
                if severity_levels[error.severity] <= threshold
            ]
    
    return results


def output_results(results: Dict[Path, LintResult], args):
    """
    Output linting results.
    
    Args:
        results: Dictionary mapping file paths to LintResults
        args: Parsed command-line arguments
    """
    output = None
    
    try:
        # Open output file if specified
        if args.output:
            output = open(args.output, "w")
        else:
            output = sys.stdout
        
        # Format and output results
        if args.format == "json":
            output_json(results, output)
        elif args.format == "summary":
            output_summary(results, output)
        else:  # text
            output_text(results, output)
    
    finally:
        # Close output file if we opened one
        if output is not None and output != sys.stdout:
            output.close()


def output_text(results: Dict[Path, LintResult], output=sys.stdout):
    """Output results in text format."""
    for path, result in results.items():
        output.write(f"{str(result)}\n")


def output_json(results: Dict[Path, LintResult], output=sys.stdout):
    """Output results in JSON format."""
    json_results = {str(path): result.to_dict() for path, result in results.items()}
    json.dump(json_results, output, indent=2)


def output_summary(results: Dict[Path, LintResult], output=sys.stdout):
    """Output a summary of results."""
    total_errors = sum(result.error_count for result in results.values())
    total_warnings = sum(result.warning_count for result in results.values())
    total_info = sum(result.info_count for result in results.values())
    file_count = len(results)
    error_files = sum(1 for result in results.values() if result.error_count > 0)
    
    output.write(f"Linted {file_count} files\n")
    output.write(f"Found {total_errors} errors, {total_warnings} warnings, {total_info} info\n")
    output.write(f"{error_files} files have errors\n")
    
    if total_errors > 0:
        output.write("\nFiles with errors:\n")
        for path, result in results.items():
            if result.error_count > 0:
                output.write(f"  {path}: {result.error_count} errors\n")
    
    # Count errors by rule
    rule_counts = {}
    for result in results.values():
        for error in result.errors:
            rule_counts[error.rule_id] = rule_counts.get(error.rule_id, 0) + 1
    
    if rule_counts:
        output.write("\nMost common issues:\n")
        for rule_id, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True):
            output.write(f"  {rule_id}: {count} occurrences\n") 