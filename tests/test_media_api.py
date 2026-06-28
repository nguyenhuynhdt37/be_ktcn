"""
Integration tests for the Media Management Module API.
Tests cover:
  - APIRouter registrations
  - Logical directory creation & listing
  - File upload (Pillow thumbnailing) & download
  - Copy, Move, Rename, Delete (recursive MinIO cleanup) operations
  - S3 Presigned URLs for direct uploads & downloads
  - RBAC protection (normal users get 403)
  - Circular folder movement prevention
"""

import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image

from app.modules.auth.models import User
from app.modules.media.models import MediaItem


# ─── Mock S3 Client ───────────────────────────────────────────────────────────

class MockStreamingBody:
    def __init__(self, content: bytes):
        self.content = content

    def read(self) -> bytes:
        return self.content


class MockS3Client:
    def __init__(self) -> None:
        self.store = {}  # object_key -> (bytes, content_type)

    def head_bucket(self, Bucket: str) -> dict:
        return {}

    def create_bucket(self, Bucket: str) -> dict:
        return {}

    def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str = None) -> dict:
        self.store[Key] = (Body, ContentType)
        return {}

    def get_object(self, Bucket: str, Key: str) -> dict:
        if Key not in self.store:
            raise Exception("NoSuchKey")
        body, content_type = self.store[Key]
        return {"Body": MockStreamingBody(body), "ContentType": content_type}

    def delete_object(self, Bucket: str, Key: str) -> dict:
        self.store.pop(Key, None)
        return {}

    def copy_object(self, Bucket: str, Key: str, CopySource: dict) -> dict:
        old_key = CopySource["Key"]
        if old_key in self.store:
            self.store[Key] = self.store[old_key]
        return {}

    def generate_presigned_post(
        self, Bucket: str, Key: str, Fields: dict = None, Conditions: list = None, ExpiresIn: int = 3600
    ) -> dict:
        fields = Fields or {}
        fields["key"] = Key
        return {"url": f"http://mock-minio/{Bucket}", "fields": fields}

    def generate_presigned_url(self, ClientMethod: str, Params: dict, ExpiresIn: int = 3600) -> str:
        key = Params.get("Key", "")
        bucket = Params.get("Bucket", "")
        return f"http://mock-minio/{bucket}/{key}"


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_s3_storage(monkeypatch) -> MockS3Client:
    """
    Globally patches all boto3 S3 Client references to use the MockS3Client instead.
    """
    mock_client = MockS3Client()
    monkeypatch.setattr("app.modules.media.service.boto3.client", lambda *args, **kwargs: mock_client)
    
    # Also patch the globally-instantiated router service instance
    from app.modules.media.router import media_service
    media_service.s3_client = mock_client
    
    return mock_client


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Folder Tests ─────────────────────────────────────────────────────────────

