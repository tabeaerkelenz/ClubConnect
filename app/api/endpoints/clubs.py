from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query

from app.core.dependencies import get_club_service
from app.models.models import User
from app.schemas.club import ClubCreate, ClubUpdate, ClubRead
from app.auth.deps import get_current_active_user, get_current_user
from app.schemas.membership import MembershipCreate
from app.services.club import ClubService

router = APIRouter(
    prefix="/clubs",
    tags=["clubs"],
)


@router.post("", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club_endpoint(
    payload_club_create: ClubCreate,
    payload_membership_create: MembershipCreate,
    club_service: ClubService = Depends(get_club_service),
    me: User=Depends(get_current_active_user),
):
    return club_service.create_club_and_owner(payload_club_create, payload_membership_create)


@router.get("", response_model=List[ClubRead])
def list_or_search_clubs(
    q: Optional[str] = Query(None, description="Search by (part of) club name"),
    skip: int = 0,
    limit: int = 50,
    club_service: ClubService = Depends(get_club_service),
):
    return club_service.list_clubs_service(skip=skip, limit=limit, q=q)


@router.get("/mine", response_model=list[ClubRead])
def my_clubs(club_service: ClubService = Depends(get_club_service), me: User = Depends(get_current_user)):
    return club_service.get_my_clubs_service(user=me)


@router.get("/{club_id}", response_model=ClubRead)
def get_club_endpoint(club_id: int, club_service: ClubService = Depends(get_club_service)):
    return club_service.get_club_service(club_id)


@router.patch("/{club_id}", response_model=ClubRead)
def update_club_endpoint(
    club_id: int, payload: ClubUpdate, club_service: ClubService = Depends(get_club_service), me: User = Depends(get_current_active_user)
):
    return club_service.update_club_service(user=me, club_id=club_id, club_update=payload)


@router.delete(
    "/{club_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_club_endpoint(club_id: int, club_service: ClubService = Depends(get_club_service), me: User = Depends(get_current_active_user)):
    club_service.delete_club_service(club_id=club_id)
