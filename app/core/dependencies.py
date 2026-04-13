from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.ai_usage import AIUsageRepository
from app.repositories.attendance import AttendanceRepository
from app.repositories.club import ClubRepository
from app.repositories.exercise import ExerciseRepository
from app.repositories.group import GroupRepository
from app.repositories.group_membership import GroupMembershipRepository
from app.repositories.membership import MembershipRepository
from app.repositories.plan import PlanRepository
from app.repositories.plan_assignment import PlanAssignmentRepository
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.repositories.workout_plan import WorkoutPlanRepository
from app.services.attendance import AttendanceService
from app.services.club import ClubService
from app.services.exercise import ExerciseService
from app.services.group import GroupService
from app.services.group_membership import GroupMembershipService
from app.services.membership import MembershipService
from app.services.plan import PlanService
from app.services.plan_assignment import PlanAssignmentService
from app.services.session import SessionService
from app.services.user import UserService
from app.services.workout_plan import WorkoutPlanService
from app.services.workout_plan_ai import WorkoutPlanAIService


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


# plan assignments
def get_plan_assignment_repository(db: Session = Depends(get_db)) -> PlanAssignmentRepository:
    return PlanAssignmentRepository(db)

def get_plan_assignment_service(
    repo: PlanAssignmentRepository = Depends(get_plan_assignment_repository),
    membership_service: MembershipService = Depends(get_membership_service),
) -> PlanAssignmentService:
    return PlanAssignmentService(repo=repo, membership_service=membership_service)


# ---- groups ---
def get_group_repository(db: Session = Depends(get_db)) -> GroupRepository:
    return GroupRepository(db)

def get_group_service(
    group_repo: GroupRepository = Depends(get_group_repository),
    membership_service: MembershipService = Depends(get_membership_service),
) -> GroupService:
    return GroupService(group_repo=group_repo, membership_service=membership_service)


#---- group memberships ---
def get_group_membership_repository(db: Session = Depends(get_db)) -> GroupMembershipRepository:
    return GroupMembershipRepository(db)

def get_group_membership_service(
    gm_repo: GroupMembershipRepository = Depends(get_group_membership_repository),
    membership_service: MembershipService = Depends(get_membership_service),
) -> GroupMembershipService:
    return GroupMembershipService(gm_repo=gm_repo, membership_service=membership_service)


# ---- Workout Plans ----
def get_workout_plan_repository(db: Session = Depends(get_db)) -> WorkoutPlanRepository:
    return WorkoutPlanRepository(db=db)


def get_workout_plan_service(
    repo: WorkoutPlanRepository = Depends(get_workout_plan_repository),
    membership_service: MembershipService = Depends(get_membership_service),
) -> WorkoutPlanService:
    return WorkoutPlanService(repo=repo, membership_service=membership_service)


# ---- AI Usage Repository ----
def get_ai_usage_repository(db: Session = Depends(get_db)) -> AIUsageRepository:
    return AIUsageRepository(db)


# ---- workout plan ai ----
def get_workout_plan_ai_service(
    workout_plan_service: WorkoutPlanService = Depends(get_workout_plan_service),
    ai_usage_repo: AIUsageRepository = Depends(get_ai_usage_repository),
    club_repo: ClubRepository = Depends(get_club_repository),
) -> WorkoutPlanAIService:
    return WorkoutPlanAIService(
        workout_plan_service=workout_plan_service,
        ai_usage_repo=ai_usage_repo,
        club_repo=club_repo,
        daily_limit=3,
    )

