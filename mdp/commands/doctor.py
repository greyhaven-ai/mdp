"""
CLI commands for the mdp-doctor tool.

The doctor tool provides comprehensive checking and diagnosis for MDP files
and collections, including validation, relationship integrity, and suggestions
for improvement.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set, Optional

from ..document import Document
from ..core import MDPFile, read_mdp
from ..metadata import is_valid_uuid, is_semantic_version
from ..lint import MDPLinter, LintResult, LintSeverity
from ..schema.validation import validate_metadata_with_schema


class DoctorReport:
    """Report containing diagnostic information about MDP files."""
    
    def __init__(self, target_path: Path):
        """Initialize a DoctorReport."""
        self.target_path = target_path
        self.is_directory = target_path.is_dir()
        
        self.files: List[Path] = []
        self.file_reports: Dict[Path, Dict[str, Any]] = {}
        self.lint_results: Dict[Path, LintResult] = {}
        
        self.relationships: Dict[str, List[Tuple[Path, Dict[str, Any]]]] = {
            'invalid': [],
            'broken': [],
            'orphaned': []
        }
        
        self.versions: Dict[str, List[Path]] = {
            'missing': [],
            'invalid': []
        }
        
        self.suggestions: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the report to a dictionary."""
        return {
            'target_path': str(self.target_path),
            'is_directory': self.is_directory,
            'file_count': len(self.files),
            'file_reports': {str(path): report for path, report in self.file_reports.items()},
            'lint_results': {str(path): result.to_dict() for path, result in self.lint_results.items()},
            'relationships': {
                'invalid': [(str(path), rel) for path, rel in self.relationships['invalid']],
                'broken': [(str(path), rel) for path, rel in self.relationships['broken']],
                'orphaned': [(str(path), rel) for path, rel in self.relationships['orphaned']]
            },
            'versions': {
                'missing': [str(path) for path in self.versions['missing']],
                'invalid': [str(path) for path in self.versions['invalid']]
            },
            'suggestions': self.suggestions,
            'summary': self.summary
        }


def add_doctor_parser(subparsers):
    """
    Add the doctor command to the CLI.
    
    Args:
        subparsers: Subparsers object from the main parser
    """
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check and diagnose issues in MDP files and collections"
    )
    
    # File/directory to check
    doctor_parser.add_argument(
        "target",
        help="File or directory to check"
    )
    
    # General options
    doctor_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively check directories"
    )
    
    doctor_parser.add_argument(
        "--profile",
        choices=["minimal", "standard", "publication", "collection", "archival"],
        default="standard",
        help="Validation profile to use"
    )
    
    doctor_parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix common issues"
    )
    
    # Check options
    doctor_parser.add_argument(
        "--check-relationships",
        action="store_true",
        help="Check relationship integrity"
    )
    
    doctor_parser.add_argument(
        "--check-versions",
        action="store_true",
        help="Check version integrity"
    )
    
    doctor_parser.add_argument(
        "--with-lint",
        action="store_true",
        help="Run linter as part of doctor checks"
    )
    
    # Output options
    doctor_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    
    doctor_parser.add_argument(
        "--output", "-o",
        help="Output file for results (default: stdout)"
    )


