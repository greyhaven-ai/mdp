"""
Rules for linting MDP files.

This module defines the Rule class and its subclasses for
checking different aspects of MDP files.
"""

import os
import re
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set, Type, Callable

from ..core import MDPFile
from ..metadata import extract_metadata, is_semantic_version, is_valid_uuid, validate_metadata
from ..schema.validation import validate_metadata_with_schema
from .linter import LintError, LintSeverity


class Rule(ABC):
    """
    Base class for linting rules.
    
    Rules define checks to be performed on MDP files and
    return LintError objects for any issues found.
    """
    
    def __init__(self, id: str, description: str, category: str = "general"):
        """
        Initialize a Rule.
        
        Args:
            id: Unique identifier for the rule
            description: Human-readable description of the rule
            category: Category for the rule (metadata, content, relationship, etc.)
        """
        self.id = id
        self.description = description
        self.category = category
    
    @abstractmethod
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """
        Check an MDP file against this rule.
        
        Args:
            mdp_file: MDPFile to check
            
        Returns:
            List of LintError objects for any issues found
        """
        pass
    
    def should_apply(self, mdp_file: MDPFile) -> bool:
        """
        Determine if this rule should be applied to a file.
        
        Args:
            mdp_file: MDPFile to check
            
        Returns:
            True if the rule should be applied, False otherwise
        """
        return True
    
    def __str__(self) -> str:
        """Return a string representation of the rule."""
        return f"{self.id}: {self.description}"


class MetadataRule(Rule):
    """Base class for rules that check metadata."""
    
    def __init__(self, id: str, description: str):
        """Initialize a MetadataRule."""
        super().__init__(id, description, category="metadata")


class ContentRule(Rule):
    """Base class for rules that check content."""
    
    def __init__(self, id: str, description: str):
        """Initialize a ContentRule."""
        super().__init__(id, description, category="content")


class RelationshipRule(Rule):
    """Base class for rules that check relationships."""
    
    def __init__(self, id: str, description: str):
        """Initialize a RelationshipRule."""
        super().__init__(id, description, category="relationship")


# --------------------------------
# Metadata Rules
# --------------------------------

