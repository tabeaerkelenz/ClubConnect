from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.membership_deps import assert_is_coach_of_club, assert_is_member_of_club
from app.db.deps import get_db
from app.models.models import User
from app.schemas.group import GroupRead, GroupCreate
from app.services.group import get_group_by_id_service, list_search_groups_service, create_group_service

def require_member_of_club(
    club_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    assert_is_member_of_club(db, me.id, club_id)


router = APIRouter(prefix="/clubs/{club_id}/groups", tags=["groups"], dependencies=[Depends(require_member_of_club)])


@router.post("", response_model=GroupRead, status_code=201, response_model_exclude_none=True)
def create_group_ep(club_id: int, payload: GroupCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> GroupRead:
    """Create a new group."""
    assert_is_coach_of_club(db, user_id=me.id, club_id=club_id)
    try:
        group = create_group_service(db=db, club_id=club_id, name=payload.name, description=payload.description, created_by_id=me.id)
        return group
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("", response_model=list[GroupRead], response_model_exclude_none=True)
def list_search_groups_ep(
    club_id: int,                                   # from prefix /clubs/{club_id}/groups
    q: str | None = Query(
        None,
        min_length=2,
        description="Case-insensitive substring match on group name",
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
) -> list[GroupRead]:
    # (optional) auth: only members can list groups of this club
    assert_is_member_of_club(db, me.id, club_id)
    try:
        return list_search_groups_service(db, club_id=club_id, q=q, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{group_id}", response_model=GroupRead, response_model_exclude_none=True)
def get_group_by_id_ep(group_id: int, db: Session = Depends(get_db)) -> GroupRead:
    """Get a group by ID."""
    try:
        group = get_group_by_id_service(db, group_id)
        return group
    except Exception as e:
        raise HTTPException(400, str(e))
