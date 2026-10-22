
"""Application service for user-related operations."""

from app.domain.models import User


def prepare_user(username: str) -> User:
    """Validate and prepare a new user for application use.

    Args:
        username: The desired username.

    Returns:
        A validated User instance that has not yet been persisted.

    Raises:
        ValueError: If the username is empty or contains only whitespace.
    """
    normalized_username = username.strip()

    if not normalized_username:
        raise ValueError("Username must not be empty.")

    return User(username=normalized_username)
