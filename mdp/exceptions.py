"""
Exceptions used throughout the MDP package.

This module defines custom exceptions that are raised by various components
of the MDP package.
"""


class MDPError(Exception):
    """Base exception for all MDP-related errors."""
    pass


class ValidationError(MDPError):
    """Raised when validation of MDP metadata or content fails."""
    pass


class RelationshipError(MDPError):
    """Raised when there's an issue with MDP relationships."""
    pass


class VersioningError(MDPError):
    """Raised when there's an issue with MDP versioning."""
    pass


class ConflictError(MDPError):
    """Raised when there's a conflict during MDP operations."""
    pass


class FormatError(MDPError):
    """Raised when there's an issue with MDP formatting."""
    pass 