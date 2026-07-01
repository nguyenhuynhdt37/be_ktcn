import asyncio
import time
from loguru import logger
import sys

# Cấu hình logger
logger.remove()
logger.add(sys.stderr, level="INFO")

# Đoạn văn bản mẫu khoảng 200 từ tiếng Việt (khoảng 1100 ký tự)
SAMPLE_TEXT = (
    "Trường Đại học Công nghệ thông tin và Truyền thông là một trong những cơ sở giáo dục hàng đầu "
    "cả nước về đào tạo và nghiên cứu trong lĩnh vực công nghệ. Với sứ mệnh cung cấp nguồn nhân lực "
    "chất lượng cao, trường không ngừng cải tiến chương trình đào tạo, đầu tư trang thiết bị hiện đại "
    "và đẩy mạnh hợp tác quốc tế. Sinh viên tại trường được học tập trong môi trường năng động, "
    "sáng tạo với sự hướng dẫn của đội ngũ giảng viên giàu kinh nghiệm. Ngoài ra, nhà trường còn chú trọng "
    "đến việc phát triển kỹ năng mềm và tạo cơ hội thực tập tại các doanh nghiệp công nghệ lớn. Nhờ đó, "
    "tỷ lệ sinh viên có việc làm ngay sau khi tốt nghiệp luôn đạt mức cao, khẳng định uy tín và vị thế của "
    "nhà trường trong hệ thống giáo dục đại học. Trong những năm tới, trường đặt mục tiêu trở thành một "
    "trung tâm nghiên cứu khoa học tiên tiến và chuyển giao công nghệ hàng đầu khu vực."
)

async def run_benchmark():
    from app.modules.translation import translation_service
    
    # Tính số từ
    word_count = len(SAMPLE_TEXT.split())
    char_count = len(SAMPLE_TEXT)
    
    logger.info(f"📝 Đoạn văn bản benchmark: {word_count} từ ({char_count} ký tự)")
    
    logger.info("⏳ 1. Khởi động và warmup model...")
    translation_service.warmup()
    
    logger.info("🤖 2. Bắt đầu dịch Việt -> Anh...")
    start_en = time.time()
    en_result = await translation_service.translate_text(SAMPLE_TEXT, ["en"])
    duration_en = time.time() - start_en
    logger.info(f"✨ [EN] Dịch xong trong {duration_en:.2f} giây.")
    
    logger.info("🤖 3. Bắt đầu dịch Việt -> Lào...")
    start_lo = time.time()
    lo_result = await translation_service.translate_text(SAMPLE_TEXT, ["lo"])
    duration_lo = time.time() - start_lo
    logger.info(f"✨ [LO] Dịch xong trong {duration_lo:.2f} giây.")
    
    logger.info("=" * 60)
    logger.info(f"📊 KẾT QUẢ BENCHMARK (Độ dài: {word_count} từ / {char_count} ký tự):")
    logger.info(f"- Thời gian dịch sang tiếng Anh (en): {duration_en:.3f} giây (tốc độ: {word_count / duration_en:.1f} từ/giây)")
    logger.info(f"- Thời gian dịch sang tiếng Lào (lo): {duration_lo:.3f} giây (tốc độ: {word_count / duration_lo:.1f} từ/giây)")
    logger.info(f"- Tổng thời gian dịch ra cả 2 ngôn ngữ: {duration_en + duration_lo:.3f} giây")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
