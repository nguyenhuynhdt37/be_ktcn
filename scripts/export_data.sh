#!/bin/bash
set -e

# Màu sắc hiển thị
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CLEAR='\033[0m'

BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}=== BẮT ĐẦU XUẤT (BACKUP) DATABASE VÀ MINIO ===${CLEAR}"

# 1. Kiểm tra các container có đang chạy không
if ! docker ps | grep -q "be_postgres" || ! docker ps | grep -q "be_minio"; then
    echo -e "${RED}Lỗi: Các container be_postgres hoặc be_minio chưa chạy. Hãy chạy docker compose up -d trước!${CLEAR}"
    exit 1
fi

# 2. Backup PostgreSQL
echo -e "${YELLOW}[1/2] Đang xuất cơ sở dữ liệu PostgreSQL...${CLEAR}"
docker exec -t be_postgres pg_dump -U postgres -d university_cms > "$BACKUP_DIR/db_backup.sql"
echo -e "${GREEN}✓ Đã xuất database thành công: $BACKUP_DIR/db_backup.sql${CLEAR}"

# 3. Backup MinIO
echo -e "${YELLOW}[2/2] Đang xuất dữ liệu tệp tin từ MinIO...${CLEAR}"
docker run --rm \
  --entrypoint sh \
  --network be_default \
  -v "$(pwd)/$BACKUP_DIR/minio_backup:/backup" \
  minio/mc -c "
    mc alias set myminio http://minio:9000 minio_admin minio_password && \
    mc mirror --overwrite myminio/university-media /backup/university-media
  "

echo -e "${GREEN}✓ Đã xuất dữ liệu MinIO thành công vào thư mục: $BACKUP_DIR/minio_backup/${CLEAR}"
echo -e "${GREEN}=== XUẤT DỮ LIỆU HOÀN TẤT THÀNH CÔNG! ===${CLEAR}"