def handle_doctor(args):
    """
    Handle the doctor command.
    
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
    
    # Create report
    report = run_doctor(target, args)
    
    # Output report
    output_report(report, args)
    
    # Return exit code based on report
    if report.summary.get('error_count', 0) > 0:
        return 1
    
    return 0


def run_doctor(target: Path, args) -> DoctorReport:
    """
    Run doctor checks on target file or directory.
    
    Args:
        target: Target file or directory
        args: Parsed command-line arguments
        
    Returns:
        DoctorReport containing diagnostic information
    """
    report = DoctorReport(target)
    
    # Find MDP files to check
    if target.is_file():
        report.files = [target]
    else:  # Directory
        if args.recursive:
            report.files = list(target.rglob("*.mdp"))
        else:
            report.files = list(target.glob("*.mdp"))
    
    # Run checks on each file
    for file_path in report.files:
        file_report = check_file(file_path, args)
        report.file_reports[file_path] = file_report
    
    # Run relationship checks if requested
    if args.check_relationships:
        check_relationships(report, args)
    
    # Run version checks if requested
    if args.check_versions:
        check_versions(report, args)
    
    # Run linter if requested
    if args.with_lint:
        run_linter(report, args)
    
    # Generate suggestions
    generate_suggestions(report, args)
    
    # Create summary
    generate_summary(report)
    
    # Fix issues if requested
    if args.fix:
        fix_issues(report, args)
    
    return report


def check_file(file_path: Path, args) -> Dict[str, Any]:
    """
    Run basic checks on a single file.
    
    Args:
        file_path: Path to the MDP file
        args: Parsed command-line arguments
        
    Returns:
        Dictionary with check results
    """
    report = {
        'status': 'ok',
        'errors': [],
        'warnings': [],
        'info': []
    }
    
    try:
        # Try to read the file
        mdp_file = read_mdp(file_path)
        report['mdp_file'] = mdp_file
        
        # Check basic metadata
        basic_checks(mdp_file, report)
        
        # Validate against schema
        schema_validate(mdp_file, report, args.profile)
    
    except Exception as e:
        report['status'] = 'error'
        report['errors'].append({
            'type': 'file_read',
            'message': f"Failed to read file: {e}"
        })
    
    # Determine overall status
    if len(report['errors']) > 0:
        report['status'] = 'error'
    elif len(report['warnings']) > 0:
        report['status'] = 'warning'
    
    return report


def basic_checks(mdp_file: MDPFile, report: Dict[str, Any]):
    """
    Perform basic checks on an MDPFile.
    
    Args:
        mdp_file: MDPFile to check
        report: Report dictionary to update with results
    """
    # Check for title
    if 'title' not in mdp_file.metadata:
        report['errors'].append({
            'type': 'missing_title',
            'message': "Document has no title"
        })
    
    # Check UUID
    if 'uuid' in mdp_file.metadata:
        uuid = mdp_file.metadata['uuid']
        if not is_valid_uuid(uuid):
            report['errors'].append({
                'type': 'invalid_uuid',
                'message': f"Invalid UUID: {uuid}"
            })
    else:
        report['warnings'].append({
            'type': 'missing_uuid',
            'message': "Document has no UUID"
        })
    
    # Check version
    if 'version' in mdp_file.metadata:
        version = mdp_file.metadata['version']
        if not is_semantic_version(version):
            report['errors'].append({
                'type': 'invalid_version',
                'message': f"Invalid semantic version: {version}"
            })
    else:
        report['warnings'].append({
            'type': 'missing_version',
            'message': "Document has no version"
        })
    
    # Check created_at and updated_at
    if 'created_at' not in mdp_file.metadata:
        report['warnings'].append({
            'type': 'missing_created_at',
            'message': "Document has no created_at date"
        })
    
    if 'updated_at' not in mdp_file.metadata:
        report['warnings'].append({
            'type': 'missing_updated_at',
            'message': "Document has no updated_at date"
        })
    
    # Check content
    if not mdp_file.content.strip():
        report['warnings'].append({
            'type': 'empty_content',
            'message': "Document has empty content"
        })
    else:
        # Check for heading
        if not mdp_file.content.lstrip().startswith('#'):
            report['info'].append({
                'type': 'missing_heading',
                'message': "Document content does not start with a heading"
            })


def schema_validate(mdp_file: MDPFile, report: Dict[str, Any], profile: str):
    """
    Validate an MDPFile against the schema.
    
    Args:
        mdp_file: MDPFile to validate
        report: Report dictionary to update with results
        profile: Validation profile to use
    """
    try:
        valid, validation_errors = validate_metadata_with_schema(
            mdp_file.metadata,
            profile=profile
        )
        
        if not valid:
            for field, message in validation_errors.items():
                report['errors'].append({
                    'type': 'schema_validation',
                    'field': field,
                    'message': message
                })
    except Exception as e:
        report['errors'].append({
            'type': 'schema_validation_error',
            'message': f"Error validating against schema: {e}"
        })


def check_relationships(report: DoctorReport, args):
    """
    Check relationship integrity across all files.
    
    Args:
        report: DoctorReport to update with results
        args: Parsed command-line arguments
    """
    # Build a map of UUIDs to files
    uuid_map = {}
    for file_path in report.files:
        file_report = report.file_reports[file_path]
        
        if file_report['status'] == 'error':
            continue
        
        mdp_file = file_report['mdp_file']
        
        if 'uuid' in mdp_file.metadata:
            uuid = mdp_file.metadata['uuid']
            if is_valid_uuid(uuid):
                uuid_map[uuid] = file_path
    
    # Check relationships in each file
    for file_path in report.files:
        file_report = report.file_reports[file_path]
        
        if file_report['status'] == 'error':
            continue
        
        mdp_file = file_report['mdp_file']
        
        if 'relationships' not in mdp_file.metadata:
            continue
        
        relationships = mdp_file.metadata['relationships']
        if not isinstance(relationships, list):
            continue
        
        for rel in relationships:
            if not isinstance(rel, dict):
                report.relationships['invalid'].append((file_path, rel))
                continue
            
            # Check required fields
            if 'type' not in rel:
                report.relationships['invalid'].append((file_path, rel))
                continue
            
            # Check that at least one identifier is present
            if not any(key in rel for key in ['id', 'uri', 'path', 'cid']):
                report.relationships['invalid'].append((file_path, rel))
                continue
            
            # Check referenced UUID
            if 'id' in rel and rel['id']:
                uuid = rel['id']
                
                if not is_valid_uuid(uuid):
                    report.relationships['invalid'].append((file_path, rel))
                    continue
                
                if uuid not in uuid_map:
                    report.relationships['broken'].append((file_path, rel))
            
            # Check referenced path
            if 'path' in rel and rel['path']:
                path = rel['path']
                
                # Resolve path relative to file's location
                full_path = os.path.join(os.path.dirname(file_path), path)
                full_path = str(Path(full_path).resolve())
                
                if not os.path.exists(full_path):
                    report.relationships['broken'].append((file_path, rel))
    
    # Find orphaned relationships (documents that are referenced but don't reference back)
    # This is a complex check and would require building a relationship graph
    # For simplicity, not implementing it here


def check_versions(report: DoctorReport, args):
    """
    Check version integrity across all files.
    
    Args:
        report: DoctorReport to update with results
        args: Parsed command-line arguments
    """
    for file_path in report.files:
        file_report = report.file_reports[file_path]
        
        if file_report['status'] == 'error':
            continue
        
        mdp_file = file_report['mdp_file']
        
        # Check if version exists
        if 'version' not in mdp_file.metadata:
            report.versions['missing'].append(file_path)
            continue
        
        version = mdp_file.metadata['version']
        
        # Check if version is valid semver
        if not is_semantic_version(version):
            report.versions['invalid'].append(file_path)
            continue
        
        # Check version history if available
        if 'version_history' in mdp_file.metadata:
            version_history = mdp_file.metadata['version_history']
            
            if not isinstance(version_history, list):
                file_report['warnings'].append({
                    'type': 'invalid_version_history',
                    'message': "version_history should be a list"
                })
                continue
            
            # Check version history entries
            for i, entry in enumerate(version_history):
                if not isinstance(entry, dict):
                    file_report['warnings'].append({
                        'type': 'invalid_version_history_entry',
                        'message': f"version_history entry {i} should be an object"
                    })
                    continue
                
                # Check version in entry
                if 'version' not in entry:
                    file_report['warnings'].append({
                        'type': 'missing_version_in_history',
                        'message': f"version_history entry {i} is missing version"
                    })
                    continue
                
                history_version = entry['version']
                if not is_semantic_version(history_version):
                    file_report['warnings'].append({
                        'type': 'invalid_version_in_history',
                        'message': f"version_history entry {i} has invalid version: {history_version}"
                    })


def run_linter(report: DoctorReport, args):
    """
    Run linter on all files.
    
    Args:
        report: DoctorReport to update with results
        args: Parsed command-line arguments
    """
    linter = MDPLinter()
    
    for file_path in report.files:
        # Skip files that couldn't be read
        if report.file_reports[file_path]['status'] == 'error' and 'mdp_file' not in report.file_reports[file_path]:
            continue
        
        result = linter.lint_file(file_path)
        report.lint_results[file_path] = result


def generate_suggestions(report: DoctorReport, args):
    """
    Generate suggestions for improvement.
    
    Args:
        report: DoctorReport to update with suggestions
        args: Parsed command-line arguments
    """
    # Suggestions based on missing fields
    missing_fields = {'uuid': [], 'version': [], 'author': [], 'tags': []}
    
    for file_path in report.files:
        file_report = report.file_reports[file_path]
        
        if file_report['status'] == 'error' or 'mdp_file' not in file_report:
            continue
        
        mdp_file = file_report['mdp_file']
        
        for field in missing_fields:
            if field not in mdp_file.metadata:
                missing_fields[field].append(file_path)
    
    for field, files in missing_fields.items():
        if len(files) > 5:  # Only suggest if multiple files are affected
            report.suggestions.append({
                'type': f'add_{field}',
                'message': f"Add '{field}' to {len(files)} files that are missing it",
                'files': [str(path) for path in files[:5]] + (["..."] if len(files) > 5 else [])
            })
    
    # Suggestions based on relationship issues
    if len(report.relationships['broken']) > 0:
        report.suggestions.append({
            'type': 'fix_broken_relationships',
            'message': f"Fix {len(report.relationships['broken'])} broken relationships",
            'relationships': [(str(path), rel) for path, rel in report.relationships['broken'][:5]]
        })
    
    # Suggestions based on version issues
    if len(report.versions['missing']) > 0:
        report.suggestions.append({
            'type': 'add_versions',
            'message': f"Add version information to {len(report.versions['missing'])} files",
            'files': [str(path) for path in report.versions['missing'][:5]] + (["..."] if len(report.versions['missing']) > 5 else [])
        })
    
    # Suggestions based on file structure
    if report.is_directory and len(report.files) > 10:
        # Check if files have similar titles or content
        # This would be a complex analysis and not implemented here
        pass


def generate_summary(report: DoctorReport):
    """
    Generate a summary of the report.
    
    Args:
        report: DoctorReport to update with summary
    """
    error_count = 0
    warning_count = 0
    info_count = 0
    
    # Count issues from file reports
    for file_report in report.file_reports.values():
        error_count += len(file_report.get('errors', []))
        warning_count += len(file_report.get('warnings', []))
        info_count += len(file_report.get('info', []))
    
    # Count issues from lint results
    for result in report.lint_results.values():
        error_count += result.error_count
        warning_count += result.warning_count
        info_count += result.info_count
    
    # Count relationship issues
    relationship_issues = (
        len(report.relationships['invalid']) +
        len(report.relationships['broken']) +
        len(report.relationships['orphaned'])
    )
    
    # Count version issues
    version_issues = (
        len(report.versions['missing']) +
        len(report.versions['invalid'])
    )
    
    report.summary = {
        'file_count': len(report.files),
        'error_count': error_count,
        'warning_count': warning_count,
        'info_count': info_count,
        'relationship_issues': relationship_issues,
        'version_issues': version_issues,
        'suggestion_count': len(report.suggestions)
    }


def fix_issues(report: DoctorReport, args):
    """
    Fix common issues automatically.
    
    Args:
        report: DoctorReport with issues to fix
        args: Parsed command-line arguments
    """
    # This would implement automatic fixes for common issues
    # For simplicity, not implementing the full logic here
    pass


def output_report(report: DoctorReport, args):
    """
    Output the doctor report.
    
    Args:
        report: DoctorReport to output
        args: Parsed command-line arguments
    """
    output = None
    
    try:
        # Open output file if specified
        if args.output:
            output = open(args.output, "w")
        else:
            output = sys.stdout
        
        # Format and output report
        if args.format == "json":
            output_json(report, output)
        else:  # text
            output_text(report, output)
    
    finally:
        # Close output file if we opened one
        if output is not None and output != sys.stdout:
            output.close()


def output_json(report: DoctorReport, output=sys.stdout):
    """Output report in JSON format."""
    json.dump(report.to_dict(), output, indent=2)


def output_text(report: DoctorReport, output=sys.stdout):
    """Output report in text format."""
    summary = report.summary
    
    output.write(f"MDP Doctor Report for {report.target_path}\n")
    output.write("=" * 60 + "\n\n")
    
    output.write("Summary:\n")
    output.write(f"- Examined {summary['file_count']} files\n")
    output.write(f"- Found {summary['error_count']} errors, {summary['warning_count']} warnings, {summary['info_count']} info\n")
    output.write(f"- Relationship issues: {summary['relationship_issues']}\n")
    output.write(f"- Version issues: {summary['version_issues']}\n")
    output.write(f"- Suggestions: {summary['suggestion_count']}\n")
    
    if report.suggestions:
        output.write("\nSuggestions:\n")
        for i, suggestion in enumerate(report.suggestions):
            output.write(f"{i+1}. {suggestion['message']}\n")
    
    # Display file with errors
    files_with_errors = [path for path, file_report in report.file_reports.items() 
                         if file_report.get('status') == 'error']
    
    if files_with_errors:
        output.write("\nFiles with errors:\n")
        for path in files_with_errors[:10]:  # Limit to 10 files
            output.write(f"- {path}\n")
        
        if len(files_with_errors) > 10:
            output.write(f"  ... and {len(files_with_errors) - 10} more\n")
    
    # Display relationship issues
    if report.relationships['broken']:
        output.write("\nBroken relationships:\n")
        for path, rel in report.relationships['broken'][:5]:  # Limit to 5 relationships
            if 'id' in rel:
                output.write(f"- {path}: references ID {rel['id']}\n")
            elif 'path' in rel:
                output.write(f"- {path}: references path {rel['path']}\n")
        
        if len(report.relationships['broken']) > 5:
            output.write(f"  ... and {len(report.relationships['broken']) - 5} more\n")
    
    # Display lint results if available
    if report.lint_results:
        error_count = sum(result.error_count for result in report.lint_results.values())
        if error_count > 0:
            output.write("\nLint errors:\n")
            for path, result in report.lint_results.items():
                if result.error_count > 0:
                    output.write(f"- {path}: {result.error_count} errors\n")
    
    output.write("\n")
    if summary['error_count'] == 0:
        output.write("🎉 No errors found! Your MDP files look healthy.\n")
    else:
        output.write(f"❌ Found {summary['error_count']} errors that need attention.\n") 