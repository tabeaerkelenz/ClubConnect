from unittest.mock import MagicMock

import pytest

from app.exceptions.base import NotClubMember
from app.exceptions.base import GroupMembershipExistsError
from app.repositories.group_membership import GroupMembershipRepository
from app.services.group_membership import GroupMembershipService
from app.services.membership import MembershipService
from factories import make_user, make_club, make_membership
from app.models.models import MembershipRole


@pytest.fixture
def mock_gm_repo() -> MagicMock:
    return MagicMock(spec=GroupMembershipRepository)


@pytest.fixture
def mock_membership_service() -> MagicMock:
    return MagicMock(spec=MembershipService)


@pytest.fixture
def gm_service(mock_gm_repo: MagicMock, mock_membership_service: MagicMock) -> GroupMembershipService:
    return GroupMembershipService(gm_repo=mock_gm_repo, membership_service=mock_membership_service)


def test_list_members_requires_member(
    gm_service: GroupMembershipService,
    mock_gm_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")

    mock_membership_service.require_member_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.member
    )
    mock_gm_repo.list_for_group.return_value = []

    gm_service.list_members(actor_id=actor.id, club_id=club.id, group_id=7)

    mock_membership_service.require_member_of_club.assert_called_once_with(actor.id, club.id)
    mock_gm_repo.list_for_group.assert_called_once_with(club_id=club.id, group_id=7)


def test_add_member_requires_coach_or_owner(
    gm_service: GroupMembershipService,
    mock_gm_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")

    mock_membership_service.require_coach_or_owner_of_club.side_effect = NotClubMember()

    with pytest.raises(NotClubMember):
        gm_service.add_member(actor_id=actor.id, club_id=club.id, group_id=7, user_id=2, role="member")

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(actor.id, club.id)
    mock_gm_repo.add.assert_not_called()


def test_add_member_requires_target_user_is_club_member(
    gm_service: GroupMembershipService,
    mock_gm_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")
    target_user_id = 2

    mock_membership_service.require_coach_or_owner_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.coach
    )

    def require_member_side_effect(user_id: int, club_id_arg: int):
        # actor membership isn't checked here; only target membership
        if user_id == target_user_id:
            raise NotClubMember()
        return make_membership(membership_id=99, club_id=club.id, user_id=user_id, role=MembershipRole.member)

    mock_membership_service.require_member_of_club.side_effect = require_member_side_effect

    with pytest.raises(NotClubMember):
        gm_service.add_member(
            actor_id=actor.id,
            club_id=club.id,
            group_id=7,
            user_id=target_user_id,
            role="member",
        )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(actor.id, club.id)
    mock_membership_service.require_member_of_club.assert_called_with(target_user_id, club.id)
    mock_gm_repo.add.assert_not_called()


def test_add_member_happy_path(
    gm_service: GroupMembershipService,
    mock_gm_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")
    target_user_id = 2

    mock_membership_service.require_coach_or_owner_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.owner
    )
    mock_membership_service.require_member_of_club.return_value = make_membership(
        membership_id=2, club_id=club.id, user_id=target_user_id, role=MembershipRole.member
    )

    fake_gm = MagicMock()
    fake_gm.group_id = 7
    fake_gm.user_id = target_user_id
    fake_gm.role = "member"
    mock_gm_repo.add.return_value = fake_gm

    result = gm_service.add_member(
        actor_id=actor.id,
        club_id=club.id,
        group_id=7,
        user_id=target_user_id,
        role="member",
    )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(actor.id, club.id)
    mock_membership_service.require_member_of_club.assert_called_once_with(target_user_id, club.id)
    mock_gm_repo.add.assert_called_once_with(
        club_id=club.id,
        group_id=7,
        user_id=target_user_id,
        role="member",
    )
    assert result is fake_gm


def test_add_member_propagates_repo_conflict(
    gm_service: GroupMembershipService,
    mock_gm_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    actor = make_user(user_id=1)
    club = make_club(club_id=10, name="My Club")
    target_user_id = 2

    mock_membership_service.require_coach_or_owner_of_club.return_value = make_membership(
        membership_id=1, club_id=club.id, user_id=actor.id, role=MembershipRole.coach
    )
    mock_membership_service.require_member_of_club.return_value = make_membership(
        membership_id=2, club_id=club.id, user_id=target_user_id, role=MembershipRole.member
    )

    mock_gm_repo.add.side_effect = GroupMembershipExistsError()

    with pytest.raises(GroupMembershipExistsError):
        gm_service.add_member(
            actor_id=actor.id,
            club_id=club.id,
            group_id=7,
            user_id=target_user_id,
            role="member",
        )

    mock_gm_repo.add.assert_called_once()
