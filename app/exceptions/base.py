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


# club exceptions
class ClubNotFoundError(NotFoundError):
    default_detail = "Club not found"

class MembershipNotFoundError(NotFoundError):
    default_detail = "Membership not found"

class DuplicateSlugError(ConflictError):
    default_detail = "Slug already exists"
