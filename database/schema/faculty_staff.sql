-- Faculty Staff Schema (Departments, Positions, Staffs)

-- ==========================================
-- 1. Departments (Bộ môn)
-- ==========================================
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    english_name VARCHAR(255),
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    thumbnail_object_key VARCHAR(512),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    office VARCHAR(255),
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Triggers for updated_at
CREATE TRIGGER set_timestamp_departments
BEFORE UPDATE ON departments
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

-- Indexes for departments
CREATE UNIQUE INDEX uidx_departments_slug
ON departments(slug)
WHERE deleted_at IS NULL;

CREATE INDEX idx_departments_list
ON departments(is_active, sort_order)
WHERE deleted_at IS NULL;

-- Comments for departments
COMMENT ON TABLE departments IS 'Bảng quản lý danh sách các Bộ môn / Khoa của trường';
COMMENT ON COLUMN departments.id IS 'ID định danh duy nhất (UUID)';
COMMENT ON COLUMN departments.name IS 'Tên Tiếng Việt của Bộ môn';
COMMENT ON COLUMN departments.english_name IS 'Tên Tiếng Anh của Bộ môn';
COMMENT ON COLUMN departments.slug IS 'Slug duy nhất của Bộ môn dùng cho URL';
COMMENT ON COLUMN departments.description IS 'Mô tả chi tiết về Bộ môn';
COMMENT ON COLUMN departments.thumbnail_object_key IS 'Đường dẫn key ảnh đại diện / thumbnail của bộ môn lưu trên Storage';
COMMENT ON COLUMN departments.phone IS 'Số điện thoại liên hệ';
COMMENT ON COLUMN departments.email IS 'Địa chỉ email liên hệ';
COMMENT ON COLUMN departments.website IS 'Trang web riêng của bộ môn';
COMMENT ON COLUMN departments.office IS 'Địa chỉ văn phòng làm việc';
COMMENT ON COLUMN departments.sort_order IS 'Thứ tự sắp xếp hiển thị trên giao diện';
COMMENT ON COLUMN departments.is_active IS 'Trạng thái hoạt động (True: Hoạt động, False: Tạm khóa)';
COMMENT ON COLUMN departments.created_at IS 'Thời gian tạo bản ghi';
COMMENT ON COLUMN departments.updated_at IS 'Thời gian cập nhật bản ghi gần nhất';
COMMENT ON COLUMN departments.deleted_at IS 'Thời gian xóa mềm bản ghi (Null nếu chưa bị xóa)';

-- ==========================================
-- 2. Positions (Chức vụ)
-- ==========================================
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    english_name VARCHAR(150),
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Triggers for updated_at
CREATE TRIGGER set_timestamp_positions
BEFORE UPDATE ON positions
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

-- Indexes for positions
CREATE UNIQUE INDEX uidx_positions_name
ON positions(name)
WHERE deleted_at IS NULL;

CREATE INDEX idx_positions_list
ON positions(is_active, sort_order)
WHERE deleted_at IS NULL;

-- Comments for positions
COMMENT ON TABLE positions IS 'Bảng quản lý chức vụ công tác của giảng viên';
COMMENT ON COLUMN positions.id IS 'ID định danh duy nhất (UUID)';
COMMENT ON COLUMN positions.name IS 'Tên chức vụ tiếng Việt (Ví dụ: Trưởng bộ môn, Giảng viên)';
COMMENT ON COLUMN positions.english_name IS 'Tên chức vụ tiếng Anh';
COMMENT ON COLUMN positions.description IS 'Mô tả chức năng nhiệm vụ của chức vụ';
COMMENT ON COLUMN positions.sort_order IS 'Thứ tự sắp xếp hiển thị';
COMMENT ON COLUMN positions.is_active IS 'Trạng thái hoạt động';
COMMENT ON COLUMN positions.created_at IS 'Thời gian tạo bản ghi';
COMMENT ON COLUMN positions.updated_at IS 'Thời gian cập nhật bản ghi gần nhất';
COMMENT ON COLUMN positions.deleted_at IS 'Thời gian xóa mềm bản ghi (Null nếu chưa bị xóa)';

