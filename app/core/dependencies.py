from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.attendance import AttendanceRepository
from app.repositories.club import ClubRepository
from app.repositories.exercise import ExerciseRepository
from app.repositories.membership import MembershipRepository
from app.repositories.plan import PlanRepository
from app.repositories.plan_assignment import PlanAssignmentRepository
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.services.attendance import AttendanceService
from app.services.club import ClubService
from app.services.exercise import ExerciseService
from app.services.membership import MembershipService
from app.services.plan import PlanService
from app.services.plan_assignment import PlanAssignmentService
from app.services.session import SessionService
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
    user_repo: UserRepository = Depends(get_user_repository),
    club_repo: ClubRepository = Depends(get_club_repository),
) -> MembershipService:
    return MembershipService(membership_repo, user_repo=user_repo, club_repo=club_repo)


def get_plan_repository(db: Session = Depends(get_db)):
    return PlanRepository(db)

def get_plan_service(plan_repo: PlanRepository = Depends(get_plan_repository),
                     membership_service: MembershipService = Depends(get_membership_service)
                     ) -> PlanService:
    return PlanService(plan_repo, membership_service)


# ---- Session ----
def get_session_repository(db: Session = Depends(get_db)) -> SessionRepository:
    return SessionRepository(db)

def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    membership_service: MembershipService = Depends(get_membership_service),
) -> SessionService:
    return SessionService(session_repo=session_repo, membership_service=membership_service)



# ---- Exercise ----
def get_exercise_repository(db: Session = Depends(get_db)):
    return ExerciseRepository(db)

def get_exercise_service(
    exercise_repo: ExerciseRepository = Depends(get_exercise_repository),
    membership_service: MembershipService = Depends(get_membership_service),
) -> ExerciseService:
    return ExerciseService(
        exercise_repo=exercise_repo,
        membership_service=membership_service,
    )

# Attendance
def get_attendance_repository(db: Session = Depends(get_db)) -> AttendanceRepository:
    return AttendanceRepository(db)

def get_attendance_service(
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository),
    membership_service: MembershipService = Depends(get_membership_service),
) -> AttendanceService:
    return AttendanceService(attendance_repo=attendance_repo, membership_service=membership_service)


# plan_assignments
def get_plan_assignment_repository(db: Session = Depends(get_db)) -> PlanAssignmentRepository:
    return PlanAssignmentRepository(db)

def get_plan_assignment_service(
    repo: PlanAssignmentRepository = Depends(get_plan_assignment_repository),
    membership_service: MembershipService = Depends(get_membership_service),
) -> PlanAssignmentService:
    return PlanAssignmentService(repo=repo, membership_service=membership_service)