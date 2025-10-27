# tests/unit/test_security.py
import pytest
from app.core.security import hash_password, verify_password

@pytest.mark.unit
@pytest.mark.parametrize("pw", [
    "pw123456",
    "😊🔥密码🔒",
    " " * 8,
    "a" * 1024,                    # long
])
def test_verify_password_roundtrip(pw):
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)
    assert not verify_password(pw + "x", hashed)

def test_hash_is_salted():
    # two hashes for same pw should differ if salt is used
    pw = "samepw"
    h1 = hash_password(pw)
    h2 = hash_password(pw)
    assert h1 != h2
