import inspect
from app.exceptions import base
from app.exceptions.base import DomainError

def test_all_domain_errors_define_status_and_detail():
    for name, obj in inspect.getmembers(base):
        if inspect.isclass(obj) and issubclass(obj, DomainError) and obj is not DomainError:
            assert isinstance(getattr(obj, "status_code", None), int)
            assert isinstance(getattr(obj, "detail", None), str)