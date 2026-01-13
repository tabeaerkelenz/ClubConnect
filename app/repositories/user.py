from typing import Any, Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SASession

from app.models.models import User, UserRole
from app.exceptions.base import EmailExistsError


class UserRepository:
    def __init__(self, db: SASession):
        self.db = db

    # --- basic loaders ---

    def get(self, user_id: int) -> User | None:
        """Return user by id or None."""
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        """Return user by email or None."""
        stmt = select(User).where(User.email == email)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    # --- listing ---

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        roles: Sequence[UserRole] | None = None,
    ) -> list[User]:
        """List users with optional role filter and pagination."""
        stmt = select(User)

        if q:
            stmt = stmt.where(User.name.contains(q, autoescape=True))
        if roles:
            stmt = stmt.where(User.role.in_(list(roles)))

        stmt = stmt.order_by(User.name.asc()).offset(skip).limit(limit)

        result = self.db.execute(stmt)
        return list(result.scalars().all())

    # --- helpers ---

    def _commit_with_email_guard(self, user: User) -> User:
        """Commit and refresh user, mapping unique email errors."""
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            orig = getattr(e, "orig", None)

            # ---- Postgres: unique_violation ----
            if hasattr(orig, "pgcode") and orig.pgcode == "23505":
                constraint = getattr(getattr(orig, "diag", None), "constraint_name", None)
                if constraint == "users_email_key":
                    raise EmailExistsError from e

            # ---- SQLite: UNIQUE constraint failed: users.email ----
            msg = str(orig) if orig is not None else str(e)
            if "UNIQUE constraint failed" in msg and "users.email" in msg:
                raise EmailExistsError from e

            raise
        self.db.refresh(user)
        return user

    # --- create & update ---

    def create_user(self, **kwargs: Any) -> User:
        """Create a new user."""
        user = User(**kwargs)
        self.db.add(user)
        return self._commit_with_email_guard(user)

    def update_fields(self, user: User, updates: Mapping[str, Any]) -> User:
        """Apply partial updates to a user and persist."""
        for field, value in updates.items():
            setattr(user, field, value)
        self.db.add(user)
        return self._commit_with_email_guard(user)

    def set_active(self, user: User, is_active: bool) -> User:
        """Toggle is_active and persist."""
        user.is_active = is_active
        self.db.add(user)
        return self._commit_with_email_guard(user)

    # --- delete ---

    def delete_user(self, user: User) -> None:
        """Delete an existing user."""
        self.db.delete(user)
        self.db.commit()
