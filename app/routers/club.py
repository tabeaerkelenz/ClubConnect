from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ClubConnect.app.db.database import SessionLocal
from ClubConnect.app.schemas.club import ClubCreate, ClubUpdate, ClubRead
from ClubConnect.app.crud.club import create_club, get_club, list_clubs, update_club, delete_club

router = APIRouter(prefix="/clubs", tags=["clubs"])

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club_endpoint(payload: ClubCreate, db: Session = Depends(get_db)):
    return create_club(db, payload)

@router.get("/{club_id}", response_model=ClubRead, status_code=status.HTTP_200_OK)
def get_club_endpoint(club_id: int, db: Session = Depends(get_db)):
    club = get_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

@router.get("",response_model=List[ClubRead], status_code=status.HTTP_200_OK)
def get_clubs_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list_clubs(db, skip=skip, limit=limit)

@router.patch("/{club_id}", response_model=ClubRead, status_code=status.HTTP_200_OK)
def update_club_endpoint(club_id: int, payload: ClubUpdate, db: Session = Depends(get_db)):
    club = update_club(db, club_id, payload)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

@router.delete("/{club_id}", response_model=ClubRead, status_code=status.HTTP_200_OK)
def delete_club_endpoint(club_id: int, db: Session = Depends(get_db)):
    club = delete_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club