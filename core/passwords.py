import anyio
import bcrypt


async def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False

    def _check() -> bool:
        try:
            return bcrypt.checkpw(plain.encode(), hashed.encode())
        except (ValueError, TypeError):
            return False

    return await anyio.to_thread.run_sync(_check)


async def hash_password(plain: str) -> str:
    def _hash() -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    return await anyio.to_thread.run_sync(_hash)
