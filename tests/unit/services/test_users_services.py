from unittest.mock import MagicMock

import pytest

from app.core.security import hash_password
from app.exceptions.base import (
    UserNotFoundError,
    EmailExistsError,
    IncorrectPasswordError
)
from app.models.models import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.services.user import UserService


@pytest.fixture
def mock_user_repo() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_user_repo: MagicMock) -> UserService:
    return UserService(repo=mock_user_repo)


def make_user(
    user_id: int = 1,
    name: str = "Alice",
    email: str = "alice@example.com",
    role: UserRole | None = None,
    is_active: bool = True,
    raw_password: str = "pw123",  # default raw password
) -> User:
    return User(
        id=user_id,
        name=name,
        email=email,
        password_hash=hash_password(raw_password),
        role=role or list(UserRole)[0],
        is_active=is_active,
    )


# --- get_user ---


def test_get_user_happy_path(user_service: UserService, mock_user_repo: MagicMock):
    user = make_user(user_id=123)
    mock_user_repo.get.return_value = user

    result = user_service.get_user(123)

    assert result is user
    mock_user_repo.get.assert_called_once_with(123)


def test_get_user_not_found_raises(user_service: UserService, mock_user_repo: MagicMock):
    mock_user_repo.get.return_value = None

    with pytest.raises(UserNotFoundError):
        user_service.get_user(999)

    mock_user_repo.get.assert_called_once_with(999)


# --- list_users ---


def test_list_users_normalizes_q_and_passes_to_repo(user_service: UserService, mock_user_repo: MagicMock):
    mock_user_repo.list.return_value = []

    result = user_service.list_users(skip=0, limit=10, q="  Alice  ")

    assert result == []
    _, kwargs = mock_user_repo.list.call_args
    assert kwargs["skip"] == 0
    assert kwargs["limit"] == 10
    # normalized q
    assert kwargs["q"] == "Alice"
    assert kwargs["roles"] is None


def test_list_users_whitespace_q_becomes_none(user_service: UserService, mock_user_repo: MagicMock):
    mock_user_repo.list.return_value = []

    result = user_service.list_users(skip=0, limit=10, q="   ")

    assert result == []
    _, kwargs = mock_user_repo.list.call_args
    assert kwargs["skip"] == 0
    assert kwargs["limit"] == 10
    assert kwargs["q"] is None


# --- create_user ---


def test_create_user_normalizes_and_hashes_password(user_service: UserService, mock_user_repo: MagicMock):
    user_create = UserCreate(
        name="  Alice  ",
        email="  ALICE@EXAMPLE.COM  ",
        password="pw123456",
    )
    fake_user = make_user(name="Alice", email="alice@example.com")
    mock_user_repo.create_user.return_value = fake_user

    result = user_service.create_user(user_create)

    assert result is fake_user
    mock_user_repo.create_user.assert_called_once()
    _, kwargs = mock_user_repo.create_user.call_args

    # name and email normalized
    assert kwargs["name"] == "Alice"
    assert kwargs["email"] == "alice@example.com"

    # password_hash exists and is not the plain password
    assert "password_hash" in kwargs
    assert kwargs["password_hash"] != user_create.password

    # we don't care which role/is_active exactly, only that they are present
    assert "role" in kwargs
    assert "is_active" in kwargs


def test_create_user_propagates_email_exists_error(user_service: UserService, mock_user_repo: MagicMock):
    user_create = UserCreate(
        name="Bob",
        email="bob@example.com",
        password="pw_with_8_chars",
    )
    mock_user_repo.create_user.side_effect = EmailExistsError

    with pytest.raises(EmailExistsError):
        user_service.create_user(user_create)


# --- update_me ---


def test_update_me_happy_path_calls_repo_with_normalized_data(
    user_service: UserService, mock_user_repo: MagicMock
):
    me = make_user(email="old@example.com")
    payload = UserUpdate(
        name="  New Name  ",
        email="  NEW@EXAMPLE.COM  ",
    )

    mock_user_repo.get_by_email.return_value = None  # no conflict
    updated = make_user(name="New Name", email="new@example.com")
    mock_user_repo.update_fields.return_value = updated

    result = user_service.update_me(me, payload)

    assert result is updated
    mock_user_repo.get_by_email.assert_called_once_with("new@example.com")
    mock_user_repo.update_fields.assert_called_once()
    args, kwargs = mock_user_repo.update_fields.call_args

    # first positional arg should be 'me'
    assert args[0] is me

    updates = args[1]
    assert updates["name"] == "New Name"
    assert updates["email"] == "new@example.com"


