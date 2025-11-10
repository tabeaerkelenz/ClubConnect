from sqlalchemy.orm import Session
from app.crud.group import create_group, get_group_by_id, list_search_groups
from app.exceptions.base import ConflictError


def create_group_service(db: Session, club_id, name: str, description: str, created_by_id: int):
    try:
        return create_group(db, club_id=club_id, name=name, description=description, created_by_id=created_by_id)
    except ConflictError as e:
        raise e


def get_group_by_id_service(db: Session, group_id: int):
    try:
        return get_group_by_id(db, group_id)
    except Exception as e:
        raise e from e

def list_search_groups_service(db: Session, club_id: int, q: str | None, limit: int, offset: int):
    try:
        return list_search_groups(db, club_id, q, limit=limit, offset=offset)
    except Exception as e:
        raise e from e
