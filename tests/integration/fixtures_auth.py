from typing import Dict
from fastapi.testclient import TestClient

def signup_and_login(
    client: TestClient,
    email: str,
    password: str,
) -> Dict[str, str]:
    """
    Helper function to sign up and log in a user, returning the auth headers
    :param client: FastAPI TestClient
    :param email: User email
    :param password: User password
    :return: Dictionary with Authorization header
    """
    # Sign up the user
    signup_response = client.post(
        "/auth/signup",
        json={"email": email, "password": password},
    )
    assert signup_response.status_code == 201, f"Signup failed: {signup_response.text}"

    # Log in the user
    login_response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json().get("access_token")
    assert token is not None, "No access token returned"

    return {"Authorization": f"Bearer {token}"}