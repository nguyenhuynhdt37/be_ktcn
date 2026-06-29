import asyncio
from sqlalchemy import select
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.core.security import verify_password

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User).where(User.username == 'superadmin'))
        user = res.scalar_one_or_none()
        if user:
            print(f"Superadmin found. Hash: {user.password_hash}")
            print(f"Is Password@123 correct? {verify_password('Password@123', user.password_hash)}")
            print(f"Is 123456 correct? {verify_password('123456', user.password_hash)}")
            print(f"Is admin correct? {verify_password('admin', user.password_hash)}")
        else:
            print("Superadmin not found in DB.")

asyncio.run(main())
