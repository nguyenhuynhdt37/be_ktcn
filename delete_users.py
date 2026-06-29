import asyncio
from sqlalchemy import select, delete
from app.core.database import SessionLocal
from app.modules.auth.models import User

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User))
        users = res.scalars().all()
        print(f"Total users before: {len(users)}")
        
        stmt = delete(User).where(User.username != 'superadmin')
        res = await db.execute(stmt)
        await db.commit()
        print(f"Deleted {res.rowcount} users.")

asyncio.run(main())
