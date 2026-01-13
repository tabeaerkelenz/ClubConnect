from unittest.mock import MagicMock

import pytest

from app.exceptions.base import GroupNotFoundError
from app.repositories.group import GroupRepository
from app.schemas.group import GroupCreate, GroupUpdate
from app.services.group import GroupService
from app.services.membership import MembershipService
from .factories import make_user, make_club, make_membership
from app.models.models import MembershipRole


@pytest.fixture
def mock_group_repo() -> MagicMock:
    return MagicMock(spec=GroupRepository)


@pytest.fixture
def mock_membership_service() -> MagicMock:
    return MagicMock(spec=MembershipService)


@pytest.fixture
def group_service(mock_group_repo: MagicMock, mock_membership_service: MagicMock) -> GroupService:
    return GroupService(group_repo=mock_group_repo, membership_service=mock_membership_service)


def test_create_group_happy_path(
    group_service: GroupService,
    mock_group_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange (domain context)
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")
    mock_membership_service.require_coach_or_owner_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.coach
    )

    data = GroupCreate(name="Team A", description="A valid description...")
    fake_group = MagicMock()
    fake_group.id = 5
    fake_group.club_id = club.id
    fake_group.name = data.name
    fake_group.description = data.description
    fake_group.created_by_id = actor.id
    mock_group_repo.create.return_value = fake_group

    # Act
    result = group_service.create(actor_id=actor.id, club_id=club.id, data=data)

    # Assert
    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(actor.id, club.id)
    mock_group_repo.create.assert_called_once_with(
        club_id=club.id,
        name=data.name,
        description=data.description,
        created_by_id=actor.id,
    )
    assert result is fake_group


def test_list_groups_requires_member(
    group_service: GroupService,
    mock_group_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")

    mock_membership_service.require_member_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.member
    )
    mock_group_repo.list.return_value = []

    group_service.list(actor_id=actor.id, club_id=club.id, q=None, offset=0, limit=10)

    mock_membership_service.require_member_of_club.assert_called_once_with(actor.id, club.id)
    mock_group_repo.list.assert_called_once_with(club_id=club.id, q=None, offset=0, limit=10)


def test_get_group_propagates_repo_error(
    group_service: GroupService,
    mock_group_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")

    mock_membership_service.require_member_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.member
    )
    mock_group_repo.get_by_id.side_effect = GroupNotFoundError()

    with pytest.raises(GroupNotFoundError):
        group_service.get(actor_id=actor.id, club_id=club.id, group_id=999)

    mock_membership_service.require_member_of_club.assert_called_once_with(actor.id, club.id)
    mock_group_repo.get_by_id.assert_called_once_with(club_id=club.id, group_id=999)


def test_update_group_requires_coach_or_owner(
    group_service: GroupService,
    mock_group_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")

    mock_membership_service.require_coach_or_owner_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.owner
    )

    data = GroupUpdate(name="New name", description=None)
    mock_group_repo.update.return_value = MagicMock()

    group_service.update(actor_id=actor.id, club_id=club.id, group_id=5, data=data)

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(actor.id, club.id)
    mock_group_repo.update.assert_called_once_with(
        club_id=club.id,
        group_id=5,
        name="New name",
        description=None,
    )


def test_delete_group_requires_coach_or_owner(
    group_service: GroupService,
    mock_group_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")

    mock_membership_service.require_coach_or_owner_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.coach
    )

    group_service.delete(actor_id=actor.id, club_id=club.id, group_id=5)

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(actor.id, club.id)
    mock_group_repo.delete.assert_called_once_with(club_id=club.id, group_id=5)
