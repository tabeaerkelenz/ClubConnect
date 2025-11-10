class DomainError(Exception):
    status_code = 500
    default_detail = "Internal error"
    def __init__(self, detail: str | None = None, status_code: int | None = None):
        if detail is not None:
            self.detail = detail or self.default_detail
        if status_code is not None:
            self.status_code = status_code or self.status_code

    def __str__(self) -> str:
        return self.detail


class NotFoundError(DomainError):
    status_code = 404
    default_detail = "Not found"

class PermissionDeniedError(DomainError):
    status_code = 403
    default_detail = "Forbidden"

class ConflictError(DomainError):
    status_code = 409
    default_detail = "Conflict"


# user exceptions
class EmailExistsError(ConflictError):
    default_detail = "Email already exists"

# club exceptions
class ClubNotFoundError(NotFoundError):
    default_detail = "Club not found"

class MembershipNotFoundError(NotFoundError):
    default_detail = "Membership not found"

class DuplicateSlugError(ConflictError):
    default_detail = "Slug already exists"

# membership exceptions
class UserNotFoundError(NotFoundError):
    default_detail = "User not found"

class MembershipExistsError(ConflictError):
    default_detail = "Membership already exists"

class LastCoachViolationError(ConflictError):
    default_detail = "Last Coach Violation"


# Plan errors
class NotCoachOfClubError(PermissionDeniedError):
    default_detail = "Not Coach Club"


class PlanNotFoundError(NotFoundError):
    default_detail = "Plan not found"


# session errors
class NotClubMember(PermissionDeniedError):
    default_detail = "Not Club Member"

class InvalidTimeRange(ConflictError):
    default_detail = "Invalid time range"

class SessionNotFound(NotFoundError):
    default_detail = "Session not found"

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
