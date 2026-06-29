import asyncio
from sqlalchemy import update
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.core.security import hash_password

async def main():
    async with SessionLocal() as db:
        new_hash = hash_password('Password@123')
        stmt = update(User).where(User.username == 'superadmin').values(password_hash=new_hash)
        res = await db.execute(stmt)
        await db.commit()
        print(f"Updated {res.rowcount} user(s). New password is Password@123")

asyncio.run(main())
