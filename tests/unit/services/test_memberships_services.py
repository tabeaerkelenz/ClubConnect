import pytest
from unittest.mock import MagicMock

from app.services.membership import MembershipService
from app.repositories.membership import MembershipRepository
from app.repositories.user import UserRepository
from app.repositories.club import ClubRepository
from app.models.models import MembershipRole
from app.exceptions.base import (
    UserNotFoundError,
    ClubNotFoundError,
    MembershipExistsError,
    LastCoachViolationError,
    NotClubMember,
    CoachRequiredError,
    CoachOrOwnerRequiredError
)
from .factories import make_user, make_club, make_membership


# --- fixtures ---
@pytest.fixture
def mock_membership_repo() -> MagicMock:
    return MagicMock(spec=MembershipRepository)


@pytest.fixture
def mock_user_repo() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_club_repo() -> MagicMock:
    return MagicMock(spec=ClubRepository)


@pytest.fixture
def membership_service(mock_membership_repo, mock_user_repo, mock_club_repo) -> MembershipService:
    return MembershipService(
        membership_repo=mock_membership_repo,
        user_repo=mock_user_repo,
        club_repo=mock_club_repo,
    )


# --- tests ---

# --- add member ---
def test_add_member_by_email_normalizes_email_and_creates_membership(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
    mock_user_repo: MagicMock,
    mock_club_repo: MagicMock,
):
    # Arrange
    user = make_user()
    club_id = 10
    club = make_club(club_id=club_id, name="Test Club")

    existing_membership = None
    created_membership = make_membership(
        membership_id=1, club_id=club_id, user_id=user.id, role=MembershipRole.coach
    )

    mock_user_repo.get_by_email.return_value = user
    mock_club_repo.get_club.return_value = club
    mock_membership_repo.get_by_club_and_user.return_value = existing_membership
    mock_membership_repo.create.return_value = created_membership

    # Act
    result = membership_service.add_member_by_email(
        club_id=club_id,
        email="  User@Example.com  ",  # uppercase + spaces
        role=MembershipRole.coach,
    )

    # Assert
    assert result is created_membership

    # email should be normalized for lookup
    mock_user_repo.get_by_email.assert_called_once_with("user@example.com")

    # check that we looked for existing membership using the user.id
    mock_membership_repo.get_by_club_and_user.assert_called_once_with(
        club_id=club_id,
        user_id=user.id,
    )

    # check that we created the correct membership
    mock_membership_repo.create.assert_called_once_with(
        club_id=club_id,
        user_id=user.id,
        role=MembershipRole.coach,
    )


def test_add_member_by_email_raises_UserNotFound_if_email_unknown(
    membership_service: MembershipService,
    mock_user_repo: MagicMock,
    mock_club_repo: MagicMock,
    mock_membership_repo: MagicMock,
):
    # Arrange
    mock_user_repo.get_by_email.return_value = None

    # Act / Assert
    with pytest.raises(UserNotFoundError):
        membership_service.add_member_by_email(
            club_id=1,
            email="test-mail@example.com",
            role=MembershipRole.member,
)


def test_add_member_by_email_raises_MembershipExists_if_already_member(
    membership_service: MembershipService,
    mock_user_repo: MagicMock,
    mock_club_repo: MagicMock,
    mock_membership_repo: MagicMock,
):
    # Arrange
    user = make_user(user_id=1, email="example@mail.com")
    club = make_club(club_id=1, name="Test Club")
    existing_membership = make_membership(membership_id=1, club_id=club.id, user_id=user.id, role=MembershipRole.member)

    mock_user_repo.get_by_email.return_value = user
    mock_club_repo.get_club.return_value = club
    mock_membership_repo.get_by_club_and_user.return_value = existing_membership

    # Act / Assert
    with pytest.raises(MembershipExistsError):
        membership_service.add_member_by_email(
            club_id=club.id,
            email=user.email,
            role=MembershipRole.member,
        )

    mock_membership_repo.create.assert_not_called()


def test_add_member_by_email_raises_ClubNotFound_if_club_unknown(
    membership_service: MembershipService,
    mock_user_repo: MagicMock,
    mock_club_repo: MagicMock,
    mock_membership_repo: MagicMock,
):
    # Arrange
    user = make_user(user_id=1, email="test@user.com")
    mock_user_repo.get_by_email.return_value = user
    mock_club_repo.get_club.return_value = None  # club not found

    # Act / Assert
    with pytest.raises(ClubNotFoundError):
        membership_service.add_member_by_email(
            club_id=999,  # non-existent club
            email=user.email,
            role=MembershipRole.member,
        )

    mock_membership_repo.create.assert_not_called()


