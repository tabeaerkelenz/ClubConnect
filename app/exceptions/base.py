class DomainError(Exception):
    status_code = 500
    default_detail = "Internal error"
    def __init__(self, detail: str | None = None, status_code: int | None = None):
        if detail is not None:
            self.detail = detail or self.default_detail

    def __str__(self) -> str:
        return self.detail


class NotFoundError(DomainError):
    detail = "Not found"

class PermissionDeniedError(DomainError):
    detail = "Forbidden"

class ConflictError(DomainError):
    detail = "Conflict"


# user exceptions
class EmailExistsError(ConflictError):
    detail = "Email already exists"

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


# Plan errors
class NotCoachOfClubError(PermissionDeniedError):
    detail = "Not Coach Club"


class PlanNotFoundError(NotFoundError):
    detail = "Plan not found"


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
