-- System Schema (Settings, Audit Logs)

-- 1. Settings Table (flexible system configurations using JSONB)
CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER set_timestamp_settings
BEFORE UPDATE ON settings
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

CREATE INDEX idx_settings_group ON settings(group_name);

-- 2. Audit Logs Table (immutable logs tracking data modifications)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Nullable to allow system-triggered actions or anonymous actions
    action VARCHAR(50) NOT NULL, -- e.g., 'CREATE_ARTICLE', 'UPDATE_USER'
    module_name VARCHAR(50) NOT NULL, -- e.g., 'articles', 'users'
    entity_name VARCHAR(50) NOT NULL, -- e.g., 'articles', 'users'
    entity_id VARCHAR(50),
    old_data JSONB, -- Previous state
    new_data JSONB, -- Modified state
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_module ON audit_logs(module_name);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
