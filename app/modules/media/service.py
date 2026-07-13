import hashlib
import io
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import boto3
from botocore.config import Config
from loguru import logger
from PIL import Image
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from anyio.to_thread import run_sync

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.media.models import MediaItem


def validate_magic_bytes(content: bytes, content_type: str) -> bool:
    """
    Validates that the file contents match the expected MIME type signature (Magic Bytes).
    """
    if not content:
        return False
        
    # Standard signatures (Magic Bytes)
    if content_type.startswith("image/png"):
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    elif content_type.startswith("image/jpeg") or content_type.startswith("image/jpg"):
        return content.startswith(b"\xff\xd8\xff")
    elif content_type.startswith("image/gif"):
        return content.startswith(b"GIF87a") or content.startswith(b"GIF89a")
    elif content_type == "application/pdf":
        return content.startswith(b"%PDF")
    elif content_type == "image/svg+xml" or content_type.endswith("svg+xml"):
        try:
            text = content[:1000].decode("utf-8", errors="ignore").lower()
            return "<svg" in text
        except Exception:
            return False
            
    # Allow other files without validation (like docx, xlsx, etc. or dynamic validation)
    return True


def check_svg_safety(content: bytes) -> bool:
    """
    Scans SVG content for potential XSS payloads like script tags or onload attributes.
    """
    try:
        text = content.decode("utf-8", errors="ignore").lower()
        dangerous_patterns = [
            "<script", "javascript:", "onload=", "onerror=", 
            "onclick=", "onmouseover=", "onfocus=", "onblur="
        ]
        for pattern in dangerous_patterns:
            if pattern in text:
                return False
        return True
    except Exception:
        return False


def sanitize_image_metadata(file_content: bytes) -> tuple[bytes, int, int]:
    """
    Loads image with Pillow, strips EXIF metadata, and returns clean bytes, width, and height.
    Runs inside a threadpool.
    """
    img = Image.open(io.BytesIO(file_content))
    
    # Auto rotate based on EXIF orientation if available
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    width, height = img.width, img.height
    
    # Re-save to strip metadata (EXIF is not passed)
    out_io = io.BytesIO()
    img_format = img.format or "PNG"
    img.save(out_io, format=img_format)
    return out_io.getvalue(), width, height


