from sqlalchemy.ext.asyncio import AsyncSession

from core.passwords import hash_password, verify_password
from core.security import create_access_token
from modules.users.models import Users
from modules.users import service as users_service


async def register(db: AsyncSession, email: str, password: str) -> dict:
    existing = await users_service.get_user_by_email(db, email)
    if existing:
        raise ValueError("Email already registered")

    hashed = await hash_password(password)
    user = Users(email=email, password_hash=hashed)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = await create_access_token({"user_id": str(user.id)})
    return {"access_token": token, "user_id": str(user.id), "email": user.email}


async def login(db: AsyncSession, email: str, password: str) -> dict:
    user = await users_service.get_user_by_email(db, email)
    if not user:
        raise ValueError("Invalid credentials")

    if not await verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    token = await create_access_token({"user_id": str(user.id)})
    return {"access_token": token, "user_id": str(user.id), "email": user.email}
