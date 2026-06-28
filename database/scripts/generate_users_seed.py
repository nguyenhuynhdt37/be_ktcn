#!/usr/bin/env python3
"""
Generate 1000 test users seed SQL for Admin CMS.
Rules:
  - 1 Super Admin (fixed UUID from existing seed.sql)
  - ~10 Admin, ~150 Editor, ~840 Author
  - Realistic Vietnamese names, emails, phones
  - Passwords all bcrypt-hashed from 'Password@123'
  - ON CONFLICT DO NOTHING so safe to re-run
"""
import uuid
import random
import sys
from datetime import datetime, timezone, timedelta

# ── bcrypt hash of "Password@123" (cost=12) ──────────────────────────────────
# Pre-computed so script has no runtime dependency
PASSWORD_HASH = "$2b$12$7fUPFlvPZN/mKflaMRcXcOYLrLe2PhIQq.i3xPzU8h/IRu1L49st."

# ── Role IDs (from seed.sql) ──────────────────────────────────────────────────
ROLE_SUPER_ADMIN = "d1017cf7-88b3-4f9e-c616-3e4b3c75ad01"
ROLE_ADMIN       = "d1017cf7-88b3-4f9e-c616-3e4b3c75ad02"
ROLE_EDITOR      = "d1017cf7-88b3-4f9e-c616-3e4b3c75ad03"
ROLE_AUTHOR      = "d1017cf7-88b3-4f9e-c616-3e4b3c75ad04"

# ── Existing Super Admin user (must stay, not re-created) ─────────────────────
SUPER_ADMIN_ID = "a0000000-0000-0000-0000-000000000001"

# ── Name pools ────────────────────────────────────────────────────────────────
FIRST_NAMES = [
    "Anh", "Bảo", "Chi", "Dũng", "Em", "Phú", "Giang", "Hoa", "Ích", "Khánh",
    "Lan", "Minh", "Nam", "Oanh", "Phong", "Quân", "Rạng", "Sơn", "Tuấn", "Uyên",
    "Vinh", "Xuân", "Yến", "Zung", "An", "Bình", "Cường", "Duyên", "Hằng", "Hiếu",
    "Hoà", "Hùng", "Hải", "Huy", "Khoa", "Long", "Linh", "Mai", "Ngân", "Nhân",
    "Ngọc", "Nhung", "Phúc", "Quang", "Thành", "Thảo", "Thanh", "Thiện", "Thu", "Tiến",
    "Toàn", "Trang", "Trung", "Tú", "Tùng", "Vân", "Việt", "Vũ", "Wân", "Hà",
]

LAST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
    "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đinh", "Trịnh", "Lưu", "Đoàn",
    "Tô", "Cao", "Lâm", "Trương", "Nông", "Tống", "Từ", "Quách", "Khúc", "Kiều",
]

MIDDLE_NAMES = [
    "Văn", "Thị", "Đức", "Thế", "Hữu", "Xuân", "Thu", "Quốc", "Bá", "Tấn",
    "Công", "Ngọc", "Kim", "Diễm", "Bích", "Hoài", "Như", "Tường", "Phương", "Thanh",
]

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
                 "proton.me", "company.vn", "mail.vn", "vnn.vn", "vnpt.vn"]

VN_AREA_CODES = ["096", "097", "098", "032", "033", "034", "035", "036", "037", "038",
                 "039", "070", "079", "077", "078", "076", "089", "090", "093", "094"]

def rand_phone():
    code = random.choice(VN_AREA_CODES)
    suffix = "".join(str(random.randint(0, 9)) for _ in range(7))
    return f"{code}{suffix}"

