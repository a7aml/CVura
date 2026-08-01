import uuid

from app.repositories import profile_repo
from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileAlreadyExists(Exception):
    pass


class ProfileNotFound(Exception):
    pass


async def get_full_profile(db, user_id: uuid.UUID):
    profile = await profile_repo.get_by_user_id(db, user_id)
    if profile is None:
        raise ProfileNotFound()
    return profile


async def create_profile(db, user_id: uuid.UUID, data: ProfileCreate):
    if await profile_repo.get_by_user_id(db, user_id) is not None:
        raise ProfileAlreadyExists()
    return await profile_repo.create_profile(db, user_id, **data.model_dump())


async def update_profile(db, user_id: uuid.UUID, data: ProfileUpdate):
    profile = await profile_repo.get_by_user_id(db, user_id)
    if profile is None:
        raise ProfileNotFound()
    changes = data.model_dump(exclude_unset=True)
    return await profile_repo.update_profile(db, profile, **changes)
