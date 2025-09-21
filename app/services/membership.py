from sqlalchemy.exc import IntegrityError
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

def create_membership_service(db, club_id, email, role):
    user = get_user_by_email(db, email.strip().lower())
    if not user:
        raise UserNotFoundError()
    try:
        return create_membership(db, club_id, user.id, role)
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
    return update_membership_role(db, club_id, membership_id, new_role)

def delete_membership_service(db, club_id, membership_id):
    membership = get_membership_by_id(db, membership_id)
    if membership.role == MembershipRole.coach:
        remaining = count_other_coaches(db, club_id, membership.user_id)
        if remaining == 0:
            raise LastCoachViolationError()
    delete_membership(db, membership_id)