class RequiredFieldsRule(MetadataRule):
    """Rule to check for required metadata fields."""
    
    def __init__(self, required_fields: Optional[List[str]] = None):
        """
        Initialize a RequiredFieldsRule.
        
        Args:
            required_fields: List of fields that must be present
        """
        super().__init__(
            id="metadata-required-fields",
            description="Check for required metadata fields"
        )
        # Default required fields if none provided
        self.required_fields = required_fields or ["title"]
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check for required fields in metadata."""
        errors = []
        
        for field in self.required_fields:
            if field not in mdp_file.metadata:
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Required field '{field}' is missing",
                    severity=LintSeverity.ERROR,
                    field=field,
                    fix=self._add_default_value(field) if self._has_default(field) else None
                ))
        
        return errors
    
    def _has_default(self, field: str) -> bool:
        """Check if a field has a default value."""
        return field in self._default_values()
    
    def _default_values(self) -> Dict[str, Any]:
        """Define default values for fields."""
        return {
            "title": "Untitled Document",
            "version": "0.1.0",
            "created_at": "YYYY-MM-DD",  # Will be replaced with current date
            "updated_at": "YYYY-MM-DD",  # Will be replaced with current date
        }
    
    def _add_default_value(self, field: str) -> Callable:
        """Create a fix function to add a default value."""
        def fix_function(mdp_file: MDPFile, error: LintError) -> MDPFile:
            default_values = self._default_values()
            
            if field in default_values:
                # If it's a date field, use current date
                import datetime
                value = default_values[field]
                if value == "YYYY-MM-DD":
                    value = datetime.date.today().strftime("%Y-%m-%d")
                
                # Add the field with default value
                mdp_file.metadata[field] = value
            
            return mdp_file
        
        return fix_function


class FieldTypeRule(MetadataRule):
    """Rule to check metadata field types."""
    
    def __init__(self, field_types: Optional[Dict[str, Type]] = None):
        """
        Initialize a FieldTypeRule.
        
        Args:
            field_types: Dictionary mapping field names to expected types
        """
        super().__init__(
            id="metadata-field-types",
            description="Check metadata field types"
        )
        # Default field types if none provided
        self.field_types = field_types or {
            "title": str,
            "version": str,
            "author": str,
            "created_at": str,
            "updated_at": str,
            "tags": list,
            "relationships": list,
        }
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check metadata field types."""
        errors = []
        
        for field, expected_type in self.field_types.items():
            if field in mdp_file.metadata:
                value = mdp_file.metadata[field]
                
                if value is not None and not isinstance(value, expected_type):
                    errors.append(LintError(
                        rule_id=self.id,
                        message=f"Field '{field}' should be of type {expected_type.__name__}, got {type(value).__name__}",
                        severity=LintSeverity.ERROR,
                        field=field,
                        fix=self._fix_type(field, expected_type) if self._can_fix_type(value, expected_type) else None
                    ))
        
        return errors
    
    def _can_fix_type(self, value: Any, expected_type: Type) -> bool:
        """Check if a value's type can be fixed."""
        try:
            # Try a simple conversion
            if expected_type is str:
                str(value)
                return True
            elif expected_type is int:
                int(value)
                return True
            elif expected_type is float:
                float(value)
                return True
            elif expected_type is list and isinstance(value, str):
                return True  # Can convert string to single-item list
            elif expected_type is dict and isinstance(value, str):
                yaml.safe_load(value)  # Try parsing as YAML
                return True
            
            return False
        except (ValueError, TypeError, yaml.YAMLError):
            return False
    
    def _fix_type(self, field: str, expected_type: Type) -> Callable:
        """Create a fix function to correct a field's type."""
        def fix_function(mdp_file: MDPFile, error: LintError) -> MDPFile:
            value = mdp_file.metadata[field]
            
            try:
                if expected_type is str:
                    mdp_file.metadata[field] = str(value)
                elif expected_type is int:
                    mdp_file.metadata[field] = int(value)
                elif expected_type is float:
                    mdp_file.metadata[field] = float(value)
                elif expected_type is list and isinstance(value, str):
                    mdp_file.metadata[field] = [value]  # Convert to single-item list
                elif expected_type is dict and isinstance(value, str):
                    mdp_file.metadata[field] = yaml.safe_load(value)
            except (ValueError, TypeError, yaml.YAMLError):
                # If conversion fails, leave it for manual fixing
                pass
            
            return mdp_file
        
        return fix_function


class VersionFormatRule(MetadataRule):
    """Rule to check semantic version format."""
    
    def __init__(self):
        """Initialize a VersionFormatRule."""
        super().__init__(
            id="metadata-version-format",
            description="Check semantic version format (MAJOR.MINOR.PATCH)"
        )
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check if version follows semantic versioning format."""
        errors = []
        
        if "version" in mdp_file.metadata:
            version = mdp_file.metadata["version"]
            
            if version is not None and not is_semantic_version(version):
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Version '{version}' does not follow semantic versioning format (MAJOR.MINOR.PATCH)",
                    severity=LintSeverity.ERROR,
                    field="version",
                    fix=self._fix_version if self._can_fix_version(version) else None
                ))
        
        return errors
    
    def _can_fix_version(self, version: Any) -> bool:
        """Check if a version can be fixed."""
        # If it's already a string and has at least one digit, we'll try to fix it
        return isinstance(version, str) and any(c.isdigit() for c in version)
    
    def _fix_version(self, mdp_file: MDPFile, error: LintError) -> MDPFile:
        """Fix invalid version format."""
        version = mdp_file.metadata["version"]
        
        # Extract digits from the version
        parts = re.findall(r'\d+', version)
        
        if len(parts) >= 3:
            # Use the first three number groups
            fixed_version = f"{parts[0]}.{parts[1]}.{parts[2]}"
        elif len(parts) == 2:
            # Use the two number groups and add .0
            fixed_version = f"{parts[0]}.{parts[1]}.0"
        elif len(parts) == 1:
            # Use the one number group and add .0.0
            fixed_version = f"{parts[0]}.0.0"
        else:
            # Default to 0.1.0
            fixed_version = "0.1.0"
        
        mdp_file.metadata["version"] = fixed_version
        return mdp_file


class DateFormatRule(MetadataRule):
    """Rule to check date format (YYYY-MM-DD)."""
    
    def __init__(self, date_fields: Optional[List[str]] = None):
        """
        Initialize a DateFormatRule.
        
        Args:
            date_fields: List of fields that should contain dates
        """
        super().__init__(
            id="metadata-date-format",
            description="Check date format (YYYY-MM-DD)"
        )
        self.date_fields = date_fields or ["created_at", "updated_at"]
        self.date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check date format."""
        errors = []
        
        for field in self.date_fields:
            if field in mdp_file.metadata:
                value = mdp_file.metadata[field]
                
                if value is not None and isinstance(value, str) and not self.date_pattern.match(value):
                    errors.append(LintError(
                        rule_id=self.id,
                        message=f"Field '{field}' should follow date format YYYY-MM-DD, got '{value}'",
                        severity=LintSeverity.ERROR,
                        field=field,
                        fix=self._fix_date if self._can_fix_date(value) else None
                    ))
        
        return errors
    
    def _can_fix_date(self, date_str: str) -> bool:
        """Check if a date can be fixed."""
        # If it has digits and separators, we'll try to fix it
        return isinstance(date_str, str) and re.search(r'\d', date_str) is not None
    
    def _fix_date(self, mdp_file: MDPFile, error: LintError) -> MDPFile:
        """Fix invalid date format."""
        field = error.field
        date_str = mdp_file.metadata[field]
        
        # Try different date formats
        from ..metadata import format_date
        import datetime
        
        try:
            # Try to format the date
            formatted_date = format_date(date_str)
            mdp_file.metadata[field] = formatted_date
        except ValueError:
            # If formatting fails, use current date
            mdp_file.metadata[field] = datetime.date.today().strftime("%Y-%m-%d")
        
        return mdp_file


