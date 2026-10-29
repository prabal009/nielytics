"""Predictable exceptions for callers; catch NIElyticsError at integration boundaries."""

class NIElyticsError(Exception):
    """Base library error."""

class ValidationError(NIElyticsError, ValueError):
    """Invalid input or configuration."""

class DataLoadError(NIElyticsError):
    """A dataset could not be read."""

class UnsupportedFormatError(DataLoadError):
    """An input format is unsupported."""

class OptionalDependencyError(NIElyticsError, ImportError):
    """Install the documented optional dependency for this operation."""
