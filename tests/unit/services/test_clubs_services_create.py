import pytest
from unittest.mock import MagicMock

from app.schemas.club import ClubCreate, ClubUpdate
from app.schemas.membership import MembershipCreate
from app.services.club import ClubService
from app.repositories.club import ClubRepository
from app.exceptions.base import ClubNotFoundError, DuplicateSlugError
from app.models.models import Club, User, MembershipRole


# Fixtures
@pytest.fixture
def mock_club_repo() -> MagicMock:
    """Fixture for mocking ClubRepository."""
    return MagicMock(spec=ClubRepository)

@pytest.fixture
def club_service(mock_club_repo: MagicMock) -> ClubService:
    """Fixture for ClubService with mocked ClubRepository."""
    return ClubService(club_repo=mock_club_repo)

@pytest.fixture
def mock_user() -> User:
    """Fixture for a mock User."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "owner@example.com"
    return user


# create_club_and_owner tests
def test_create_club_and_owner_success(club_service: ClubService, mock_club_repo: MagicMock, mock_user: User) -> None:
    # Arrange
    club_create = ClubCreate(name="Test Club", country="DE")
    membership_create = MembershipCreate(
        email=mock_user.email,
        role=MembershipRole.owner,
    )

    mock_club = MagicMock(spec=Club, id=123, name="Test Club")
    mock_membership = MagicMock()

    mock_club_repo.create_club.return_value = mock_club
    mock_club_repo.add_membership.return_value = mock_membership

    # Act
    club, owner_membership = club_service.create_club_and_owner(club_create=club_create, membership_create=membership_create, user=mock_user)

    # Assert
    mock_club_repo.create_club.assert_called_once_with(name="Test Club", country="DE", slug="test-club-de")

    mock_club_repo.add_membership.assert_called_once_with(
        user_id=mock_user.id,
        club_id=mock_club.id,
        role=membership_create.role,
    )

    assert club is mock_club
    assert owner_membership is mock_membership


# Negative test: DuplicateSlugError during club creation
def test_create_club_duplicate_slug(
    club_service: ClubService,
    mock_club_repo: MagicMock,
    mock_user: User,
):
    # Arrange
    club_create = ClubCreate(name="Existing Club", country="DE")
    membership_create = MembershipCreate(
        email=mock_user.email,
        role=MembershipRole.owner,
    )

    mock_club_repo.create_club.side_effect = DuplicateSlugError("Club already exist.")

    # Act & Assert
    with pytest.raises(DuplicateSlugError, match="Club already exist."):
        club_service.create_club_and_owner(club_create, membership_create, user=mock_user)

    # membership should not be created if club creation fails
    mock_club_repo.add_membership.assert_not_called()


def test_get_club_success(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    club_id = 42
    mock_club = MagicMock(spec=Club, id=club_id, name="Test Club")
    mock_club_repo.get_club.return_value = mock_club

    # Act
    result = club_service.get_club_service(club_id=club_id)

    # Assert
    mock_club_repo.get_club.assert_called_once_with(club_id)
    assert result is mock_club


def test_get_club_not_found(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    club_id = 999
    mock_club_repo.get_club.return_value = None

    # Act & Assert
    with pytest.raises(ClubNotFoundError):
        club_service.get_club_service(club_id=club_id)

    mock_club_repo.get_club.assert_called_once_with(club_id)


def test_get_my_clubs_success(
    club_service: ClubService,
    mock_club_repo: MagicMock,
    mock_user: User,
):
    # Arrange
    mock_clubs = [
        MagicMock(spec=Club, id=1, name="Club A"),
        MagicMock(spec=Club, id=2, name="Club B"),
    ]
    mock_club_repo.get_clubs_by_user.return_value = mock_clubs

    # Act
    result = club_service.get_my_clubs_service(user=mock_user)

    # Assert
    mock_club_repo.get_clubs_by_user.assert_called_once_with(mock_user.id)
    assert result == mock_clubs


def test_list_clubs_success(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    mock_clubs = [
        MagicMock(spec=Club, id=1, name="Club A"),
        MagicMock(spec=Club, id=2, name="Club B"),
    ]
    mock_club_repo.list_clubs.return_value = mock_clubs

    # Act
    result = club_service.list_clubs_service(skip=0, limit=10, q=None)

    # Assert
    mock_club_repo.list_clubs.assert_called_once_with(skip=0, limit=10, q=None)
    assert result == mock_clubs


def test_list_clubs_with_query(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    mock_clubs = [
        MagicMock(spec=Club, id=1, name="Soccer Club"),
        MagicMock(spec=Club, id=2, name="Soccer Club"),
    ]
    mock_club_repo.list_clubs.return_value = mock_clubs

    # Act
    result = club_service.list_clubs_service(skip=0, limit=10, q="Soccer")

    # Assert
    mock_club_repo.list_clubs.assert_called_once()
    args, kwargs = mock_club_repo.list_clubs.call_args

    assert result == mock_clubs
    assert args == ()
    assert kwargs == {"skip": 0, "limit": 10, "q": "Soccer"}


def test_list_clubs_limit_bounds(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    mock_clubs = []
    mock_club_repo.list_clubs.return_value = mock_clubs

    # Act
    result = club_service.list_clubs_service(skip=0, limit=500, q=None)

    # Assert
    mock_club_repo.list_clubs.assert_called_once()
    args, kwargs = mock_club_repo.list_clubs.call_args

    assert result == mock_clubs
    assert args == ()
    assert kwargs == {"skip": 0, "limit": 200, "q": None}


def test_list_clubs_with_negative_skip(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    mock_clubs = []
    mock_club_repo.list_clubs.return_value = mock_clubs

    # Act
    result = club_service.list_clubs_service(skip=-10, limit=10, q=None)

    # Assert
    mock_club_repo.list_clubs.assert_called_once()
    args, kwargs = mock_club_repo.list_clubs.call_args

    assert result == mock_clubs
    assert args == ()
    assert kwargs == {"skip": 0, "limit": 10, "q": None}


def test_list_clubs_with_query_wide_spaces(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    mock_clubs = []
    mock_club_repo.list_clubs.return_value = mock_clubs

    # Act
    result = club_service.list_clubs_service(skip=0, limit=10, q="   ")

    # Assert
    mock_club_repo.list_clubs.assert_called_once()
    args, kwargs = mock_club_repo.list_clubs.call_args

    assert result == mock_clubs
    assert args == ()
    assert kwargs == {"skip": 0, "limit": 10, "q": None}


# update_club_service tests
def test_update_club_success(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    club_id = 42
    club_update = ClubUpdate(name="Updated Club Name")
    mock_club = MagicMock(spec=Club, id=club_id, name="Old Club Name", country="DE", city="Berlin", sport="Soccer")
    updated_club = MagicMock(spec=Club, id=club_id, name="Updated Club Name")

    mock_club_repo.get_club.return_value = mock_club
    mock_club_repo.update_club.return_value = updated_club

    # Act
    result = club_service.update_club_service(user=None, club_id=club_id, club_update=club_update)

    # Assert
    mock_club_repo.get_club.assert_called_once_with(club_id)
    mock_club_repo.update_club.assert_called_once()
    args, kwargs = mock_club_repo.update_club.call_args

    assert args[0] == mock_club
    assert kwargs["name"] == "Updated Club Name"
    assert "slug" in kwargs
    assert kwargs["slug"] == "updated-club-name-de-berlin-soccer"
    assert result is updated_club


def test_update_club_not_found(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    club_id = 999
    club_update = ClubUpdate(name="Updated Club Name")
    mock_club_repo.get_club.return_value = None

    # Act & Assert
    with pytest.raises(ClubNotFoundError):
        club_service.update_club_service(user=None, club_id=club_id, club_update=club_update)

    mock_club_repo.update_club.assert_not_called()


def test_update_duplicate_slug(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    club_id = 42
    club_update = ClubUpdate(name="Duplicate Slug Name")
    mock_club = MagicMock(spec=Club, id=club_id, name="Old Club Name", country="DE", city="Berlin", sport="Soccer")

    mock_club_repo.get_club.return_value = mock_club
    mock_club_repo.update_club.side_effect = DuplicateSlugError("Club with this slug already exists.")

    # Act & Assert
    with pytest.raises(DuplicateSlugError, match="Club with this slug already exists."):
        club_service.update_club_service(user=None, club_id=club_id, club_update=club_update)

    mock_club_repo.get_club.assert_called_once()
    args, kwargs = mock_club_repo.update_club.call_args

    assert args[0] == mock_club
    assert kwargs["name"] == "Duplicate Slug Name"
    assert "slug" in kwargs
    assert kwargs["slug"] == "duplicate-slug-name-de-berlin-soccer"


# delete_club_service tests
def test_delete_club_success(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    club_id = 42
    mock_club = MagicMock(spec=Club, id=club_id)
    mock_club_repo.get_club.return_value = mock_club

    # Act
    result = club_service.delete_club_service(club_id=club_id)

    # Assert
    mock_club_repo.get_club.assert_called_once_with(club_id)
    mock_club_repo.delete_club.assert_called_once_with(mock_club)
    assert result is None


def test_delete_club_not_found(
    club_service: ClubService,
    mock_club_repo: MagicMock,
):
    # Arrange
    mock_club_repo.get_club.return_value = None

    # Act & Assert
    with pytest.raises(ClubNotFoundError):
        club_service.delete_club_service(club_id=999)

    mock_club_repo.delete_club.assert_not_called()
