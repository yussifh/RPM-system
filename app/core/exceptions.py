"""
exceptions.py
-------------
Custom exception hierarchy for the application.

Design decision: Instead of letting raw exceptions (KeyError, mysql
connector errors, etc.) leak up into the Streamlit UI layer, every layer
raises one of these well-named, domain-specific exceptions. The UI layer
catches these and shows the user a friendly message, while the real
error is still logged for debugging.
"""


class RPMSystemError(Exception):
    """Base class for all custom exceptions in this application."""
    pass


# --- Authentication / Authorization ---
class AuthenticationError(RPMSystemError):
    """Raised when login credentials are invalid."""
    pass


class AuthorizationError(RPMSystemError):
    """Raised when a user tries to access a resource outside their role."""
    pass


class SessionExpiredError(RPMSystemError):
    """Raised when a user's session has expired and they must re-authenticate."""
    pass


# --- Database Layer ---
class DatabaseConnectionError(RPMSystemError):
    """Raised when the application cannot connect to MySQL."""
    pass


class RecordNotFoundError(RPMSystemError):
    """Raised when a query expects a record (e.g., by ID) that doesn't exist."""
    pass


class DuplicateRecordError(RPMSystemError):
    """Raised when attempting to create a record that violates a uniqueness
    constraint (e.g., registering an email that's already in use)."""
    pass


# --- Validation ---
class ValidationError(RPMSystemError):
    """Raised when user-submitted data fails validation rules
    (e.g., an out-of-range blood pressure reading)."""
    pass


# --- Machine Learning Layer ---
class ModelNotLoadedError(RPMSystemError):
    """Raised when a prediction is requested but the trained model
    file could not be found/loaded from disk."""
    pass


class PredictionError(RPMSystemError):
    """Raised when the ML pipeline fails during inference
    (e.g., malformed feature vector)."""
    pass
