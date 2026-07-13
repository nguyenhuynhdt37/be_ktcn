#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CLEAR='\033[0m'

BACKUP_DIR="backups"

echo -e "${BLUE}=== BẮT ĐẦU NẠP (RESTORE) DATABASE VÀ MINIO ===${CLEAR}"

# 1. Kiểm tra các container có đang chạy không
if ! docker ps | grep -q "be_postgres" || ! docker ps | grep -q "be_minio"; then
    echo -e "${RED}Lỗi: Các container be_postgres hoặc be_minio chưa chạy. Hãy chạy docker compose up -d trước!${CLEAR}"
    exit 1
fi

# 2. Kiểm tra sự tồn tại của tệp tin backup
if [ ! -f "$BACKUP_DIR/db_backup.sql" ]; then
    echo -e "${RED}Lỗi: Không tìm thấy file backup $BACKUP_DIR/db_backup.sql${CLEAR}"
    exit 1
fi

# 3. Restore PostgreSQL
echo -e "${YELLOW}[1/2] Đang làm sạch và nạp dữ liệu PostgreSQL...${CLEAR}"
# Xóa schema cũ để tránh xung đột dữ liệu
docker exec -i be_postgres psql -U postgres -d university_cms -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
# Nạp lại dữ liệu
docker exec -i be_postgres psql -U postgres -d university_cms < "$BACKUP_DIR/db_backup.sql" > /dev/null
echo -e "${GREEN}✓ Đã nạp database thành công!${CLEAR}"

# 4. Restore MinIO
echo -e "${YELLOW}[2/2] Đang nạp dữ liệu tệp tin vào MinIO...${CLEAR}"
if [ -f "$BACKUP_DIR/minio_backup.tar.gz" ]; then
    echo -e "${YELLOW}Đang giải nén dữ liệu MinIO...${CLEAR}"
    rm -rf "$BACKUP_DIR/minio_temp"
    mkdir -p "$BACKUP_DIR/minio_temp"
    tar -xzf "$BACKUP_DIR/minio_backup.tar.gz" -C "$BACKUP_DIR/minio_temp"

    docker run --rm \
      --entrypoint sh \
      --network be_default \
      -v "$(pwd)/$BACKUP_DIR/minio_temp:/backup" \
      minio/mc -c "
        mc alias set myminio http://minio:9000 minio_admin minio_password && \
        mc mb --ignore-existing myminio/university-media && \
        mc mirror --overwrite /backup/university-media myminio/university-media
      "
    
    # Dọn dẹp thư mục tạm
    rm -rf "$BACKUP_DIR/minio_temp"
    echo -e "${GREEN}✓ Đã nạp dữ liệu MinIO thành công!${CLEAR}"
elif [ -d "$BACKUP_DIR/minio_backup/university-media" ]; then
    echo -e "${YELLOW}Phát hiện thư mục backup cũ, đang tiến hành nạp...${CLEAR}"
    docker run --rm \
      --entrypoint sh \
      --network be_default \
      -v "$(pwd)/$BACKUP_DIR/minio_backup:/backup" \
      minio/mc -c "
        mc alias set myminio http://minio:9000 minio_admin minio_password && \
        mc mb --ignore-existing myminio/university-media && \
        mc mirror --overwrite /backup/university-media myminio/university-media
      "
    echo -e "${GREEN}✓ Đã nạp dữ liệu MinIO thành công!${CLEAR}"
else
    echo -e "${YELLOW}Cảnh báo: Không tìm thấy tệp nén $BACKUP_DIR/minio_backup.tar.gz hoặc thư mục cũ, bỏ qua bước này.${CLEAR}"
fi

echo -e "${GREEN}=== NẠP DỮ LIỆU HOÀN TẤT THÀNH CÔNG! ===${CLEAR}"
