-- SQL SCHEMA TOÀN HỆ THỐNG (POSTGRESQL DIALECT)
-- Tự động trích xuất từ SQLAlchemy Models của dự án
-- Ngày tạo: 2026-06-30

CREATE TABLE banners (
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	desktop_image_object_key VARCHAR(512) NOT NULL, 
	mobile_image_object_key VARCHAR(512), 
	link_url VARCHAR(1000), 
	open_in_new_tab BOOLEAN NOT NULL, 
	position banner_position NOT NULL, 
	sort_order INTEGER NOT NULL, 
	start_at TIMESTAMP WITH TIME ZONE, 
	end_at TIMESTAMP WITH TIME ZONE, 
	is_active BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE departments (
	name VARCHAR(255) NOT NULL, 
	english_name VARCHAR(255), 
	slug VARCHAR(255) NOT NULL, 
	description TEXT, 
	thumbnail_object_key VARCHAR(512), 
	phone VARCHAR(50), 
	email VARCHAR(255), 
	website VARCHAR(255), 
	office VARCHAR(255), 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE media_items (
	name VARCHAR(255) NOT NULL, 
	is_folder BOOLEAN NOT NULL, 
	parent_id UUID, 
	object_key VARCHAR(512), 
	thumbnail_key VARCHAR(512), 
	bucket VARCHAR(255), 
	mime_type VARCHAR(100), 
	size BIGINT, 
	checksum VARCHAR(64), 
	width INTEGER, 
	height INTEGER, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES media_items (id) ON DELETE CASCADE
);

CREATE TABLE menus (
	name VARCHAR(100) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	description TEXT, 
	is_active BOOLEAN NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);

CREATE TABLE positions (
	name VARCHAR(150) NOT NULL, 
	english_name VARCHAR(150), 
	description TEXT, 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE tags (
	name VARCHAR(100) NOT NULL, 
	slug VARCHAR(100) NOT NULL, 
	description TEXT, 
	color VARCHAR(7), 
	usage_count INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE menu_items (
	menu_id UUID NOT NULL, 
	parent_id UUID, 
	title VARCHAR(255) NOT NULL, 
	target_type VARCHAR(13), 
	target_id UUID, 
	external_url VARCHAR(500), 
	open_in_new_tab BOOLEAN NOT NULL, 
	icon VARCHAR(100), 
	depth INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	is_visible BOOLEAN NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT chk_menu_items_depth CHECK (depth >= 1 AND depth <= 3), 
	CONSTRAINT chk_menu_items_target_consistency CHECK (
            (target_type = 'EXTERNAL_LINK' AND external_url IS NOT NULL AND target_id IS NULL)
            OR (target_type IS NOT NULL AND target_type != 'EXTERNAL_LINK' AND target_id IS NOT NULL AND external_url IS NULL)
            OR (target_type IS NULL AND target_id IS NULL AND external_url IS NULL)
            ), 
	FOREIGN KEY(menu_id) REFERENCES menus (id) ON DELETE CASCADE, 
	FOREIGN KEY(parent_id) REFERENCES menu_items (id) ON DELETE CASCADE
);

CREATE TABLE staffs (
	department_id UUID NOT NULL, 
	position_id UUID NOT NULL, 
	full_name VARCHAR(255) NOT NULL, 
	english_name VARCHAR(255), 
	slug VARCHAR(255) NOT NULL, 
	academic_title VARCHAR(50), 
	degree VARCHAR(100), 
	avatar_object_key VARCHAR(512), 
	email VARCHAR(255), 
	phone VARCHAR(50), 
	website VARCHAR(255), 
	office VARCHAR(255), 
	biography TEXT, 
	research_interests TEXT, 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT, 
	FOREIGN KEY(position_id) REFERENCES positions (id) ON DELETE RESTRICT
);

CREATE TABLE users (
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20), 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	avatar_url VARCHAR(500), 
	is_active BOOLEAN NOT NULL, 
	last_login TIMESTAMP WITH TIME ZONE, 
	email_verified_at TIMESTAMP WITH TIME ZONE, 
	password_changed_at TIMESTAMP WITH TIME ZONE, 
	bio TEXT, 
	title VARCHAR(100), 
	avatar_id UUID, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email), 
	FOREIGN KEY(avatar_id) REFERENCES media_items (id) ON DELETE SET NULL
);

CREATE TABLE audit_logs (
	id UUID NOT NULL, 
	actor_id UUID, 
	actor_username VARCHAR(50) NOT NULL, 
	action VARCHAR(50) NOT NULL, 
	target_type VARCHAR(50) NOT NULL, 
	target_id UUID, 
	changes JSON, 
	ip_address VARCHAR(45), 
	user_agent TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE categories (
	parent_id UUID, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	description TEXT, 
	thumbnail_id UUID, 
	sort_order INTEGER NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	is_visible BOOLEAN NOT NULL, 
	is_weekly_schedule BOOLEAN NOT NULL, 
	is_locked BOOLEAN NOT NULL, 
	created_by UUID, 
	updated_by UUID, 
	deleted_by UUID, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	seo_title VARCHAR(255), 
	seo_description TEXT, 
	seo_keywords VARCHAR(255), 
	seo_canonical VARCHAR(255), 
	seo_robots VARCHAR(50), 
	seo_og_image_id UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE SET NULL, 
	FOREIGN KEY(thumbnail_id) REFERENCES media_items (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(updated_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(deleted_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(seo_og_image_id) REFERENCES media_items (id) ON DELETE SET NULL
);

CREATE TABLE login_histories (
	user_id UUID NOT NULL, 
	ip_address VARCHAR(45) NOT NULL, 
	user_agent TEXT, 
	status VARCHAR(20) NOT NULL, 
	failure_reason VARCHAR(255), 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE refresh_tokens (
	user_id UUID NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	ip_address VARCHAR(45) NOT NULL, 
	user_agent TEXT, 
	is_revoked BOOLEAN NOT NULL, 
	parent_token_id UUID, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	UNIQUE (token_hash), 
	FOREIGN KEY(parent_token_id) REFERENCES refresh_tokens (id) ON DELETE SET NULL
);

CREATE TABLE articles (
	category_id UUID, 
	author_id UUID, 
	title VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	excerpt TEXT, 
	content TEXT NOT NULL, 
	thumbnail_object_key VARCHAR(512), 
	cover_object_key VARCHAR(512), 
	status article_status NOT NULL, 
	is_draft BOOLEAN NOT NULL, 
	is_featured BOOLEAN NOT NULL, 
	is_pinned BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	seo_title VARCHAR(255), 
	seo_description TEXT, 
	canonical_url VARCHAR(255), 
	robots VARCHAR(50), 
	og_title VARCHAR(255), 
	og_description TEXT, 
	og_image VARCHAR(512), 
	view_count INTEGER NOT NULL, 
	word_count INTEGER NOT NULL, 
	reading_time INTEGER NOT NULL, 
	publish_at TIMESTAMP WITH TIME ZONE, 
	published_at TIMESTAMP WITH TIME ZONE, 
	expire_at TIMESTAMP WITH TIME ZONE, 
	last_edited_at TIMESTAMP WITH TIME ZONE, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
	FOREIGN KEY(author_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE article_tags (
	article_id UUID NOT NULL, 
	tag_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (article_id, tag_id), 
	FOREIGN KEY(article_id) REFERENCES articles (id) ON DELETE CASCADE, 
	FOREIGN KEY(tag_id) REFERENCES tags (id) ON DELETE CASCADE
);