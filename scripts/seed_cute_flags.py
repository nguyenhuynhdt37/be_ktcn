import asyncio
import os
import uuid
import boto3
from botocore.client import Config
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.modules.media.models import MediaItem
from app.modules.language.models import Language

VI_IMG = "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/vietnam_cropped.png"
EN_IMG = "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/uk_cropped.png"
LO_IMG = "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/laos_cropped.png"

async def main():
    print("🚀 Bắt đầu chạy seed quốc kỳ chuyên nghiệp...")
    
    # 1. Khởi tạo S3 Client kết nối MinIO
    protocol = "https" if settings.MINIO_SECURE else "http"
    s3_client = boto3.client(
        "s3",
        endpoint_url=f"{protocol}://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )
    
    bucket_name = settings.MINIO_BUCKET
    
    # Đảm bảo bucket tồn tại
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception:
        print(f"Bucket '{bucket_name}' chưa tồn tại, tiến hành tạo mới...")
        s3_client.create_bucket(Bucket=bucket_name)
    
    # Các file cần upload
    flags_data = [
        {"code": "vi", "path": VI_IMG, "name": "vietnam.png", "key": "flags/vietnam.png"},
        {"code": "en", "path": EN_IMG, "name": "uk.png", "key": "flags/uk.png"},
        {"code": "lo", "path": LO_IMG, "name": "laos.png", "key": "flags/laos.png"}
    ]
    
    # 2. Upload file lên MinIO
    uploaded_items = {}
    for item in flags_data:
        file_path = item["path"]
        if not os.path.exists(file_path):
            print(f"❌ File không tồn tại: {file_path}")
            return
            
        file_size = os.path.getsize(file_path)
        
        # Upload
        print(f"📤 Đang upload {item['name']} lên MinIO ({item['key']})...")
        with open(file_path, "rb") as f:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=item["key"],
                Body=f,
                ContentType="image/png"
            )
        
        uploaded_items[item["code"]] = {
            "name": item["name"],
            "object_key": item["key"],
            "size": file_size
        }
        print(f"✅ Upload thành công: {item['name']}")

    # 3. Kết nối CSDL và tạo MediaItem & cập nhật Language
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        async with session.begin():
            # Dọn dẹp các flag cũ để tránh trùng lặp bản ghi rác
            for code in ["vi", "en", "lo"]:
                # Lấy language hiện tại
                q = select(Language).where(Language.code == code)
                res = await session.execute(q)
                lang = res.scalar_one_or_none()
                if lang and lang.flag_id:
                    old_flag_id = lang.flag_id
                    lang.flag_id = None
                    session.add(lang)
                    # Xóa media item cũ
                    await session.execute(delete(MediaItem).where(MediaItem.id == old_flag_id))
                    print(f"🧹 Đã dọn dẹp flag_id cũ của ngôn ngữ '{code}'")

            for code, data in uploaded_items.items():
                # Tạo MediaItem trong DB
                media_id = uuid.uuid4()
                media_item = MediaItem(
                    id=media_id,
                    name=data["name"],
                    is_folder=False,
                    object_key=data["object_key"],
                    bucket=bucket_name,
                    mime_type="image/png",
                    size=data["size"]
                )
                session.add(media_item)
                print(f"💾 Đã tạo MediaItem: ID={media_id}, Name={data['name']}")
                
                # Cập nhật Language
                query = select(Language).where(Language.code == code)
                res = await session.execute(query)
                lang = res.scalar_one_or_none()
                
                if lang:
                    lang.flag_id = media_id
                    session.add(lang)
                    print(f"✏️ Đã gán flag_id cho ngôn ngữ '{code}' -> ID={media_id}")
                else:
                    print(f"⚠️ Không tìm thấy ngôn ngữ '{code}' trong DB để cập nhật!")
                    
        await session.commit()
    
    print("🎉 Hoàn tất seed quốc kỳ chuyên nghiệp thành công!")

if __name__ == "__main__":
    asyncio.run(main())
