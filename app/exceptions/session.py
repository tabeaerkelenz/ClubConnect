class NotClubMember(Exception):
    """Exception raised when a user is not a member of the club."""
    pass
class NotCoach(Exception):
    """Exception raised when a user is not a coach of the club."""
    pass
class Conflict(Exception):
    """Exception raised for conflicts, such as unique constraint violations."""
    pass
class InvalidTimeRange(Exception):
    """Exception raised for invalid attendance actions."""
    pass
class SessionNotFound(Exception):
    """Exception raised when a session is not found."""
    pass