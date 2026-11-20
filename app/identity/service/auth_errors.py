class AuthenticationError(Exception):
    """Raised when supplied login credentials are invalid."""


class AuthorizationError(Exception):
    """Raised when a user does not have a valid active session."""


class UserAlreadyExistsError(Exception):
    """Raised when registration uses an email that is already registered."""