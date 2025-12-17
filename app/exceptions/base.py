class DomainError(Exception):
    status_code = 500
    default_detail = "Internal error"

    def __init__(self, detail: str | None = None, status_code: int | None = None):
        if status_code is not None:
            self.status_code = status_code
        if detail is not None:
            self.detail = detail
        elif not hasattr(self, "detail"):
            self.detail = self.default_detail

    def __str__(self) -> str:
        return self.detail


class NotFoundError(DomainError):
    status_code = 404
    detail = "Not found"

class PermissionDeniedError(DomainError):
    status_code = 403
    detail = "Forbidden"

class ConflictError(DomainError):
    status_code = 409
    detail = "Conflict"


# user exceptions
class EmailExistsError(ConflictError):
    detail = "Email already exists"


class AuthError(DomainError):
    """Domain error for auth problems."""
    detail = "Authentication error"


class IncorrectPasswordError(AuthError):
    """Raised when the old password does not match."""
    detail = "Incorrect password"


# club exceptions
class ClubNotFoundError(NotFoundError):
    detail = "Club not found"

class MembershipNotFoundError(NotFoundError):
    detail = "Membership not found"

class DuplicateSlugError(ConflictError):
    detail = "Slug already exists"

# membership exceptions
class UserNotFoundError(NotFoundError):
    detail = "User not found"

class MembershipExistsError(ConflictError):
    detail = "Membership already exists"

class LastCoachViolationError(ConflictError):
    detail = "Last Coach Violation"

class CoachRequiredError(PermissionDeniedError):
    detail = "Coach role required"

class OwnerRequiredError(PermissionDeniedError):
    detail = "Owner role required"

class CoachOrOwnerRequiredError(PermissionDeniedError):
    detail = "Coach or Owner role required"


# Plan errors
class NotCoachOfClubError(PermissionDeniedError):
    detail = "Not Coach Club"


class PlanNotFoundError(NotFoundError):
    detail = "Plan not found"


class PlanNameExistsError(ConflictError):
    detail = "Plan name already exists"


# session errors
class NotClubMember(PermissionDeniedError):
    detail = "Not Club Member"

class InvalidTimeRange(ConflictError):
    detail = "Invalid time range"

class SessionNotFound(NotFoundError):
    detail = "Session not found"

# exercise errors
class ExerciseNotFoundError(NotFoundError):
    detail = "Exercise not found."

class PositionConflictError(ConflictError):
    detail = "Position already taken."

# plan assignment errors
class PlanAssigneeNotFound(NotFoundError):
    detail = "Plan assignee not found."

class UserNotClubMember(PermissionDeniedError):
    detail = "User is not a member of this club."

class PlanAssignmentExistsError(ConflictError):
    detail = "Plan assignment already exists."


# attendance errors
class AttendanceNotFoundError(NotFoundError):
    detail = "Attendance record not found."

class AttendanceExistsError(ConflictError):
    detail = "Attendance record already exists."


# groups
class GroupNotFoundError(NotFoundError):
    detail = "Group not found"


class GroupNameExistsError(ConflictError):
    detail = "Group name already exists in this club"


class GroupMembershipNotFoundError(NotFoundError):
    detail = "Group membership not found"


class GroupMembershipExistsError(ConflictError):
    detail = "User is already in this group"