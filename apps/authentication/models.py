"""Re-export the User model so Django can find it via AUTH_USER_MODEL."""
from authentication.infrastructure.repositories.models import User  # noqa: F401