class TestFolderManagement:
    async def test_create_folder_root(self, client: AsyncClient) -> None:
        """Kiểm tra tạo thư mục ở thư mục gốc (root)."""
        token = await _get_admin_token(client)
        resp = await client.post(
            "/api/v1/media/folders",
            json={"name": "Thư mục gốc"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Thư mục gốc"
        assert data["is_folder"] is True
        assert data["parent_id"] is None

    async def test_create_subfolder(self, client: AsyncClient) -> None:
        """Kiểm tra tạo thư mục con bên trong thư mục khác."""
        token = await _get_admin_token(client)
        
        # 1. Tạo thư mục cha
        parent_resp = await client.post(
            "/api/v1/media/folders",
            json={"name": "Folder Cha"},
            headers=_auth(token),
        )
        parent_id = parent_resp.json()["id"]

        # 2. Tạo thư mục con
        sub_resp = await client.post(
            "/api/v1/media/folders",
            json={"name": "Folder Con", "parent_id": parent_id},
            headers=_auth(token),
        )
        assert sub_resp.status_code == 200
        data = sub_resp.json()
        assert data["name"] == "Folder Con"
        assert data["parent_id"] == parent_id

    async def test_list_directory(self, client: AsyncClient) -> None:
        """Kiểm tra liệt kê danh mục."""
        token = await _get_admin_token(client)
        
        # Tạo thư mục cha
        parent_resp = await client.post(
            "/api/v1/media/folders",
            json={"name": "Folder Test List"},
            headers=_auth(token),
        )
        parent_id = parent_resp.json()["id"]

        # Tạo 2 thư mục con bên trong
        await client.post(
            "/api/v1/media/folders",
            json={"name": "A_sub", "parent_id": parent_id},
            headers=_auth(token),
        )
        await client.post(
            "/api/v1/media/folders",
            json={"name": "B_sub", "parent_id": parent_id},
            headers=_auth(token),
        )

        # Liệt kê
        list_resp = await client.get(
            f"/api/v1/media?parent_id={parent_id}",
            headers=_auth(token),
        )
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == 2
        assert items[0]["name"] == "A_sub"
        assert items[1]["name"] == "B_sub"


# ─── File Upload & Download Tests ─────────────────────────────────────────────

class TestFileTransfer:
    async def test_upload_text_file(self, client: AsyncClient, mock_s3_storage: MockS3Client) -> None:
        """Kiểm tra tải lên file text thường (không tạo thumbnail)."""
        token = await _get_admin_token(client)
        
        file_content = b"Day la noi dung file text test."
        files = {"file": ("test_file.txt", file_content, "text/plain")}
        
        resp = await client.post(
            "/api/v1/media/upload",
            files=files,
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test_file.txt"
        assert data["is_folder"] is False
        assert data["mime_type"] == "text/plain"
        assert data["size"] == len(file_content)
        assert data["thumbnail_key"] is None
        assert data["object_key"] in mock_s3_storage.store

    async def test_upload_image_with_thumbnail(self, client: AsyncClient, mock_s3_storage: MockS3Client) -> None:
        """Kiểm tra tải lên file hình ảnh (phải tạo thumbnail)."""
        token = await _get_admin_token(client)

        # Tạo file ảnh ảo bằng Pillow
        img = Image.new("RGB", (400, 400), color="red")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        files = {"file": ("test_image.png", img_bytes, "image/png")}
        resp = await client.post(
            "/api/v1/media/upload",
            files=files,
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_folder"] is False
        assert data["width"] == 400
        assert data["height"] == 400
        
        # Verify thumbnail keys were generated and uploaded
        assert data["thumbnail_key"] is not None
        assert data["thumbnail_key"] in mock_s3_storage.store
        
        # Verify thumbnail dimensions (max 200px)
        thumb_bytes = mock_s3_storage.store[data["thumbnail_key"]][0]
        thumb_img = Image.open(io.BytesIO(thumb_bytes))
        assert thumb_img.width <= 200
        assert thumb_img.height <= 200

    async def test_download_file(self, client: AsyncClient) -> None:
        """Kiểm tra tải xuống file."""
        token = await _get_admin_token(client)
        
        # Upload
        file_content = b"Binary stream data."
        files = {"file": ("data.bin", file_content, "application/octet-stream")}
        upload_resp = await client.post("/api/v1/media/upload", files=files, headers=_auth(token))
        media_id = upload_resp.json()["id"]

        # Download
        download_resp = await client.get(
            f"/api/v1/media/{media_id}/download",
            headers=_auth(token),
        )
        assert download_resp.status_code == 200
        assert download_resp.content == file_content
        assert "attachment; filename=data.bin" in download_resp.headers["Content-Disposition"]


# ─── File Operations (Rename, Move, Copy, Delete) ─────────────────────────────

class TestFileOperations:
    async def test_rename_item(self, client: AsyncClient) -> None:
        """Kiểm tra đổi tên."""
        token = await _get_admin_token(client)

        folder_resp = await client.post(
            "/api/v1/media/folders",
            json={"name": "Old Name"},
            headers=_auth(token),
        )
        media_id = folder_resp.json()["id"]

        rename_resp = await client.post(
            f"/api/v1/media/{media_id}/rename",
            json={"name": "New Name"},
            headers=_auth(token),
        )
        assert rename_resp.status_code == 200
        assert rename_resp.json()["name"] == "New Name"

    async def test_move_item(self, client: AsyncClient) -> None:
        """Kiểm tra di chuyển file/thư mục."""
        token = await _get_admin_token(client)

        # 1. Tạo thư mục A, B
        folder_a = await client.post("/api/v1/media/folders", json={"name": "Folder A"}, headers=_auth(token))
        folder_b = await client.post("/api/v1/media/folders", json={"name": "Folder B"}, headers=_auth(token))
        id_a = folder_a.json()["id"]
        id_b = folder_b.json()["id"]

        # 2. Di chuyển Folder B vào Folder A
        move_resp = await client.post(
            f"/api/v1/media/{id_b}/move",
            json={"parent_id": id_a},
            headers=_auth(token),
        )
        assert move_resp.status_code == 200
        assert move_resp.json()["parent_id"] == id_a

    async def test_circular_move_prevention(self, client: AsyncClient) -> None:
        """Không được di chuyển thư mục cha vào thư mục con của nó."""
        token = await _get_admin_token(client)

        # Tạo Folder Cha
        parent = await client.post("/api/v1/media/folders", json={"name": "Cha"}, headers=_auth(token))
        parent_id = parent.json()["id"]

        # Tạo Folder Con
        child = await client.post(
            "/api/v1/media/folders",
            json={"name": "Con", "parent_id": parent_id},
            headers=_auth(token),
        )
        child_id = child.json()["id"]

        # Di chuyển Cha vào Con (Lỗi)
        move_resp = await client.post(
            f"/api/v1/media/{parent_id}/move",
            json={"parent_id": child_id},
            headers=_auth(token),
        )
        assert move_resp.status_code == 400
        assert move_resp.json()["error"]["code"] == "CIRCULAR_MOVE_ERROR"

    async def test_copy_file(self, client: AsyncClient, mock_s3_storage: MockS3Client) -> None:
        """Kiểm tra copy file."""
        token = await _get_admin_token(client)

        # 1. Upload file gốc
        files = {"file": ("original.txt", b"content", "text/plain")}
        upload = await client.post("/api/v1/media/upload", files=files, headers=_auth(token))
        original = upload.json()
        media_id = original["id"]

        # 2. Tạo thư mục đích
        dest_folder = await client.post("/api/v1/media/folders", json={"name": "Dest"}, headers=_auth(token))
        dest_id = dest_folder.json()["id"]

        # 3. Copy sang thư mục đích
        copy_resp = await client.post(
            f"/api/v1/media/{media_id}/copy",
            json={"dest_parent_id": dest_id},
            headers=_auth(token),
        )
        assert copy_resp.status_code == 200
        copy_data = copy_resp.json()
        assert copy_data["parent_id"] == dest_id
        assert copy_data["name"] == original["name"]
        assert copy_data["object_key"] != original["object_key"]
        
        # Verify copied object exists in mock S3 store
        assert copy_data["object_key"] in mock_s3_storage.store

    async def test_delete_recursive(self, client: AsyncClient, mock_s3_storage: MockS3Client) -> None:
        """Xóa thư mục cha phải xóa sạch file con trong DB và MinIO."""
        token = await _get_admin_token(client)

        # 1. Tạo thư mục cha
        folder = await client.post("/api/v1/media/folders", json={"name": "Delete Me"}, headers=_auth(token))
        folder_id = folder.json()["id"]

        # 2. Upload file con bên trong thư mục đó
        files = {"file": ("child.txt", b"child content", "text/plain")}
        upload = await client.post(
            "/api/v1/media/upload",
            files=files,
            data={"parent_id": str(folder_id)},
            headers=_auth(token),
        )

        file_data = upload.json()
        object_key = file_data["object_key"]
        assert object_key in mock_s3_storage.store

        # 3. Xóa thư mục cha
        del_resp = await client.delete(f"/api/v1/media/{folder_id}", headers=_auth(token))
        assert del_resp.status_code == 200
        
        # Verify S3 object is physically removed
        assert object_key not in mock_s3_storage.store


# ─── Presigned URLs & RBAC Tests ──────────────────────────────────────────────

class TestURLsAndRBAC:
    async def test_get_url(self, client: AsyncClient) -> None:
        """Kiểm tra sinh URL trực tiếp."""
        token = await _get_admin_token(client)
        files = {"file": ("test.txt", b"test", "text/plain")}
        upload = await client.post("/api/v1/media/upload", files=files, headers=_auth(token))
        media_id = upload.json()["id"]

        url_resp = await client.get(f"/api/v1/media/{media_id}/url", headers=_auth(token))
        assert url_resp.status_code == 200
        assert "url" in url_resp.json()

    async def test_presigned_upload_url(self, client: AsyncClient) -> None:
        """Kiểm tra sinh presigned upload POST."""
        token = await _get_admin_token(client)
        resp = await client.post(
            "/api/v1/media/presigned-upload?filename=hello.jpg&content_type=image/jpeg",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "url" in data
        assert "fields" in data
        assert data["expires_in"] == 3600

    async def test_presigned_download_url(self, client: AsyncClient) -> None:
        """Kiểm tra sinh presigned download URL."""
        token = await _get_admin_token(client)
        files = {"file": ("test.txt", b"test", "text/plain")}
        upload = await client.post("/api/v1/media/upload", files=files, headers=_auth(token))
        media_id = upload.json()["id"]

        resp = await client.get(
            f"/api/v1/media/{media_id}/presigned-download?expires_in=600",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert "url" in resp.json()

    async def test_rbac_denial_for_normal_user(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Người dùng không có quyền bị từ chối 403."""
        from app.core.security import hash_password

        # Tạo user thường không có quyền
        normal_user = User(
            username="normal_media_user",
            email="normal_media@test.com",
            password_hash=hash_password("pass123"),
            full_name="Normal User",
            is_active=True,
        )
        db_session.add(normal_user)
        await db_session.commit()
        await db_session.refresh(normal_user)

        # Login
        login = await client.post(
            "/api/v1/auth/login",
            json={"username": "normal_media_user", "password": "pass123"},
        )
        assert login.status_code == 200
        normal_token = login.json()["access_token"]

        # Gọi API tạo folder -> 403 Forbidden
        resp = await client.post(
            "/api/v1/media/folders",
            json={"name": "Hacker Folder"},
            headers=_auth(normal_token),
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN_ACCESS"