class MediaService:
    """
    Independent Media Management Service.
    Encapsulates all logic for MinIO storage interaction and database file metadata.
    """

    def __init__(self) -> None:
        # Initialize boto3 S3 Client configured for MinIO
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"http{'s' if settings.MINIO_SECURE else ''}://{settings.MINIO_INTERNAL_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """
        Validates default bucket existence and attempts auto-creation if missing.
        Configures public read policy for media retrieval.
        """
        import json
        bucket_name = settings.MINIO_BUCKET
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except Exception:
            try:
                self.s3_client.create_bucket(Bucket=bucket_name)
                logger.info(f"Đã tự động tạo MinIO bucket: '{bucket_name}'")
            except Exception as e:
                logger.warning(
                    f"Không thể kiểm tra hoặc tạo bucket '{bucket_name}': {e}. "
                    "Hãy chắc chắn MinIO service đang chạy."
                )
                return

        # Set public read policy so browser can access uploaded files
        try:
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                    }
                ]
            }
            self.s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        except Exception as e:
            logger.warning(f"Không thể cập nhật policy cho bucket '{bucket_name}': {e}")

    # ─── Folder Management ────────────────────────────────────────────────────

    async def create_folder(
        self, db: AsyncSession, name: str, parent_id: Optional[uuid.UUID] = None
    ) -> MediaItem:
        """
        Creates a logical directory in the database.
        """
        if parent_id:
            await self._verify_parent_exists_and_is_folder(db, parent_id)

        folder = MediaItem(
            name=name,
            is_folder=True,
            parent_id=parent_id,
        )
        db.add(folder)
        await db.commit()
        await db.refresh(folder)
        return folder

    async def list_directory(
        self, db: AsyncSession, parent_id: Optional[uuid.UUID] = None
    ) -> List[MediaItem]:
        """
        Lists files and subdirectories located inside a specific parent folder.
        """
        if parent_id:
            await self._verify_parent_exists_and_is_folder(db, parent_id)

        stmt = (
            select(MediaItem)
            .where(MediaItem.parent_id == parent_id)
            .order_by(MediaItem.is_folder.desc(), MediaItem.name.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # ─── File Management ──────────────────────────────────────────────────────

    async def upload_file(
        self,
        db: AsyncSession,
        file_content: bytes,
        filename: str,
        content_type: str,
        parent_id: Optional[uuid.UUID] = None,
    ) -> MediaItem:
        """
        Uploads file to MinIO, calculates metadata/dimensions, generates thumbnail if image,
        and saves registry to Database.
        """
        if parent_id:
            await self._verify_parent_exists_and_is_folder(db, parent_id)

        # 0. Security Validations
        # Validate Magic Bytes (File Signatures)
        if not validate_magic_bytes(file_content, content_type):
            raise BadRequestException(
                message="Nội dung tập tin không khớp với định dạng được khai báo.",
                error_code="INVALID_FILE_SIGNATURE",
            )

        # SVG Protection against script/XSS injection
        if content_type == "image/svg+xml" or content_type.endswith("svg+xml"):
            if not check_svg_safety(file_content):
                raise BadRequestException(
                    message="Tập tin SVG không an toàn, chứa mã độc hại.",
                    error_code="UNSAFE_SVG_FILE",
                )

        # 1. Image Sanitization (Strip EXIF & Re-encode)
        width, height = None, None
        thumbnail_key = None

        if content_type.startswith("image/") and not content_type.endswith("svg+xml"):
            try:
                # Sanitize original image (Remove EXIF)
                file_content, width, height = await run_sync(
                    sanitize_image_metadata, file_content
                )
            except Exception as e:
                logger.error(f"Lỗi khi xóa siêu dữ liệu ảnh: {e}")
                raise BadRequestException(
                    message="Tập tin hình ảnh không hợp lệ hoặc bị lỗi.",
                    error_code="INVALID_IMAGE_FILE",
                )

        # Compute checksum and file details after sanitization
        size = len(file_content)
        checksum = hashlib.md5(file_content).hexdigest()

        # 2. Extract image thumbnail
        if content_type.startswith("image/") and not content_type.endswith("svg+xml"):
            try:
                # Run Image parsing on thread pool to keep event loop responsive
                _, _, thumbnail_bytes = await run_sync(
                    self._process_image_and_thumbnail, file_content
                )
                
                # If thumbnail was generated, upload to MinIO
                if thumbnail_bytes:
                    thumb_key = f"thumbs/{uuid.uuid4().hex}"
                    await run_sync(
                        lambda: self.s3_client.put_object(
                            Bucket=settings.MINIO_BUCKET,
                            Key=thumb_key,
                            Body=thumbnail_bytes,
                            ContentType=content_type,
                        )
                    )
                    thumbnail_key = thumb_key
            except Exception as e:
                logger.warning(f"Không thể tạo thumbnail cho '{filename}': {e}")

        # 3. Upload original file to MinIO S3
        object_key = f"files/{uuid.uuid4().hex}"
        await run_sync(
            lambda: self.s3_client.put_object(
                Bucket=settings.MINIO_BUCKET,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
            )
        )

        # 4. Save to Database
        media_item = MediaItem(
            name=filename,
            is_folder=False,
            parent_id=parent_id,
            object_key=object_key,
            thumbnail_key=thumbnail_key,
            bucket=settings.MINIO_BUCKET,
            mime_type=content_type,
            size=size,
            checksum=checksum,
            width=width,
            height=height,
        )
        db.add(media_item)
        await db.commit()
        await db.refresh(media_item)
        return media_item

    def _process_image_and_thumbnail(self, file_content: bytes) -> tuple[int, int, Optional[bytes]]:
        """
        Extracts width/height and generates a max 200px thumbnail.
        Runs inside threadpool.
        """
        img = Image.open(io.BytesIO(file_content))
        width, height = img.width, img.height

        # Copy image and resize
        img_copy = img.copy()
        img_copy.thumbnail((200, 200))
        
        # Save thumbnail to buffer
        thumb_io = io.BytesIO()
        # Default to PNG if format is missing
        img_format = img.format or "PNG"
        img_copy.save(thumb_io, format=img_format)
        
        return width, height, thumb_io.getvalue()

    async def get_file_stream(self, db: AsyncSession, media_id: uuid.UUID) -> tuple[bytes, str, str]:
        """
        Retrieves a file's binary content, name, and mime-type for download.
        """
        item = await self._get_item_or_raise(db, media_id)
        if item.is_folder:
            raise BadRequestException(
                message="Không thể tải xuống thư mục trực tiếp",
                error_code="DOWNLOAD_DIRECTORY_ERROR",
            )

        try:
            response = await run_sync(
                lambda: self.s3_client.get_object(
                    Bucket=item.bucket or settings.MINIO_BUCKET,
                    Key=item.object_key,
                )
            )
            # Read streaming body into memory
            body = await run_sync(lambda: response["Body"].read())
            return body, item.name, item.mime_type or "application/octet-stream"
        except Exception as e:
            logger.error(f"Lỗi tải xuống file vật lý từ MinIO: {e}")
            raise BadRequestException(
                message="Lỗi truy xuất file từ hệ thống lưu trữ",
                error_code="STORAGE_RETRIEVAL_ERROR",
            )

    # ─── Operations (Delete, Move, Copy, Rename) ──────────────────────────────

    async def delete_item(self, db: AsyncSession, media_id: uuid.UUID) -> None:
        """
        Deletes a file or directory recursively.
        Physically removes S3 objects before database deletion.
        """
        item = await self._get_item_or_raise(db, media_id)

        # 1. Collect files to delete in MinIO
        files_to_delete: List[MediaItem] = []
        if item.is_folder:
            # Recursively collect all descendant files
            await self._collect_descendant_files(db, item.id, files_to_delete)
        else:
            files_to_delete.append(item)

        # 2. Delete S3 objects
        for file in files_to_delete:
            if file.object_key:
                try:
                    await run_sync(
                        lambda: self.s3_client.delete_object(
                            Bucket=file.bucket or settings.MINIO_BUCKET,
                            Key=file.object_key,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Lỗi xóa file '{file.object_key}' từ MinIO: {e}")
            
            if file.thumbnail_key:
                try:
                    await run_sync(
                        lambda: self.s3_client.delete_object(
                            Bucket=file.bucket or settings.MINIO_BUCKET,
                            Key=file.thumbnail_key,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Lỗi xóa thumbnail '{file.thumbnail_key}' từ MinIO: {e}")

        # 3. Delete database record(s) - cascade handles child rows in DB
        await db.delete(item)
        await db.commit()

    async def rename_item(self, db: AsyncSession, media_id: uuid.UUID, new_name: str) -> MediaItem:
        """
        Renames a logical file or directory (DB-only operation).
        """
        item = await self._get_item_or_raise(db, media_id)
        item.name = new_name
        item.updated_at = datetime.now(timezone.utc)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def move_item(
        self, db: AsyncSession, media_id: uuid.UUID, new_parent_id: Optional[uuid.UUID]
    ) -> MediaItem:
        """
        Moves a file or directory to a different folder.
        Includes cyclic hierarchy detection.
        """
        item = await self._get_item_or_raise(db, media_id)

        if new_parent_id:
            # 1. Verify destination exists and is a folder
            await self._verify_parent_exists_and_is_folder(db, new_parent_id)
            
            # 2. Prevent circular move (cannot move folder inside itself or its descendants)
            if item.is_folder:
                is_descendant = await self._is_folder_descendant_of(db, new_parent_id, item.id)
                if media_id == new_parent_id or is_descendant:
                    raise BadRequestException(
                        message="Không thể di chuyển thư mục vào chính nó hoặc thư mục con của nó",
                        error_code="CIRCULAR_MOVE_ERROR",
                    )

        item.parent_id = new_parent_id
        item.updated_at = datetime.now(timezone.utc)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def copy_file(
        self, db: AsyncSession, media_id: uuid.UUID, dest_parent_id: Optional[uuid.UUID] = None
    ) -> MediaItem:
        """
        Copies a file: Duplicates the MinIO object and inserts a new DB record.
        If copying a folder, it will recursively duplicate all files and nested structure.
        """
        item = await self._get_item_or_raise(db, media_id)

        if dest_parent_id:
            await self._verify_parent_exists_and_is_folder(db, dest_parent_id)

        if not item.is_folder:
            # 1. Copy S3 objects
            new_object_key = f"files/{uuid.uuid4().hex}"
            try:
                await run_sync(
                    lambda: self.s3_client.copy_object(
                        Bucket=settings.MINIO_BUCKET,
                        Key=new_object_key,
                        CopySource={"Bucket": item.bucket or settings.MINIO_BUCKET, "Key": item.object_key},
                    )
                )
            except Exception as e:
                logger.error(f"Lỗi sao chép file vật lý trong MinIO: {e}")
                raise BadRequestException(
                    message="Không thể sao chép tệp tin trên hệ thống lưu trữ",
                    error_code="STORAGE_COPY_ERROR",
                )

            new_thumbnail_key = None
            if item.thumbnail_key:
                new_thumbnail_key = f"thumbs/{uuid.uuid4().hex}"
                try:
                    await run_sync(
                        lambda: self.s3_client.copy_object(
                            Bucket=settings.MINIO_BUCKET,
                            Key=new_thumbnail_key,
                            CopySource={"Bucket": item.bucket or settings.MINIO_BUCKET, "Key": item.thumbnail_key},
                        )
                    )
                except Exception as e:
                    logger.warning(f"Lỗi sao chép ảnh thumbnail trong MinIO: {e}")

            # 2. Save DB copy
            copied_item = MediaItem(
                name=f"Copy of {item.name}" if dest_parent_id == item.parent_id else item.name,
                is_folder=False,
                parent_id=dest_parent_id,
                object_key=new_object_key,
                thumbnail_key=new_thumbnail_key,
                bucket=settings.MINIO_BUCKET,
                mime_type=item.mime_type,
                size=item.size,
                checksum=item.checksum,
                width=item.width,
                height=item.height,
            )
            db.add(copied_item)
            await db.commit()
            await db.refresh(copied_item)
            return copied_item

        else:
            # Recursively copy directory
            return await self._recursive_copy_folder(db, item, dest_parent_id)

    async def _recursive_copy_folder(
        self, db: AsyncSession, source_folder: MediaItem, dest_parent_id: Optional[uuid.UUID]
    ) -> MediaItem:
        """
        Recursively copies a folder structure.
        """
        # Create destination folder
        new_folder = MediaItem(
            name=f"Copy of {source_folder.name}" if dest_parent_id == source_folder.parent_id else source_folder.name,
            is_folder=True,
            parent_id=dest_parent_id,
        )
        db.add(new_folder)
        await db.flush()

        # Load child items of source_folder
        stmt = select(MediaItem).where(MediaItem.parent_id == source_folder.id)
        result = await db.execute(stmt)
        children = result.scalars().all()

        for child in children:
            if child.is_folder:
                await self._recursive_copy_folder(db, child, new_folder.id)
            else:
                # Copy file S3 objects
                new_object_key = f"files/{uuid.uuid4().hex}"
                await run_sync(
                    lambda: self.s3_client.copy_object(
                        Bucket=settings.MINIO_BUCKET,
                        Key=new_object_key,
                        CopySource={"Bucket": child.bucket or settings.MINIO_BUCKET, "Key": child.object_key},
                    )
                )
                
                new_thumbnail_key = None
                if child.thumbnail_key:
                    new_thumbnail_key = f"thumbs/{uuid.uuid4().hex}"
                    await run_sync(
                        lambda: self.s3_client.copy_object(
                            Bucket=settings.MINIO_BUCKET,
                            Key=new_thumbnail_key,
                            CopySource={"Bucket": child.bucket or settings.MINIO_BUCKET, "Key": child.thumbnail_key},
                        )
                    )

                copied_file = MediaItem(
                    name=child.name,
                    is_folder=False,
                    parent_id=new_folder.id,
                    object_key=new_object_key,
                    thumbnail_key=new_thumbnail_key,
                    bucket=settings.MINIO_BUCKET,
                    mime_type=child.mime_type,
                    size=child.size,
                    checksum=child.checksum,
                    width=child.width,
                    height=child.height,
                )
                db.add(copied_file)

        await db.commit()
        await db.refresh(new_folder)
        return new_folder

    # ─── S3 URL Operations ────────────────────────────────────────────────────

    async def get_url(self, db: AsyncSession, media_id: uuid.UUID) -> str:
        """
        Retrieves direct public link of S3 object.
        """
        item = await self._get_item_or_raise(db, media_id)
        if item.is_folder:
            raise BadRequestException(
                message="Thư mục không có đường dẫn URL file trực tiếp",
                error_code="DIRECTORY_URL_ERROR",
            )
        
        return f"/api/v1/portal/media/file/{item.object_key}"

    async def generate_presigned_upload_url(
        self, filename: str, content_type: str, expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Generates S3 Presigned POST URL for direct client S3 file uploads.
        """
        object_key = f"files/{uuid.uuid4().hex}"
        
        response = await run_sync(
            lambda: self.s3_client.generate_presigned_post(
                Bucket=settings.MINIO_BUCKET,
                Key=object_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["starts-with", "$key", "files/"]
                ],
                ExpiresIn=expires_in
            )
        )
        return {
            "url": response["url"],
            "fields": response["fields"],
            "expires_in": expires_in,
        }

    async def generate_presigned_download_url(
        self, db: AsyncSession, media_id: uuid.UUID, expires_in: int = 3600
    ) -> str:
        """
        Generates a temporary secure presigned download link.
        """
        item = await self._get_item_or_raise(db, media_id)
        if item.is_folder:
            raise BadRequestException(
                message="Không thể tạo mã tải xuống cho thư mục",
                error_code="DIRECTORY_PRESIGNED_ERROR",
            )

        url = await run_sync(
            lambda: self.s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": item.bucket or settings.MINIO_BUCKET, "Key": item.object_key},
                ExpiresIn=expires_in
            )
        )
        return url

    # ─── Internal Helpers ─────────────────────────────────────────────────────

    async def _get_item_or_raise(self, db: AsyncSession, media_id: uuid.UUID) -> MediaItem:
        stmt = select(MediaItem).where(MediaItem.id == media_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException(
                message="Tài nguyên media không tồn tại",
                error_code="MEDIA_NOT_FOUND",
            )
        return item

    async def _verify_parent_exists_and_is_folder(self, db: AsyncSession, parent_id: uuid.UUID) -> None:
        parent = await self._get_item_or_raise(db, parent_id)
        if not parent.is_folder:
            raise BadRequestException(
                message="ID cha được chỉ định phải là một thư mục",
                error_code="NOT_A_DIRECTORY_ERROR",
            )

    async def _collect_descendant_files(
        self, db: AsyncSession, folder_id: uuid.UUID, accumulator: List[MediaItem]
    ) -> None:
        """
        Recursively collects all child file items inside a folder.
        """
        stmt = select(MediaItem).where(MediaItem.parent_id == folder_id)
        result = await db.execute(stmt)
        children = result.scalars().all()
        for child in children:
            if child.is_folder:
                await self._collect_descendant_files(db, child.id, accumulator)
            else:
                accumulator.append(child)

    async def _is_folder_descendant_of(
        self, db: AsyncSession, folder_id: uuid.UUID, ancestor_id: uuid.UUID
    ) -> bool:
        """
        Verifies if 'folder_id' is located inside 'ancestor_id' hierarchy.
        Prevents circular references.
        """
        current_id: Optional[uuid.UUID] = folder_id
        while current_id is not None:
            if current_id == ancestor_id:
                return True
            stmt = select(MediaItem.parent_id).where(MediaItem.id == current_id)
            result = await db.execute(stmt)
            current_id = result.scalar_one_or_none()
        return False
