import io
from fastapi import APIRouter, HTTPException, Response
from anyio.to_thread import run_sync

from app.core.config import settings
from app.modules.media.service import MediaService

portal_router = APIRouter()
media_service = MediaService()


@portal_router.get("/file/{object_key:path}")
async def get_media_file(
    object_key: str,
) -> Response:
    """
    Public endpoint to stream media files from MinIO.
    Allows unauthenticated access to files via their object_key.
    """
    try:
        response = await run_sync(
            lambda: media_service.s3_client.get_object(
                Bucket=settings.MINIO_BUCKET,
                Key=object_key,
            )
        )
        body = await run_sync(lambda: response["Body"].read())
        content_type = response.get("ContentType", "application/octet-stream")
        return Response(content=body, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")