class UUIDFormatRule(MetadataRule):
    """Rule to check UUID format."""
    
    def __init__(self):
        """Initialize a UUIDFormatRule."""
        super().__init__(
            id="metadata-uuid-format",
            description="Check UUID format"
        )
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check UUID format."""
        errors = []
        
        if "uuid" in mdp_file.metadata:
            uuid = mdp_file.metadata["uuid"]
            
            if uuid is not None and not is_valid_uuid(uuid):
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"UUID '{uuid}' is not a valid UUID",
                    severity=LintSeverity.ERROR,
                    field="uuid",
                    fix=self._fix_uuid
                ))
        
        return errors
    
    def _fix_uuid(self, mdp_file: MDPFile, error: LintError) -> MDPFile:
        """Fix invalid UUID by generating a new one."""
        from ..metadata import generate_uuid
        mdp_file.metadata["uuid"] = generate_uuid()
        return mdp_file


class SchemaValidationRule(MetadataRule):
    """Rule to validate metadata against the MDP schema."""
    
    def __init__(self, schema_path: Optional[str] = None, profile: Optional[str] = None):
        """
        Initialize a SchemaValidationRule.
        
        Args:
            schema_path: Path to a custom schema file (optional)
            profile: Validation profile to use (minimal, standard, etc.)
        """
        super().__init__(
            id="metadata-schema-validation",
            description="Validate metadata against the MDP schema"
        )
        self.schema_path = schema_path
        self.profile = profile
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Validate metadata against the schema."""
        errors = []
        
        # Use the schema validation from the schema module
        try:
            valid, validation_errors = validate_metadata_with_schema(
                mdp_file.metadata,
                schema_path=self.schema_path,
                profile=self.profile
            )
            
            if not valid:
                for field, message in validation_errors.items():
                    errors.append(LintError(
                        rule_id=self.id,
                        message=message,
                        severity=LintSeverity.ERROR,
                        field=field
                    ))
        except Exception as e:
            errors.append(LintError(
                rule_id=self.id,
                message=f"Schema validation error: {e}",
                severity=LintSeverity.ERROR
            ))
        
        return errors


# --------------------------------
# Content Rules
# --------------------------------

