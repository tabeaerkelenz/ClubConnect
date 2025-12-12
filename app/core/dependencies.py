from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.club import ClubRepository
from app.repositories.membership import MembershipRepository
from app.repositories.plan import PlanRepository
from app.repositories.user import UserRepository
from app.services.club import ClubService
from app.services.membership import MembershipService
from app.services.plan import PlanService
from app.services.user import UserService

#---- Dependency injection functions ----

# ---- Club ----
def get_club_repository(db: Session = Depends(get_db)) -> ClubRepository:
    return ClubRepository(db)

def get_club_service(club_repo: ClubRepository = Depends(get_club_repository)) -> ClubService:
    return ClubService(club_repo)


# ---- User ----
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repo)


# ---- Membership ----
def get_membership_repository(db: Session = Depends(get_db)):
    return MembershipRepository(db)

def get_membership_service(
    membership_repo: MembershipRepository = Depends(get_membership_repository),
) -> MembershipService:
    return MembershipService(membership_repo, user_repo=get_user_repository(), club_repo=get_club_repository())


def get_plan_repository(db: Session = Depends(get_db)):
    return PlanRepository(db)

def get_plan_service(plan_repo: PlanRepository = Depends(get_plan_repository),
                     membership_service: MembershipService = Depends(get_membership_service)
                     ) -> PlanService:
    return PlanService(plan_repo, membership_service)