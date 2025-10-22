from sqlalchemy.exc import IntegrityError

from app.auth.membership_deps import assert_is_coach_of_club, assert_is_owner_of_club, assert_is_coach_or_owner_of_club, \
    count_coach_owner
from app.crud.membership import *
from app.crud.user import get_user_by_email
from app.crud.club import get_club
from app.exceptions.membership import (
    UserNotFoundError,
    MembershipExistsError,
    ClubNotFoundError,
    MembershipNotFoundError,
    LastCoachViolationError,
)

def create_membership_service(db, club_id, email, role) -> Membership:
    user = get_user_by_email(db, email.strip().lower())
    if not user:
        raise UserNotFoundError()

    exists = membership_not_exists(db, user.id, club_id)
    if not exists:
        raise MembershipExistsError()

    try:
        membersip = create_membership(db, club_id, user.id, role)
        db.commit()
        return membersip
    except IntegrityError as e:
        db.rollback()
        raise MembershipExistsError() from e

def get_memberships_user_service(db, email):
    user = get_user_by_email(db, email.strip().lower())
    if not user:
        raise UserNotFoundError()
    return get_memberships_user(db, email)

def get_memberships_user_service(db, email):
    user = get_user_by_email(db, email.strip().lower())
    if not user:
        raise UserNotFoundError()
    return get_memberships_user(db, user.id)

def get_memberships_club_service(db, club_id):
    club = get_club(db, club_id)
    if not club:
        raise ClubNotFoundError()
    return get_memberships_club(db, club_id)

def get_membership_service(db, club_id, email):
    user = get_user_by_email(db, email.strip().lower())
    if not user:
        raise UserNotFoundError()
    membership = get_membership(db, club_id, user.id)
    if not membership:
        raise MembershipNotFoundError()
    return membership

def update_membership_role_service(db, club_id, membership_id, new_role):
    membership = get_membership_by_id(db, membership_id)
    if not membership:
        raise MembershipNotFoundError()
    if membership.role == MembershipRole.coach and new_role != MembershipRole.coach:
        remaining = count_other_coaches(db, club_id, membership.user_id)
        if remaining == 0:
            raise LastCoachViolationError()
    return update_membership_role(db, club_id=club_id, membership_id=membership_id, new_role=new_role
)


def delete_membership_service(db: Session, *, club_id: int, membership_id: int) -> None:
    m = get_membership_by_id(db, membership_id=membership_id)
    if not m:
        raise MembershipNotFoundError()

    # Only enforce last-coach if the **target** is coach-like
    if m.role == MembershipRole.coach or m.role == MembershipRole.owner:
        if count_coach_owner(db, club_id=club_id, exclude_user_id=m.user_id) == 0:
            raise LastCoachViolationError()

    delete_membership(db, membership=m)   # delete ONCE
    db.commit()