class HeadingStructureRule(ContentRule):
    """Rule to check Markdown heading structure."""
    
    def __init__(self, require_title: bool = True, max_heading_level: int = 6):
        """
        Initialize a HeadingStructureRule.
        
        Args:
            require_title: Whether a level 1 heading is required
            max_heading_level: Maximum allowed heading level
        """
        super().__init__(
            id="content-heading-structure",
            description="Check Markdown heading structure"
        )
        self.require_title = require_title
        self.max_heading_level = max_heading_level
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check heading structure."""
        errors = []
        content = mdp_file.content
        
        # Find all ATX headings (# style)
        heading_pattern = re.compile(r'^(#{1,6})[ \t]+(.+?)[ \t]*(?:#+[ \t]*)?$', re.MULTILINE)
        headings = heading_pattern.finditer(content)
        
        # Check if there's a title (level 1 heading)
        if self.require_title:
            has_title = False
            for match in heading_pattern.finditer(content):
                if match.group(1) == '#':
                    has_title = True
                    break
            
            if not has_title:
                errors.append(LintError(
                    rule_id=self.id,
                    message="Document should have a title (level 1 heading/H1)",
                    severity=LintSeverity.ERROR,
                    source="content",
                    fix=self._fix_missing_title(mdp_file.metadata.get("title", "Untitled Document"))
                ))
        
        # Check heading levels
        level_sequence = []
        for match in heading_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for excessive heading level
            if level > self.max_heading_level:
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Heading level {level} exceeds maximum allowed level ({self.max_heading_level})",
                    severity=LintSeverity.WARNING,
                    source="content",
                    location={"line": line_num},
                    fix=self._fix_heading_level(level)
                ))
            
            level_sequence.append(level)
        
        # Check for skipped heading levels (e.g., H1 -> H3)
        prev_level = 0
        for i, level in enumerate(level_sequence):
            if level > prev_level + 1 and prev_level > 0:
                line_num = 0
                for j, match in enumerate(heading_pattern.finditer(content)):
                    if j == i:
                        line_num = content[:match.start()].count('\n') + 1
                        break
                
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Skipped heading level: H{prev_level} to H{level}",
                    severity=LintSeverity.WARNING,
                    source="content",
                    location={"line": line_num}
                ))
            
            prev_level = level
        
        return errors
    
    def _fix_missing_title(self, title: str) -> Callable:
        """Create a fix function to add a missing title."""
        def fix_function(mdp_file: MDPFile, error: LintError) -> MDPFile:
            # Add a title at the beginning of the content
            mdp_file.content = f"# {title}\n\n{mdp_file.content}"
            return mdp_file
        
        return fix_function
    
    def _fix_heading_level(self, level: int) -> Callable:
        """Create a fix function to fix excessive heading level."""
        def fix_function(mdp_file: MDPFile, error: LintError) -> MDPFile:
            line_num = error.location.get("line", 0)
            if line_num == 0:
                return mdp_file
            
            lines = mdp_file.content.splitlines()
            if line_num <= len(lines):
                # Replace the heading with a max-level heading
                heading_line = lines[line_num - 1]
                fixed_heading = '#' * self.max_heading_level + heading_line[level:]
                lines[line_num - 1] = fixed_heading
                mdp_file.content = '\n'.join(lines)
            
            return mdp_file
        
        return fix_function


class LinkValidationRule(ContentRule):
    """Rule to check for broken links in content."""
    
    def __init__(self):
        """Initialize a LinkValidationRule."""
        super().__init__(
            id="content-link-validation",
            description="Check for broken or malformed links"
        )
        self.md_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check for broken or malformed links."""
        errors = []
        content = mdp_file.content
        
        # Find all Markdown links
        for match in self.md_link_pattern.finditer(content):
            link_text = match.group(1)
            link_url = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for empty link text
            if not link_text.strip():
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Link has empty text: [{link_text}]({link_url})",
                    severity=LintSeverity.WARNING,
                    source="content",
                    location={"line": line_num},
                    fix=self._fix_empty_link_text(link_url)
                ))
            
            # Check for empty link URL
            if not link_url.strip():
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Link has empty URL: [{link_text}]()",
                    severity=LintSeverity.ERROR,
                    source="content",
                    location={"line": line_num}
                ))
            
            # Check for malformed URLs
            if link_url.strip() and not self._is_valid_url(link_url):
                # Don't flag anchor links or relative paths
                if not (link_url.startswith('#') or link_url.startswith('./') or link_url.startswith('../')):
                    errors.append(LintError(
                        rule_id=self.id,
                        message=f"Link may have malformed URL: [{link_text}]({link_url})",
                        severity=LintSeverity.WARNING,
                        source="content",
                        location={"line": line_num}
                    ))
        
        return errors
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        # Simple URL validation - check for protocol and domain
        return '://' in url or url.startswith('/') or url.startswith('#')
    
    def _fix_empty_link_text(self, url: str) -> Callable:
        """Create a fix function for empty link text."""
        def fix_function(mdp_file: MDPFile, error: LintError) -> MDPFile:
            line_num = error.location.get("line", 0)
            if line_num == 0:
                return mdp_file
            
            lines = mdp_file.content.splitlines()
            if line_num <= len(lines):
                # Use URL as the link text
                line = lines[line_num - 1]
                line = line.replace('[](' + url + ')', '[' + url + '](' + url + ')')
                lines[line_num - 1] = line
                mdp_file.content = '\n'.join(lines)
            
            return mdp_file
        
        return fix_function


