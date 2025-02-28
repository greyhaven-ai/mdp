"""
Core linting functionality for MDP files.

This module defines the MDPLinter class and related classes for
performing linting on MDP files.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Set, Any, Tuple, Callable

from ..core import MDPFile, read_mdp
from ..schema.validation import validate_metadata, load_schema


class LintSeverity(str, Enum):
    """Severity levels for lint errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LintError:
    """
    A lint error or warning found during linting.
    
    Attributes:
        rule_id: Identifier for the rule that generated this error
        message: Human-readable error message
        severity: Severity level (error, warning, info)
        location: Location of the error (path, line, column)
        source: Source of the error (metadata, content, relationship)
        field: Field name if the error is in metadata
        fix: Optional function that can fix the error
    """
    
    def __init__(
        self,
        rule_id: str,
        message: str,
        severity: LintSeverity = LintSeverity.ERROR,
        location: Optional[Dict[str, Any]] = None,
        source: str = "metadata",
        field: Optional[str] = None,
        fix: Optional[Callable] = None
    ):
        """Initialize a LintError."""
        self.rule_id = rule_id
        self.message = message
        self.severity = severity
        self.location = location or {}
        self.source = source
        self.field = field
        self.fix = fix
    
    def __str__(self) -> str:
        """Return a string representation of the error."""
        loc_str = ""
        if "line" in self.location:
            loc_str = f" at line {self.location['line']}"
            if "column" in self.location:
                loc_str += f", column {self.location['column']}"
        
        field_str = f" in field '{self.field}'" if self.field else ""
        
        return f"[{self.severity.upper()}] {self.rule_id}: {self.message}{field_str}{loc_str}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity,
            "location": self.location,
            "source": self.source,
            "field": self.field,
            "has_fix": self.fix is not None
        }
    
    def apply_fix(self, mdp_file: MDPFile) -> MDPFile:
        """
        Apply the fix to the MDPFile.
        
        Args:
            mdp_file: The MDPFile to fix
            
        Returns:
            Fixed MDPFile or the original if no fix is available
            
        Raises:
            ValueError: If the fix function raises an error
        """
        if self.fix is None:
            return mdp_file
        
        try:
            return self.fix(mdp_file, self)
        except Exception as e:
            raise ValueError(f"Error applying fix for {self.rule_id}: {e}")


