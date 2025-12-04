from app.exceptions.base import  ClubNotFoundError
from app.models.models import User
from app.schemas.club import ClubUpdate, ClubCreate, ClubRead
from app.schemas.membership import MembershipCreate
from app.repositories.club import ClubRepository
from app.utils.slug import generate_club_slug


class ClubService:
    def __init__(self, club_repo: ClubRepository):
        self.club_repo = club_repo


    def create_club_and_owner(self, club_create: ClubCreate, membership_create: MembershipCreate, user: User):
        slug = generate_club_slug([club_create.name, club_create.country, club_create.city, club_create.sport])

        club_data = club_create.model_dump(exclude_unset=True)
        club_data['slug'] = slug
        club = self.club_repo.create_club(**club_data)

        owner_membership = self.club_repo.add_membership(
            user_id=user.id,
            club_id=club.id,
            role=membership_create.role
        )

        return club, owner_membership

    def get_club_service(self, club_id: int):
        club = self.club_repo.get_club(club_id)
        if not club:
            raise ClubNotFoundError()
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
        club = self.club_repo.get_club(club_id)
        if not club:
            raise ClubNotFoundError()

        # get current data
        current_data = {
            "name": club.name,
            "country": club.country,
            "city": club.city,
            "sport": club.sport,
        }

        # merge new data
        update_data = club_update.model_dump(exclude_unset=True)
        merged = {**current_data, **update_data}

        # create new slug
        new_slug = generate_club_slug(
            [
            merged["name"],
            merged["country"],
            merged["city"],
            merged["sport"],
            ]
        )

        # add new slug to update data
        update_data["slug"] = new_slug

        # call repo to update club
        updated_club = self.club_repo.update_club(club, **update_data)

        return updated_club

    def delete_club_service(self, club_id):
        club = self.club_repo.get_club(club_id)
        if not club:
            raise ClubNotFoundError()

        self.club_repo.delete_club(club)

        return None