# --------------------------------
# Relationship Rules
# --------------------------------

class RelationshipFieldsRule(RelationshipRule):
    """Rule to check relationship fields."""
    
    def __init__(self):
        """Initialize a RelationshipFieldsRule."""
        super().__init__(
            id="relationship-fields",
            description="Check for required fields in relationships"
        )
    
    def should_apply(self, mdp_file: MDPFile) -> bool:
        """Check if this rule should be applied."""
        return "relationships" in mdp_file.metadata
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check relationship fields."""
        errors = []
        
        if "relationships" not in mdp_file.metadata:
            return errors
        
        relationships = mdp_file.metadata["relationships"]
        if not isinstance(relationships, list):
            errors.append(LintError(
                rule_id=self.id,
                message="Relationships field must be a list",
                severity=LintSeverity.ERROR,
                field="relationships",
                fix=self._fix_relationships_type
            ))
            return errors
        
        for i, rel in enumerate(relationships):
            if not isinstance(rel, dict):
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Relationship at index {i} must be an object",
                    severity=LintSeverity.ERROR,
                    field="relationships"
                ))
                continue
            
            # Check for required fields
            if "type" not in rel:
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Relationship at index {i} is missing required field 'type'",
                    severity=LintSeverity.ERROR,
                    field="relationships"
                ))
            
            # Check that at least one identifier is present
            if not any(key in rel for key in ["id", "uri", "path", "cid"]):
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Relationship at index {i} must have at least one of: id, uri, path, or cid",
                    severity=LintSeverity.ERROR,
                    field="relationships"
                ))
            
            # Check that type is valid
            if "type" in rel and rel["type"] not in ["parent", "child", "related", "reference"]:
                errors.append(LintError(
                    rule_id=self.id,
                    message=f"Relationship at index {i} has invalid type: {rel['type']}",
                    severity=LintSeverity.ERROR,
                    field="relationships",
                    fix=self._fix_relationship_type(i)
                ))
        
        return errors
    
    def _fix_relationships_type(self, mdp_file: MDPFile, error: LintError) -> MDPFile:
        """Fix relationships type."""
        # Convert to list if possible
        rel = mdp_file.metadata["relationships"]
        if isinstance(rel, dict):
            mdp_file.metadata["relationships"] = [rel]
        else:
            mdp_file.metadata["relationships"] = []
        
        return mdp_file
    
    def _fix_relationship_type(self, index: int) -> Callable:
        """Create a fix function for invalid relationship type."""
        def fix_function(mdp_file: MDPFile, error: LintError) -> MDPFile:
            relationships = mdp_file.metadata["relationships"]
            if index < len(relationships):
                relationships[index]["type"] = "related"  # Default to 'related'
            
            return mdp_file
        
        return fix_function


class RelationshipIntegrityRule(RelationshipRule):
    """Rule to check relationship references."""
    
    def __init__(self, check_existence: bool = False, base_dir: Optional[str] = None):
        """
        Initialize a RelationshipIntegrityRule.
        
        Args:
            check_existence: Whether to check if referenced files exist
            base_dir: Base directory for resolving relative paths
        """
        super().__init__(
            id="relationship-integrity",
            description="Check relationship references"
        )
        self.check_existence = check_existence
        self.base_dir = base_dir
    
    def should_apply(self, mdp_file: MDPFile) -> bool:
        """Check if this rule should be applied."""
        return "relationships" in mdp_file.metadata
    
    def check(self, mdp_file: MDPFile) -> List[LintError]:
        """Check relationship references."""
        errors = []
        
        if "relationships" not in mdp_file.metadata or not isinstance(mdp_file.metadata["relationships"], list):
            return errors
        
        relationships = mdp_file.metadata["relationships"]
        
        for i, rel in enumerate(relationships):
            if not isinstance(rel, dict):
                continue
            
            # Check UUID format
            if "id" in rel and rel["id"]:
                if not is_valid_uuid(rel["id"]):
                    errors.append(LintError(
                        rule_id=self.id,
                        message=f"Relationship at index {i} has invalid UUID: {rel['id']}",
                        severity=LintSeverity.ERROR,
                        field="relationships"
                    ))
            
            # Check URI format
            if "uri" in rel and rel["uri"]:
                if not self._is_valid_uri(rel["uri"]):
                    errors.append(LintError(
                        rule_id=self.id,
                        message=f"Relationship at index {i} has invalid URI: {rel['uri']}",
                        severity=LintSeverity.ERROR,
                        field="relationships"
                    ))
            
            # Check path existence
            if self.check_existence and "path" in rel and rel["path"]:
                path = rel["path"]
                
                # Resolve path relative to base_dir or file's location
                if self.base_dir:
                    full_path = os.path.join(self.base_dir, path)
                elif mdp_file.path:
                    full_path = os.path.join(os.path.dirname(mdp_file.path), path)
                else:
                    full_path = path
                
                if not os.path.exists(full_path):
                    errors.append(LintError(
                        rule_id=self.id,
                        message=f"Relationship at index {i} references file that does not exist: {path}",
                        severity=LintSeverity.WARNING,
                        field="relationships"
                    ))
        
        return errors
    
    def _is_valid_uri(self, uri: str) -> bool:
        """Check if a URI is valid."""
        # Simple URI validation - check for protocol scheme
        return '://' in uri


# --------------------------------
# Rule Loading Functions
# --------------------------------

def load_default_rules() -> List[Rule]:
    """
    Load the default set of linting rules.
    
    Returns:
        List of Rule objects
    """
    return [
        # Metadata rules
        RequiredFieldsRule(),
        FieldTypeRule(),
        VersionFormatRule(),
        DateFormatRule(),
        UUIDFormatRule(),
        SchemaValidationRule(),
        
        # Content rules
        HeadingStructureRule(),
        LinkValidationRule(),
        
        # Relationship rules
        RelationshipFieldsRule(),
        RelationshipIntegrityRule()
    ]


def load_custom_rules(rules_file: Union[str, Path]) -> List[Rule]:
    """
    Load custom linting rules from a file.
    
    Args:
        rules_file: Path to JSON/YAML file with rule configurations
        
    Returns:
        List of Rule objects
        
    Raises:
        FileNotFoundError: If the rules file does not exist
        ValueError: If the rules file has invalid format
    """
    rules_file = Path(rules_file)
    
    # Check file existence
    if not rules_file.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_file}")
    
    # Load the rules file
    try:
        with open(rules_file, 'r') as f:
            if rules_file.suffix == '.json':
                import json
                config = json.load(f)
            else:
                import yaml
                config = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to load rules file: {e}")
    
    # Parse the config
    rules = []
    
    # Add all rule classes and their constructors
    rule_classes = {
        'metadata-required-fields': RequiredFieldsRule,
        'metadata-field-types': FieldTypeRule,
        'metadata-version-format': VersionFormatRule,
        'metadata-date-format': DateFormatRule,
        'metadata-uuid-format': UUIDFormatRule,
        'metadata-schema-validation': SchemaValidationRule,
        'content-heading-structure': HeadingStructureRule,
        'content-link-validation': LinkValidationRule,
        'relationship-fields': RelationshipFieldsRule,
        'relationship-integrity': RelationshipIntegrityRule
    }
    
    # Process enabled rules
    if 'rules' in config:
        for rule_config in config['rules']:
            rule_id = rule_config.get('id')
            if rule_id in rule_classes and rule_config.get('enabled', True):
                # Get constructor args
                kwargs = {k: v for k, v in rule_config.items() if k not in ['id', 'enabled']}
                
                # Create the rule
                try:
                    rule = rule_classes[rule_id](**kwargs)
                    rules.append(rule)
                except Exception as e:
                    raise ValueError(f"Failed to create rule {rule_id}: {e}")
    
    return rules 