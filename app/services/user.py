from typing import Any, Mapping, Sequence

from app.core.security import hash_password, verify_password
from app.exceptions.base import UserNotFoundError, EmailExistsError, \
    IncorrectPasswordError  # and maybe InvalidCredentialsError later
from app.models.models import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


FORBIDDEN_UPDATE_FIELDS = {
    "is_active",
    "role",
    "password",
    "password_hash",
    "id",
    "created_at",
    "updated_at",
}


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    # --- helpers ---

    @staticmethod
    def _normalize_email(raw: str | None) -> str | None:
        if raw is None:
            return None
        return raw.strip().lower()

    @staticmethod
    def _normalize_name(raw: str | None) -> str | None:
        if raw is None:
            return None
        return raw.strip()

    def _normalize_update_payload(self, payload: UserUpdate) -> dict[str, Any]:
        data = payload.model_dump(exclude_unset=True)

        # strip forbidden fields defensively
        for f in list(data.keys()):
            if f in FORBIDDEN_UPDATE_FIELDS:
                data.pop(f, None)

        # normalize email if present
        if "email" in data:
            data["email"] = self._normalize_email(data["email"])

        # normalize name if present
        if "name" in data:
            data["name"] = self._normalize_name(data["name"])

        return data

    def _assert_unique_email_if_changed(self, me: User, data: Mapping[str, Any]) -> None:
        new_email = data.get("email")
        if not new_email or new_email == me.email:
            return

        # ask repo whether anyone already uses this email
        existing = self.repo.get_by_email(new_email)
        if existing is not None and existing.id != me.id:
            raise EmailExistsError

    # --- core operations ---

    def get_user(self, user_id: int) -> User:
        """Return user or raise UserNotFoundError."""
        user = self.repo.get(user_id)
        if user is None:
            raise UserNotFoundError()
        return user

    def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        roles: Sequence[UserRole] | None = None,
    ) -> list[User] | None:
        """List users with optional search + role filter."""
        skip = max(0, skip)
        limit = max(1, min(limit, 50))

        q_norm = (q or "").strip() or None

        users = self.repo.list(skip=skip, limit=limit, q=q_norm, roles=roles)
        return users


    def create_user(self, user_create: UserCreate) -> User:
        """
        Create a new user:
        - normalize email/name
        - hash password
        - delegate to repo.create_user
        """
        email = self._normalize_email(user_create.email)
        name = self._normalize_name(user_create.name)
        password_hash = hash_password(user_create.password)

        user = self.repo.create_user(
            email=email,
            name=name,
            password_hash=password_hash,
            role=UserRole.athlete,
            is_active=False
        )
        return user

    def update_me(self, me: User, payload: UserUpdate) -> User:
        """
        Update limited, user-controlled fields for the authenticated user.
        - forbids role/is_active/password changes here
        - validates unique email on change
        """
        data = self._normalize_update_payload(payload)
        self._assert_unique_email_if_changed(me, data)

        updated_user = self.repo.update_fields(me, data)

        return updated_user

    def activate_user(self, user_id: int) -> User:
        """Set is_active=True for the given user."""
        user = self.repo.get(user_id)
        if user is None:
            raise UserNotFoundError()
        return self.repo.set_active(user, True)

    def deactivate_user(self, user_id: int) -> User:
        """Set is_active=False for the given user."""
        user = self.repo.get(user_id)
        if user is None:
            raise UserNotFoundError()
        return self.repo.set_active(user, False)

    def authenticate(self, email: str, password: str) -> User | None:
        """
        Return User if credentials are valid, otherwise None.
        (Optionally you could raise a domain error instead.)
        """
        email_norm = self._normalize_email(email)
        if not email_norm:
            return None

        user = self.repo.get_by_email(email_norm)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user


    def change_password(self, user: User, old_password: str, new_password: str) -> User:
        """
        Change the password for the given user.
        - verifies old_password
        - sets new password hash
        - persists via repository
        """
        if not user.check_password(old_password):
            raise IncorrectPasswordError()

        new_hash = hash_password(new_password)

        return self.repo.update_fields(user, {"password_hash": new_hash})