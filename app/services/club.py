from app.exceptions.base import  ClubNotFoundError
from app.schemas.club import ClubUpdate, ClubCreate, ClubRead
from app.schemas.membership import MembershipCreate
from app.repositories.club import ClubRepository


class ClubService:
    def __init__(self, club_repo: ClubRepository):
        self.club_repo = club_repo


    def create_club_and_owner(self, club_create: ClubCreate, membership_create: MembershipCreate):
        club = self.club_repo.create_club(**club_create.model_dump(exclude_unset=True))
        owner = self.membership_repo.crete_membership(**membership_create.model_dump(exclude_unset=True))
        return club, owner

    def get_club_service(self, club_id: int):
        club = self.club_repo.get_club(club_id)
        return club


    def list_clubs_service(self, skip: int = 0, limit: int = 50, q: str | None = None) -> list[ClubRead]:
        skip = max(0, skip)
        limit = max(1, min(limit, 200))

        if q is not None:
            q = q.strip()
            if q == "":
                q = None

        return self.club_repo.list_clubs(skip=skip, limit=limit, q=q)


    def get_my_clubs_service(self, user):
        clubs = self.club_repo.get_clubs_by_user(user)
        return clubs



    def update_club_service(self, user, club_id: int, club_update: ClubUpdate):
        # i need to add membership dependencies here: assert_is_owner_or_coach_of_club
        updated_club = self.club_repo.update_club(**club_update.model_dump(exclude_unset=True))
        return updated_club

    def delete_club_service(self, club_id):
        club = self.club_repo.get_club(club_id)
        if not club:
            raise ClubNotFoundError()
        self.club_repo.delete_club(club)
        return None