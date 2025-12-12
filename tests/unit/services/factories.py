from app.models.models import User, Club, Membership, MembershipRole, UserRole


def make_user(
    user_id: int = 1,
    name: str = "Alice",
    email: str = "alice@example.com",
    role: UserRole | None = None,
    is_active: bool = True,
    password_hash: str = "fake-hash",
) -> User:
    return User(
        id=user_id,
        name=name,
        email=email,
        password_hash=password_hash,
        role=role or list(UserRole)[0],
        is_active=is_active,
    )


'''
def make_user(user_id: int, email: str):
    u = User()
    u.id = user_id
    u.email = email
    return u
'''

def make_club(club_id: int, name: str):
    c = Club()
    c.id = club_id
    c.name = name
    return c

def make_membership(membership_id: int, club_id: int, user_id: int, role: MembershipRole):
    m = Membership()
    m.id = membership_id
    m.club_id = club_id
    m.user_id = user_id
    m.role = role
    return m