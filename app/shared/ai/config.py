import json
from pathlib import Path
from app.core.config import settings
from loguru import logger

SETTINGS_FILE = Path(__file__).parent.parent.parent / "core" / "ai_settings.json"


def get_active_model() -> str:
    """
    Đọc model chat đang hoạt động từ file cấu hình động.
    Nếu không có, fallback về cấu hình mặc định trong file .env.
    """
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_model") or settings.AI_DEFAULT_MODEL
    except Exception as e:
        logger.warning(f"Error reading dynamic active model, fallback to env: {e}")
    return settings.AI_DEFAULT_MODEL


def save_active_model(model_name: str) -> None:
    """
    Lưu model chat đang hoạt động vào file cấu hình động.
    """
    try:
        # Tạo thư mục cha nếu chưa tồn tại
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Đọc dữ liệu hiện có để tránh ghi đè mất active_embedding_model
        data = {}
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        data["active_model"] = model_name

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully saved active chat model: {model_name}")
    except Exception as e:
        logger.error(f"Error saving active model: {e}")
        raise RuntimeError(f"Could not save active model settings: {e}")


def get_active_embedding_model() -> str:
    """
    Đọc model embedding đang hoạt động từ file cấu hình động.
    Nếu không có, fallback về cấu hình mặc định trong file .env.
    """
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_embedding_model") or settings.AI_EMBEDDING_MODEL
    except Exception as e:
        logger.warning(f"Error reading dynamic active embedding model, fallback to env: {e}")
    return settings.AI_EMBEDDING_MODEL


def save_active_embedding_model(model_name: str) -> None:
    """
    Lưu model embedding đang hoạt động vào file cấu hình động.
    """
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Đọc dữ liệu hiện có để tránh ghi đè mất active_model
        data = {}
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        data["active_embedding_model"] = model_name

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully saved active embedding model: {model_name}")
    except Exception as e:
        logger.error(f"Error saving active embedding model: {e}")
        raise RuntimeError(f"Could not save active embedding model settings: {e}")
