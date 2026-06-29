# Project Structure Export

Tai lieu nay tom tat khung du an hien tai de dung lam blueprint cho mot backend FastAPI khac.
Khong copy cac file runtime/du lieu nhu `.env`, `app.db`, `articles_export.sql`, `logs/`, cache, hoac `__pycache__/`.

## Stack chinh

- Python 3.12
- FastAPI + Uvicorn
- Pydantic v2 + pydantic-settings
- SQLAlchemy 2.0 async + asyncpg
- Alembic migrations
- PostgreSQL/pgvector, Redis, MinIO/S3
- JWT + bcrypt
- Loguru
- Ruff, Black, isort, mypy, pytest

## Cay thu muc nen tao

```text
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── exceptions.py
│   │   ├── logger.py
│   │   └── security.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── seo.py
│   │   └── repositories/
│   │       ├── __init__.py
│   │       └── base.py
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── pagination.py
│   │   ├── rate_limiter.py
│   │   ├── redis.py
│   │   ├── security/
│   │   │   └── encryption.py
│   │   └── seo/
│   │       └── helper.py
│   └── modules/
│       ├── __init__.py
│       ├── health/
│       │   ├── __init__.py
│       │   └── router.py
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── dependencies.py
│       │   ├── models.py
│       │   ├── router.py
│       │   ├── schemas.py
│       │   └── service.py
│       └── <domain>/
│           ├── __init__.py
│           ├── models.py
│           ├── schemas.py
│           ├── service.py
│           └── router.py
├── migrations/
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── database/
│   ├── schema/
│   └── scripts/
├── docs/
├── scripts/
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

## Vai tro tung lop

### `app/main.py`

- Khoi tao `FastAPI`.
- Cau hinh lifespan startup/shutdown.
- Init Redis khi startup, close Redis va dispose SQLAlchemy engine khi shutdown.
- Gan CORS theo moi truong.
- Dang ky global exception handlers.
- Import model de SQLAlchemy/Alembic nhan metadata.
- Include router theo prefix `settings.API_V1_STR`, vi du `/api/v1`.

### `app/core/`

- `config.py`: khai bao `Settings(BaseSettings)`, doc `.env`, tao database URL va Redis URL.
- `database.py`: tao async engine, `async_sessionmaker`, dependency `get_db`.
- `exceptions.py`: exception domain rieng va response envelope loi thong nhat.
- `security.py`: hash/verify password bang bcrypt, tao/decode JWT.
- `logger.py`: cau hinh Loguru.

### `app/common/`

- `models/base.py`: `DeclarativeBase` va `BaseModel` gom `id`, `created_at`, `updated_at`.
- `models/seo.py`: mixin/field dung chung cho SEO.
- `repositories/base.py`: generic CRUD repository async.

### `app/shared/`

- `pagination.py`: schema phan trang dung chung.
- `redis.py`: Redis connection pool va dependency `get_redis`.
- `rate_limiter.py`: logic gioi han request.
- `security/encryption.py`: helper ma hoa.
- `seo/helper.py`: helper SEO dung lai o cac module.

### `app/modules/`

Moi module domain nen theo cung pattern:

```text
modules/<domain>/
├── __init__.py
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic request/response schemas
├── service.py     # business logic, transaction-aware
└── router.py      # FastAPI APIRouter, dependency injection
```

Module hien co:

- `health`: health check root-level.
- `auth`: login, user, token, dependencies lay current user.
- `audit`: ghi log hanh dong.
- `media`: upload/quan ly media, MinIO/S3.
- `menu`: menu va menu item.
- `category`: CRUD category, tree, slug, soft delete.
- `article`: article, tags, scheduled tasks.

## File cau hinh nen copy

### `requirements.txt`

Core dependencies:

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy[asyncio]
asyncpg
alembic
redis
loguru
pyjwt
bcrypt
python-multipart
cryptography
boto3
Pillow
```

Dev/test:

```text
ruff
black
isort
mypy
pytest
pytest-asyncio
httpx
aiosqlite
```

### `pyproject.toml`

- Black line length: `88`
- Ruff target: Python 3.12
- Ruff rules: `E`, `W`, `F`, `I`, `C`, `B`, `UP`
- mypy strict mode
- pytest async mode: `auto`

### `.env.example`

Can gom cac nhom bien:

```text
PROJECT_NAME
ENV
DEBUG
API_V1_STR
BACKEND_CORS_ORIGINS

POSTGRES_SERVER
POSTGRES_PORT
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB

REDIS_HOST
REDIS_PORT
REDIS_PASSWORD
REDIS_DB

SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS

LOG_LEVEL
LOG_FORMAT
LOG_FILE_PATH

MINIO_ENDPOINT
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
MINIO_SECURE
MINIO_BUCKET
```

### `docker-compose.yml`

Nen co 3 service ha tang:

- `db`: `pgvector/pgvector:pg17`, port `5432`
- `redis`: `redis:8-alpine`, port `6379`
- `minio`: `minio/minio:latest`, ports `9000`, `9001`

## Mau module moi

Khi tao module moi, dung skeleton:

```text
app/modules/products/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
└── router.py
```

Sau do:

1. Tao SQLAlchemy model trong `models.py`, ke thua `BaseModel`.
2. Tao Pydantic schemas trong `schemas.py`: `ProductCreate`, `ProductUpdate`, `ProductResponse`.
3. Viet business logic trong `service.py`, nhan `AsyncSession` tu router.
4. Tao `APIRouter` trong `router.py`.
5. Import model va include router trong `app/main.py`.
6. Import model trong `migrations/env.py` de Alembic autogenerate thay metadata.
7. Tao migration bang `alembic revision --autogenerate -m "create products table"`.

## Lenh scaffold nhanh

```bash
mkdir -p app/{core,common/models,common/repositories,shared/security,shared/seo,modules/health,modules/auth,modules/audit,modules/media,modules/menu,modules/category,modules/article}
mkdir -p migrations/versions database/{schema,scripts} docs scripts logs

touch app/__init__.py
touch app/core/__init__.py
touch app/common/__init__.py app/common/models/__init__.py app/common/repositories/__init__.py
touch app/shared/__init__.py
touch app/modules/__init__.py
touch app/modules/{health,auth,audit,media,menu,category,article}/__init__.py
```

## Nhung thu khong nen dua sang du an moi

- `.env` that
- `app.db`, `database/app.db`
- `articles_export.sql` neu chi can khung
- `logs/`
- `.venv/`
- `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`
- `__pycache__/`, `*.pyc`
- Script tam theo du lieu cu nhu `delete_users.py`, `delete_articles.py`, `reset_superadmin.py`, `test_password.py`

## Ghi chu khi copy migration

Neu chi tao khung moi, nen copy `migrations/env.py`, `script.py.mako`, `alembic.ini` va bo qua cac file trong `migrations/versions/`.
Du an moi nen tu generate migration theo model moi.

Khi chinh `migrations/env.py`, dam bao chi import cac module ton tai. Neu xoa hoac doi ten module, phai cap nhat danh sach import model trong file nay.
