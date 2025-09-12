from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from ClubConnect.app.db.database import get_db
from ClubConnect.app.db.models import Membership, MembershipRole, Club, User
from ClubConnect.app.schemas.club import ClubCreate, ClubUpdate, ClubRead
from ClubConnect.app.crud.club import create_club, get_club, list_clubs, update_club, delete_club
from ClubConnect.app.auth.deps import get_current_active_user, get_current_user

router = APIRouter(
    prefix="/clubs",
    tags=["clubs"],
)

@router.post("", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club_endpoint(payload: ClubCreate, db: Session = Depends(get_db), me = Depends(get_current_active_user)):
    try:
        club = create_club(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Ensures creator is club coach (club-scoped admin)
    existing = db.execute(
        select(Membership).where(
            (Membership.user_id == me.id) & (Membership.club_id == club.id)
        )
    ).scalar_one_or_none()
    if not existing:
        db.add(Membership(user_id=me.id, club_id=club.id, role=MembershipRole.coach))
        db.commit()

    return club

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
    stmt = (
        select(Club)
        .join(Membership, Membership.club_id == Club.id)
        .where(Membership.user_id == me.id)
        .order_by(Club.name.asc())
    )
    clubs = db.execute(stmt).scalars().all()
    return [ClubRead.model_validate(c) for c in clubs]

@router.get("/{club_id:int}", response_model=ClubRead, status_code=status.HTTP_200_OK)
def get_club_endpoint(club_id: int, db: Session = Depends(get_db)):
    club = get_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@router.patch("/{club_id}", response_model=ClubRead, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])           # add dependency get current active user
def update_club_endpoint(club_id: int, payload: ClubUpdate, db: Session = Depends(get_db)):
    try:
        club = update_club(db, club_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

@router.delete("/{club_id}", response_model=ClubRead, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])      # add dependency get current active user
def delete_club_endpoint(club_id: int, db: Session = Depends(get_db)):
    club = delete_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club