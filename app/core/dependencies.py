from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.club import ClubRepository
from app.repositories.user import UserRepository
from app.services.club import ClubService
from app.services.user import UserService


def get_club_repository(db: Session = Depends(get_db)) -> ClubRepository:
    return ClubRepository(db)

def get_club_service(club_repo: ClubRepository = Depends(get_club_repository)) -> ClubService:
    return ClubService(club_repo)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repo)