import inspect
from app.exceptions import club
from app.exceptions.base import DomainError

def test_all_domain_errors_define_status_and_detail():
    for name, obj in inspect.getmembers(club):
        if inspect.isclass(obj) and issubclass(obj, DomainError) and obj is not DomainError:
            assert isinstance(getattr(obj, "status_code", None), int)
            assert isinstance(getattr(obj, "detail", None), str)