-- ==========================================
-- 3. Staffs (Giảng viên / Cán bộ)
-- ==========================================
CREATE TABLE staffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL,
    position_id UUID NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    english_name VARCHAR(255),
    slug VARCHAR(255) NOT NULL,
    academic_title VARCHAR(50),      -- GS, PGS, TS, ThS...
    degree VARCHAR(100),             -- Tiến sĩ, Thạc sĩ...
    avatar_object_key VARCHAR(512),
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    office VARCHAR(255),
    biography TEXT,
    research_interests TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    CONSTRAINT fk_staff_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_staff_position
        FOREIGN KEY (position_id)
        REFERENCES positions(id)
        ON DELETE RESTRICT
);

-- Triggers for updated_at
CREATE TRIGGER set_timestamp_staffs
BEFORE UPDATE ON staffs
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

-- Indexes for staffs
CREATE UNIQUE INDEX uidx_staff_slug
ON staffs(slug)
WHERE deleted_at IS NULL;

CREATE INDEX idx_staff_department
ON staffs(department_id, is_active, sort_order)
WHERE deleted_at IS NULL;

CREATE INDEX idx_staff_position
ON staffs(position_id, is_active, sort_order)
WHERE deleted_at IS NULL;

CREATE INDEX idx_staff_name
ON staffs(full_name);

CREATE INDEX idx_staff_active
ON staffs(is_active)
WHERE deleted_at IS NULL;

-- Comments for staffs
COMMENT ON TABLE staffs IS 'Bảng quản lý thông tin hồ sơ của Giảng viên / Cán bộ';
COMMENT ON COLUMN staffs.id IS 'ID định danh duy nhất (UUID)';
COMMENT ON COLUMN staffs.department_id IS 'ID bộ môn quản lý giảng viên';
COMMENT ON COLUMN staffs.position_id IS 'ID chức vụ công tác của giảng viên';
COMMENT ON COLUMN staffs.full_name IS 'Họ và tên tiếng Việt';
COMMENT ON COLUMN staffs.english_name IS 'Họ và tên tiếng Anh';
COMMENT ON COLUMN staffs.slug IS 'Slug duy nhất của giảng viên phục vụ hiển thị URL chi tiết';
COMMENT ON COLUMN staffs.academic_title IS 'Học hàm (Ví dụ: GS, PGS)';
COMMENT ON COLUMN staffs.degree IS 'Học vị (Ví dụ: Tiến sĩ, Thạc sĩ)';
COMMENT ON COLUMN staffs.avatar_object_key IS 'Đường dẫn key ảnh đại diện giảng viên lưu trên Storage';
COMMENT ON COLUMN staffs.email IS 'Địa chỉ email liên hệ';
COMMENT ON COLUMN staffs.phone IS 'Số điện thoại liên hệ';
COMMENT ON COLUMN staffs.website IS 'Trang web cá nhân';
COMMENT ON COLUMN staffs.office IS 'Địa chỉ văn phòng làm việc';
COMMENT ON COLUMN staffs.biography IS 'Tiểu sử, quá trình công tác tóm tắt';
COMMENT ON COLUMN staffs.research_interests IS 'Các hướng nghiên cứu chính quan tâm';
COMMENT ON COLUMN staffs.sort_order IS 'Thứ tự hiển thị danh sách';
COMMENT ON COLUMN staffs.is_active IS 'Trạng thái hoạt động';
COMMENT ON COLUMN staffs.created_at IS 'Thời gian tạo bản ghi';
COMMENT ON COLUMN staffs.updated_at IS 'Thời gian cập nhật bản ghi gần nhất';
COMMENT ON COLUMN staffs.deleted_at IS 'Thời gian xóa mềm bản ghi (Null nếu chưa bị xóa)';
