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
