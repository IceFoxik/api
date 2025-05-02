from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from sqlalchemy import select

async def get_user_type(session: AsyncSession, telegram_id: str):
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().first()
    return user.user_type if user else None