def test_update_me_raises_when_email_taken(
    user_service: UserService, mock_user_repo: MagicMock
):
    me = make_user(user_id=1, email="old@example.com")
    payload = UserUpdate(email="new@example.com")

    other_user = make_user(user_id=2, email="new@example.com")
    mock_user_repo.get_by_email.return_value = other_user

    with pytest.raises(EmailExistsError):
        user_service.update_me(me, payload)


# --- authenticate ---


def test_authenticate_returns_user_on_valid_credentials(
    user_service: UserService,
    mock_user_repo: MagicMock,
):
    # user created with raw_password="pw123" by default
    user = make_user(email="user@example.com", raw_password="pw123")
    mock_user_repo.get_by_email.return_value = user

    result = user_service.authenticate(email="  USER@example.com  ", password="pw123")

    assert result is user
    mock_user_repo.get_by_email.assert_called_once_with("user@example.com")


def test_authenticate_returns_none_if_user_not_found(user_service: UserService, mock_user_repo: MagicMock):
    mock_user_repo.get_by_email.return_value = None

    result = user_service.authenticate(email="missing@example.com", password="x")
    assert result is None


def test_authenticate_returns_none_if_password_invalid(user_service: UserService, mock_user_repo: MagicMock, monkeypatch: pytest.MonkeyPatch):
    user = make_user(email="user@example.com")
    mock_user_repo.get_by_email.return_value = user

    from app.core import security as security_mod
    monkeypatch.setattr(security_mod, "verify_password", lambda pw, hash_: False)

    result = user_service.authenticate(email="user@example.com", password="wrong")
    assert result is None


# --- activate / deactivate ---


def test_activate_user_happy_path(user_service: UserService, mock_user_repo: MagicMock):
    user = make_user(is_active=False)
    mock_user_repo.get.return_value = user
    mock_user_repo.set_active.return_value = user  # simulate repo return

    result = user_service.activate_user(user_id=1)

    assert result is user
    mock_user_repo.get.assert_called_once_with(1)
    mock_user_repo.set_active.assert_called_once_with(user, True)


def test_activate_user_not_found_raises(user_service: UserService, mock_user_repo: MagicMock):
    mock_user_repo.get.return_value = None

    with pytest.raises(UserNotFoundError):
        user_service.activate_user(user_id=999)

    mock_user_repo.get.assert_called_once_with(999)


def test_deactivate_user_happy_path(user_service: UserService, mock_user_repo: MagicMock):
    user = make_user(is_active=True)
    mock_user_repo.get.return_value = user
    mock_user_repo.set_active.return_value = user

    result = user_service.deactivate_user(user_id=1)

    assert result is user
    mock_user_repo.get.assert_called_once_with(1)
    mock_user_repo.set_active.assert_called_once_with(user, False)


# --- change_password (if implemented) ---


def test_change_password_happy_path(user_service: UserService, mock_user_repo: MagicMock, monkeypatch: pytest.MonkeyPatch):
    user = make_user()
    # fake check_password for this user
    def fake_check(pw: str) -> bool:
        return pw == "oldpw"

    user.check_password = fake_check  # monkeypatch the instance method

    mock_user_repo.update_fields.return_value = user

    result = user_service.change_password(user=user, old_password="oldpw", new_password="newpw")

    assert result is user
    mock_user_repo.update_fields.assert_called_once()
    args, kwargs = mock_user_repo.update_fields.call_args

    assert args[0] is user
    assert args[1] == {}  # or whatever you decided to pass as updates


def test_change_password_incorrect_old_raises(user_service: UserService, mock_user_repo: MagicMock):
    user = make_user()

    def fake_check(pw: str) -> bool:
        return False

    user.check_password = fake_check

    with pytest.raises(IncorrectPasswordError):
        user_service.change_password(user=user, old_password="wrong", new_password="newpw")

    mock_user_repo.update_fields.assert_not_called()
