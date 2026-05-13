from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import UserModel
from schemas.user import UserCreate
from core.security import get_password_hash

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str):
        result = await self.session.execute(select(UserModel).where(UserModel.username == username))
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate):
        hashed_password = get_password_hash(user_data.password)
        new_user = UserModel(username=user_data.username, hashed_password=hashed_password)
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user