# --- change role / remove member happy paths ---
def test_change_role_allows_demote_if_other_leaders_exist(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    club_id = 1
    membership_id = 10

    membership = make_membership(
        membership_id=membership_id,
        club_id=club_id,
        user_id=42,
        role=MembershipRole.coach,
    )
    updated_membership = make_membership(
        membership_id=membership_id,
        club_id=club_id,
        user_id=42,
        role=MembershipRole.member,
    )

    mock_membership_repo.get.return_value = membership
    mock_membership_repo.count_coach_owner.return_value = 1  # another coach/owner exists
    mock_membership_repo.update_role.return_value = updated_membership

    # Act
    result = membership_service.change_role(
        club_id=club_id,
        membership_id=membership_id,
        new_role=MembershipRole.member,
    )

    # Assert
    assert result is updated_membership
    mock_membership_repo.count_coach_owner.assert_called_once()
    mock_membership_repo.update_role.assert_called_once_with(
        membership,
        MembershipRole.member,
    )


def test_remove_member_allows_delete_leader_if_other_exists(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    club_id = 1
    membership_id = 10

    membership = make_membership(
        membership_id=membership_id,
        club_id=club_id,
        user_id=42,
        role=MembershipRole.coach,
    )

    mock_membership_repo.get.return_value = membership
    mock_membership_repo.count_coach_owner.return_value = 1  # another coach/owner exists

    # Act
    membership_service.remove_member(
        club_id=club_id,
        membership_id=membership_id,
    )

    # Assert
    mock_membership_repo.count_coach_owner.assert_called_once()
    mock_membership_repo.delete.assert_called_once_with(membership)



# --- change role / remove member last coach/owner guard ---
def test_change_role_prevents_last_coach_violation(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    club_id = 1
    membership_id = 10
    new_role = MembershipRole.member

    membership = make_membership(
        membership_id=membership_id,
        club_id=club_id,
        user_id=42,
        role=MembershipRole.coach,
    )

    mock_membership_repo.get.return_value = membership
    mock_membership_repo.count_coach_owner.return_value = 0  # no other coaches/owners

    # Act / Assert
    with pytest.raises(LastCoachViolationError):
        membership_service.change_role(
            club_id=club_id,
            membership_id=membership_id,
            new_role=new_role,
        )

    mock_membership_repo.update_role.assert_not_called()


def test_remove_member_prevents_last_coach_owner_violation(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    club_id = 1
    membership_id = 10

    membership = make_membership(
        membership_id=membership_id,
        club_id=club_id,
        user_id=42,
        role=MembershipRole.coach,
    )

    mock_membership_repo.get.return_value = membership
    mock_membership_repo.count_coach_owner.return_value = 0  # no other coaches/owners

    # Act / Assert
    with pytest.raises(LastCoachViolationError):
        membership_service.remove_member(
            club_id=club_id,
            membership_id=membership_id,
        )

    mock_membership_repo.delete.assert_not_called()


# --- require_coach_of_club ---
def test_require_coach_of_club_raises_NotClubMember_when_no_membership(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    user_id = 42
    club_id = 1

    mock_membership_repo.get_by_club_and_user.return_value = None  # no membership

    # Act / Assert
    with pytest.raises(NotClubMember):
        membership_service.require_coach_of_club(
            user_id=user_id,
            club_id=club_id,
        )

def test_require_coach_of_club_raises_CoachRequiredError_when_not_coach(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    user_id = 42
    club_id = 1

    membership = make_membership(
        membership_id=1,
        club_id=club_id,
        user_id=user_id,
        role=MembershipRole.member,  # not a coach
    )

    mock_membership_repo.get_by_club_and_user.return_value = membership

    # Act / Assert
    with pytest.raises(CoachRequiredError):
        membership_service.require_coach_of_club(
            user_id=user_id,
            club_id=club_id,
        )


# --- require-member-of-club ---
def test_require_member_of_club_raises_NotClubMember_when_missing(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    user_id = 42
    club_id = 1
    mock_membership_repo.get_by_club_and_user.return_value = None

    # Act / Assert
    with pytest.raises(NotClubMember):
        membership_service.require_member_of_club(
            user_id=user_id,
            club_id=club_id,
        )


@pytest.mark.parametrize("role", [MembershipRole.member, MembershipRole.coach, MembershipRole.owner]) # test all roles, runs tests three times on each different role
def test_require_member_of_club_returns_membership_for_any_role(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
    role: MembershipRole,
):
    # Arrange
    user_id = 42
    club_id = 1

    membership = make_membership(
        membership_id=1,
        club_id=club_id,
        user_id=user_id,
        role=role,
    )
    mock_membership_repo.get_by_club_and_user.return_value = membership

    # Act
    result = membership_service.require_member_of_club(
        user_id=user_id,
        club_id=club_id,
    )

    # Assert
    assert result is membership


# --- require_coach_or_owner_of_club ---
def test_require_coach_or_owner_of_club_raises_NotClubMember_when_missing(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    user_id = 42
    club_id = 1
    mock_membership_repo.get_by_club_and_user.return_value = None

    # Act / Assert
    with pytest.raises(NotClubMember):
        membership_service.require_coach_or_owner_of_club(
            user_id=user_id,
            club_id=club_id,
        )


def test_require_coach_or_owner_of_club_raises_CoachOrOwnerRequired_when_member_only(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
):
    # Arrange
    user_id = 42
    club_id = 1
    membership = make_membership(
        membership_id=1,
        club_id=club_id,
        user_id=user_id,
        role=MembershipRole.member,
    )
    mock_membership_repo.get_by_club_and_user.return_value = membership

    # Act / Assert
    with pytest.raises(CoachOrOwnerRequiredError):
        membership_service.require_coach_or_owner_of_club(
            user_id=user_id,
            club_id=club_id,
        )


@pytest.mark.parametrize("role", [MembershipRole.coach, MembershipRole.owner]) # test both coach and owner roles
def test_require_coach_or_owner_of_club_returns_membership_for_leaders(
    membership_service: MembershipService,
    mock_membership_repo: MagicMock,
    role: MembershipRole,
):
    # Arrange
    user_id = 42
    club_id = 1
    membership = make_membership(
        membership_id=1,
        club_id=club_id,
        user_id=user_id,
        role=role,
    )
    mock_membership_repo.get_by_club_and_user.return_value = membership

    # Act
    result = membership_service.require_coach_or_owner_of_club(
        user_id=user_id,
        club_id=club_id,
    )

    # Assert
    assert result is membership
