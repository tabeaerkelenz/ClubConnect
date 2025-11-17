from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.club import ClubRepository
from app.services.club import ClubService


def get_club_repository(db: Session = Depends(get_db)) -> ClubRepository:
    return ClubRepository(db)

def get_club_service(club_repo: ClubRepository = Depends(get_club_repository)) -> ClubService:
    return ClubService(club_repo)