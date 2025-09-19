from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from ClubConnect.app.db.database import get_db
from ClubConnect.app.db.models import Membership, MembershipRole, Club, User
from ClubConnect.app.schemas.club import ClubCreate, ClubUpdate, ClubRead
from ClubConnect.app.crud.club import create_club, get_club, list_clubs, update_club, delete_club
from ClubConnect.app.auth.deps import get_current_active_user, get_current_user
from ClubConnect.app.services.club import get_club_service, update_club_service, delete_club_service, \
    create_club_service, get_my_clubs_service

router = APIRouter(
    prefix="/clubs",
    tags=["clubs"],
)

@router.post("", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club_endpoint(payload: ClubCreate, db: Session = Depends(get_db), me = Depends(get_current_active_user)):
    return create_club_service(db, payload, user=me)

@router.get("", response_model=List[ClubRead])
def list_or_search_clubs(
    q: Optional[str] = Query(None, description="Search by (part of) club name"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return list_clubs(db, skip=skip, limit=limit, q=q)


@router.get("/mine", response_model=list[ClubRead])
def my_clubs(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    return get_my_clubs_service(db, me)

@router.get("/{club_id:int}", response_model=ClubRead, status_code=status.HTTP_200_OK)
def get_club_endpoint(club_id: int, db: Session = Depends(get_db)):
    return get_club_service(db, club_id)


@router.patch("/{club_id}", response_model=ClubRead, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])           # add dependency get current active user
def update_club_endpoint(club_id: int, payload: ClubUpdate, db: Session = Depends(get_db)):
    return update_club_service(db, club_id, payload)

@router.delete("/{club_id}", response_model=ClubRead, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])      # add dependency get current active user
def delete_club_endpoint(club_id: int, db: Session = Depends(get_db)):
    return delete_club_service(db, club_id)