class LintResult:
    """
    Result of a linting operation.
    
    Attributes:
        path: Path to the file that was linted
        errors: List of LintError objects found during linting
        warnings: List of LintError objects with warning severity
        info: List of LintError objects with info severity
    """
    
    def __init__(self, path: Union[str, Path]):
        """Initialize a LintResult."""
        self.path = Path(path)
        self.errors: List[LintError] = []
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return any(error.severity == LintSeverity.ERROR for error in self.errors)
    
    @property
    def error_count(self) -> int:
        """Get the number of errors."""
        return sum(1 for error in self.errors if error.severity == LintSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Get the number of warnings."""
        return sum(1 for error in self.errors if error.severity == LintSeverity.WARNING)
    
    @property
    def info_count(self) -> int:
        """Get the number of info messages."""
        return sum(1 for error in self.errors if error.severity == LintSeverity.INFO)
    
    def add_error(self, error: LintError) -> None:
        """Add an error to the result."""
        self.errors.append(error)
    
    def add_errors(self, errors: List[LintError]) -> None:
        """Add multiple errors to the result."""
        self.errors.extend(errors)
    
    def get_errors_by_severity(self, severity: LintSeverity) -> List[LintError]:
        """Get errors filtered by severity."""
        return [error for error in self.errors if error.severity == severity]
    
    def get_errors_by_source(self, source: str) -> List[LintError]:
        """Get errors filtered by source."""
        return [error for error in self.errors if error.source == source]
    
    def get_errors_by_rule(self, rule_id: str) -> List[LintError]:
        """Get errors filtered by rule ID."""
        return [error for error in self.errors if error.rule_id == rule_id]
    
    def get_fixable_errors(self) -> List[LintError]:
        """Get errors that have fixes available."""
        return [error for error in self.errors if error.fix is not None]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "path": str(self.path),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "errors": [error.to_dict() for error in self.errors]
        }
    
    def __str__(self) -> str:
        """Return a string representation of the result."""
        if not self.errors:
            return f"{self.path}: No issues found"
        
        result = f"{self.path}: {self.error_count} errors, {self.warning_count} warnings, {self.info_count} info\n"
        
        for error in sorted(self.errors, key=lambda e: (e.severity.value, e.location.get("line", 0))):
            result += f"  {str(error)}\n"
        
        return result


class MDPLinter:
    """
    Linter for MDP files.
    
    This class provides methods for linting MDP files using a set of rules.
    """
    
    def __init__(self, rules: Optional[List["Rule"]] = None):
        """
        Initialize an MDPLinter.
        
        Args:
            rules: List of Rule objects to use for linting
        """
        from .rules import load_default_rules
        self.rules = rules or load_default_rules()
        self._schema = None
    
    def lint_file(self, path: Union[str, Path]) -> LintResult:
        """
        Lint an MDP file.
        
        Args:
            path: Path to the MDP file
            
        Returns:
            LintResult containing any errors found
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        path = Path(path)
        result = LintResult(path)
        
        # Read the file
        try:
            mdp_file = read_mdp(path)
        except Exception as e:
            result.add_error(LintError(
                rule_id="mdp-file-read",
                message=f"Failed to read MDP file: {e}",
                severity=LintSeverity.ERROR,
                location={"path": str(path)}
            ))
            return result
        
        # Apply all rules
        for rule in self.rules:
            try:
                if rule.should_apply(mdp_file):
                    errors = rule.check(mdp_file)
                    result.add_errors(errors)
            except Exception as e:
                result.add_error(LintError(
                    rule_id="rule-application-error",
                    message=f"Error applying rule {rule.id}: {e}",
                    severity=LintSeverity.ERROR
                ))
        
        return result
    
    def lint_directory(
        self,
        directory: Union[str, Path],
        recursive: bool = True,
        include_pattern: str = "*.mdp"
    ) -> Dict[Path, LintResult]:
        """
        Lint all MDP files in a directory.
        
        Args:
            directory: Directory to lint
            recursive: Whether to search subdirectories
            include_pattern: Glob pattern for files to include
            
        Returns:
            Dictionary mapping file paths to LintResults
        """
        directory = Path(directory)
        results = {}
        
        # Find all MDP files
        if recursive:
            files = list(directory.rglob(include_pattern))
        else:
            files = list(directory.glob(include_pattern))
        
        # Lint each file
        for file_path in files:
            results[file_path] = self.lint_file(file_path)
        
        return results
    
    def lint_string(self, content: str, filename: Optional[str] = None) -> LintResult:
        """
        Lint MDP content from a string.
        
        Args:
            content: MDP content as a string
            filename: Optional filename for the content
            
        Returns:
            LintResult containing any errors
        """
        filename = filename or "<string>"
        result = LintResult(filename)
        
        # Parse the string into an MDPFile
        try:
            from ..metadata import extract_metadata
            metadata, md_content = extract_metadata(content)
            mdp_file = MDPFile(metadata, md_content, filename)
        except Exception as e:
            result.add_error(LintError(
                rule_id="mdp-parse",
                message=f"Failed to parse MDP content: {e}",
                severity=LintSeverity.ERROR
            ))
            return result
        
        # Apply all rules
        for rule in self.rules:
            try:
                if rule.should_apply(mdp_file):
                    errors = rule.check(mdp_file)
                    result.add_errors(errors)
            except Exception as e:
                result.add_error(LintError(
                    rule_id="rule-application-error",
                    message=f"Error applying rule {rule.id}: {e}",
                    severity=LintSeverity.ERROR
                ))
        
        return result
    
    def fix_file(self, path: Union[str, Path]) -> Tuple[MDPFile, List[LintError]]:
        """
        Apply fixes to an MDP file.
        
        Args:
            path: Path to the MDP file
            
        Returns:
            Tuple of (fixed MDPFile, list of applied fixes)
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        path = Path(path)
        
        # Read the file
        mdp_file = read_mdp(path)
        
        # Lint the file to find errors
        result = self.lint_file(path)
        
        # Get fixable errors
        fixable_errors = result.get_fixable_errors()
        applied_fixes = []
        
        # Apply fixes
        for error in fixable_errors:
            try:
                mdp_file = error.apply_fix(mdp_file)
                applied_fixes.append(error)
            except ValueError:
                # Skip fixes that fail
                continue
        
        return mdp_file, applied_fixes
    
    def add_rule(self, rule: "Rule") -> None:
        """Add a rule to the linter."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a rule from the linter.
        
        Args:
            rule_id: ID of the rule to remove
            
        Returns:
            True if the rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules.pop(i)
                return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional["Rule"]:
        """
        Get a rule by ID.
        
        Args:
            rule_id: ID of the rule to get
            
        Returns:
            Rule object or None if not found
        """
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def get_rules_by_category(self, category: str) -> List["Rule"]:
        """
        Get rules filtered by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of Rule objects in the category
        """
        return [rule for rule in self.rules if rule.category == category] 