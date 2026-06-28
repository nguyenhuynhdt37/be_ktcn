#!/usr/bin/env python3
"""
Execute users_seed.sql via asyncpg, statement by statement.
Skips statements that fail (UniqueViolation, ForeignKeyViolation) cleanly.
"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "postgres_password",
    "database": "university_cms",
}

SQL_FILE = "/Users/huynh/codes/be/database/schema/users_seed.sql"

async def run():
    sql_text = open(SQL_FILE, encoding="utf-8").read()

    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        # Split into individual statements
        statements = [s.strip() for s in sql_text.split(";") if s.strip() and not s.strip().startswith("--")]

        ok = skip = err = 0
        for stmt in statements:
            # Skip pure comment blocks
            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
            real_stmt = "\n".join(lines).strip()
            if not real_stmt:
                continue
            try:
                await conn.execute(real_stmt)
                ok += 1
            except asyncpg.UniqueViolationError:
                skip += 1
            except asyncpg.ForeignKeyViolationError:
                skip += 1
            except Exception as e:
                err += 1
                print(f"  ERROR: {e!r}")
                print(f"  STMT : {real_stmt[:120]}")

        print(f"\n✅ Execution complete: {ok} ok | {skip} skipped | {err} errors")

        # Quick count check
        total  = await conn.fetchval("SELECT COUNT(*) FROM users")
        sa     = await conn.fetchval("SELECT COUNT(*) FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE r.code = 'super_admin'")
        admin  = await conn.fetchval("SELECT COUNT(*) FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE r.code = 'admin'")
        editor = await conn.fetchval("SELECT COUNT(*) FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE r.code = 'editor'")
        author = await conn.fetchval("SELECT COUNT(*) FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE r.code = 'author'")
        print(f"\nUser counts in DB:")
        print(f"  Total users  : {total}")
        print(f"  super_admin  : {sa}")
        print(f"  admin        : {admin}")
        print(f"  editor       : {editor}")
        print(f"  author       : {author}")
    finally:
        await conn.close()

asyncio.run(run())

