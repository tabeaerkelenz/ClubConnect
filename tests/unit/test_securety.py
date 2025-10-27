from app.core.security import hash_password, verify_password  # or wherever you put them

def test_verify_password_roundtrip():
    pw = "pw123456"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)
    assert not verify_password("wrongpw", hashed)