def rand_ts(days_back_max=730):
    """Random timestamp within the past N days."""
    delta = timedelta(
        days=random.randint(0, days_back_max),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    dt = datetime.now(timezone.utc) - delta
    return dt.strftime("%Y-%m-%d %H:%M:%S+00")

def rand_last_login():
    if random.random() < 0.15:  # 15% never logged in
        return "NULL"
    delta = timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
    dt = datetime.now(timezone.utc) - delta
    return f"'{dt.strftime('%Y-%m-%d %H:%M:%S+00')}'"

def slugify(name: str) -> str:
    """Simple ASCII-safe slug from Vietnamese name."""
    mapping = str.maketrans(
        "áàảãạăắặằẳẵâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ"
        "đÁÀẢÃẠĂẮẶẰẲẴÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ",
        "aaaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiioooooooooooooooouuuuuuuuuuuyyyyyd"
        "aaaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiioooooooooooooooouuuuuuuuuuuyyyyyd"
    )
    result = name.lower().translate(mapping)
    result = "".join(c if c.isalnum() else "_" for c in result)
    return result

def generate_users(n=1000):
    """Return list of user dicts."""
    users = []
    used_usernames = set()
    used_emails = set()

    # ── User 1: Super Admin (fixed, predictable) ──────────────────────────────
    users.append({
        "id": SUPER_ADMIN_ID,
        "username": "superadmin",
        "email": "superadmin@cms.local",
        "phone": "0901234567",
        "full_name": "Super Administrator",
        "is_active": True,
        "last_login": f"'{rand_ts(days_back_max=7)}'",
        "email_verified_at": f"'{rand_ts(days_back_max=700)}'",
        "created_at": rand_ts(days_back_max=730),
        "role_id": ROLE_SUPER_ADMIN,
    })
    used_usernames.add("superadmin")
    used_emails.add("superadmin@cms.local")

    # Distribution of remaining 999 users
    # Admin: 10, Editor: 149, Author: 840
    role_distribution = (
        [ROLE_ADMIN]  * 10 +
        [ROLE_EDITOR] * 149 +
        [ROLE_AUTHOR] * 840
    )
    random.shuffle(role_distribution)

    for i, role_id in enumerate(role_distribution):
        for attempt in range(20):
            last = random.choice(LAST_NAMES)
            mid  = random.choice(MIDDLE_NAMES)
            first = random.choice(FIRST_NAMES)
            full_name = f"{last} {mid} {first}"

            slug_first = slugify(first)
            slug_last  = slugify(last)
            suffix = str(random.randint(1, 9999))
            username = f"{slug_first}{slug_last}{suffix}"[:50]

            domain = random.choice(EMAIL_DOMAINS)
            email = f"{slug_first}.{slug_last}{random.randint(1, 9999)}@{domain}"[:255]

            if username not in used_usernames and email not in used_emails:
                used_usernames.add(username)
                used_emails.add(email)
                created = rand_ts(days_back_max=720)
                users.append({
                    "id": str(uuid.uuid4()),
                    "username": username,
                    "email": email,
                    "phone": rand_phone() if random.random() > 0.2 else None,
                    "full_name": full_name,
                    "is_active": random.random() > 0.08,  # ~8% inactive
                    "last_login": rand_last_login(),
                    "email_verified_at": f"'{rand_ts(days_back_max=700)}'" if random.random() > 0.1 else "NULL",
                    "created_at": created,
                    "role_id": role_id,
                })
                break

    return users

def write_sql(users, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("-- ============================================================\n")
        f.write("-- Users Bulk Seed (1 000 records)\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write("-- Password for all test users: Password@123\n")
        f.write("-- Super Admin: superadmin / Password@123\n")
        f.write("-- ON CONFLICT DO NOTHING — safe to re-run\n")
        f.write("-- ============================================================\n\n")

        # Use a DO $$ block to safely insert each user, skipping any
        # row that conflicts on id, username, or email.
        f.write("-- 1. Insert Users (skip any existing row on id/username/email conflict)\n")

        for u in users:
            phone_val = f"'{u['phone']}'" if u["phone"] else "NULL"
            is_active = "TRUE" if u["is_active"] else "FALSE"
            f.write(
                f"INSERT INTO users "
                f"(id, username, email, phone, password_hash, full_name, is_active, last_login, email_verified_at, created_at, updated_at) "
                f"VALUES ("
                f"'{u['id']}', '{u['username']}', '{u['email']}', "
                f"{phone_val}, '{PASSWORD_HASH}', '{u['full_name']}', "
                f"{is_active}, {u['last_login']}, {u['email_verified_at']}, "
                f"'{u['created_at']}', '{u['created_at']}'"
                f") ON CONFLICT DO NOTHING;\n"
            )

        f.write("\n")

        # ── User Roles ────────────────────────────────────────────────────────
        f.write("-- 2. Assign Roles to Users\n")
        for u in users:
            f.write(
                f"INSERT INTO user_roles (user_id, role_id) VALUES "
                f"('{u['id']}', '{u['role_id']}') ON CONFLICT (user_id, role_id) DO NOTHING;\n"
            )

        f.write("\n")

        # ── Summary ───────────────────────────────────────────────────────────
        role_counts = {}
        role_names = {
            ROLE_SUPER_ADMIN: "super_admin",
            ROLE_ADMIN:       "admin",
            ROLE_EDITOR:      "editor",
            ROLE_AUTHOR:      "author",
        }
        for u in users:
            rn = role_names.get(u["role_id"], "unknown")
            role_counts[rn] = role_counts.get(rn, 0) + 1

        f.write("-- Summary:\n")
        for rname, cnt in sorted(role_counts.items()):
            f.write(f"--   {rname}: {cnt}\n")
        f.write(f"--   TOTAL: {len(users)}\n")

    print(f"✅ Generated {len(users)} users → {out_path}")
    for rname, cnt in sorted(role_counts.items()):
        print(f"   {rname:15s}: {cnt}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/Users/huynh/codes/be/database/schema/users_seed.sql"
    random.seed(42)  # deterministic so re-runs produce same UUIDs... but we use uuid4
    users = generate_users(1000)
    write_sql(users, out)
