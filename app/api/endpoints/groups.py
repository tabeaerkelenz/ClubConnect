from fastapi import APIRouter, Depends, Query, status

from app.schemas.group import GroupCreate, GroupRead, GroupUpdate
from app.services.group import GroupService
from app.core.dependencies import get_group_service

from app.auth.deps import get_current_user


router = APIRouter(
    prefix="/clubs/{club_id}/groups",
    tags=["Groups"],
)


@router.post(
    "",
    response_model=GroupRead,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    club_id: int,
    group_create: GroupCreate,
    group_service: GroupService = Depends(get_group_service),
    me=Depends(get_current_user),
):
    return group_service.create(actor_id=me.id, club_id=club_id, data=group_create)


@router.get(
    "",
    response_model=list[GroupRead],
)
def list_groups(
    club_id: int,
    q: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    group_service: GroupService = Depends(get_group_service),
    me=Depends(get_current_user),
):
    return group_service.list(actor_id=me.id, club_id=club_id, q=q, offset=offset, limit=limit)


@router.get(
    "/{group_id}",
    response_model=GroupRead,
)
def get_group(
    club_id: int,
    group_id: int,
    group_service: GroupService = Depends(get_group_service),
    me=Depends(get_current_user),
):
    return group_service.get(actor_id=me.id, club_id=club_id, group_id=group_id)


@router.patch(
    "/{group_id}",
    response_model=GroupRead,
)
def update_group(
    club_id: int,
    group_id: int,
    group_update: GroupUpdate,
    group_service: GroupService = Depends(get_group_service),
    me=Depends(get_current_user),
):
    return group_service.update(actor_id=me.id, club_id=club_id, group_id=group_id, data=group_update)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_group(
    club_id: int,
    group_id: int,
    group_service: GroupService = Depends(get_group_service),
    me=Depends(get_current_user),
):
    group_service.delete(actor_id=me.id, club_id=club_id, group_id=group_id)
    return None
