-- Seed Script (Admin CMS RBAC Configurations)
-- Automatically generated. Clean, repeatable, ON CONFLICT-safe PostgreSQL script.

-- 1. Insert Roles
INSERT INTO roles (id, name, code, description) VALUES
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'Super Admin', 'super_admin', 'Has full access to all modules and configurations')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, description = EXCLUDED.description;
INSERT INTO roles (id, name, code, description) VALUES
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'Admin', 'admin', 'Administrative manager with near full access')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, description = EXCLUDED.description;
INSERT INTO roles (id, name, code, description) VALUES
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'Editor', 'editor', 'Editor who can create and update content across the platform')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, description = EXCLUDED.description;
INSERT INTO roles (id, name, code, description) VALUES
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', 'Author', 'author', 'Content author who can manage own articles and media')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, description = EXCLUDED.description;

-- 2. Insert Features
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af01', 'Dashboard', 'dashboard', '/dashboard', 1, TRUE, 'dashboard-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', 'Articles', 'articles', '/articles', 2, TRUE, 'article-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af03', 'Categories', 'categories', '/categories', 3, TRUE, 'category-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af04', 'Tags', 'tags', '/tags', 4, TRUE, 'tag-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af05', 'Media Library', 'media', '/media', 5, TRUE, 'media-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af06', 'Pages', 'pages', '/pages', 6, TRUE, 'page-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af07', 'Menus', 'menus', '/menus', 7, TRUE, 'menu-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af08', 'Banners', 'banners', '/banners', 8, TRUE, 'banner-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', 'Users', 'users', '/users', 9, TRUE, 'user-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af10', 'Roles', 'roles', '/roles', 10, TRUE, 'role-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af11', 'Permissions', 'permissions', '/permissions', 11, TRUE, 'permission-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af12', 'Features', 'features', '/features', 12, TRUE, 'feature-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af13', 'Settings', 'settings', '/settings', 13, TRUE, 'settings-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af14', 'Profile', 'profile', '/profile', 14, TRUE, 'profile-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af15', 'Login History', 'login_history', '/login-history', 15, TRUE, 'history-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af16', 'Audit Logs', 'audit_logs', '/audit-logs', 16, TRUE, 'audit-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;
INSERT INTO features (id, name, code, route, sort_order, is_visible, icon, parent_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af17', 'AI Settings', 'ai_settings', '/settings/ai', 17, TRUE, 'sparkles-icon', NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, route = EXCLUDED.route, sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, icon = EXCLUDED.icon, parent_id = EXCLUDED.parent_id;

-- 3. Insert Permissions
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('ae497478-f188-513c-939f-661a36bf5a76', 'View Dashboard', 'dashboard.view', 'dashboard', 'view', 'Allow viewing administration dashboard')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('92ec922a-df7b-5c8f-92ac-8ae3749126c6', 'View All Articles', 'article.view', 'article', 'view', 'Allow viewing all articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e79a4192-f56a-537a-9398-a4b00fb2bd9b', 'View Own Articles', 'article.view_own', 'article', 'view_own', 'Allow viewing only own articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('8bf00c5b-e2f3-535f-8e1f-43e7f04009d5', 'Create Articles', 'article.create', 'article', 'create', 'Allow creating new articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('83055417-e999-514a-84e5-7c603b7f9500', 'Update All Articles', 'article.update', 'article', 'update', 'Allow modifying any article')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('f237e8b7-1e62-5bd4-9668-932646c70027', 'Update Own Articles', 'article.update_own', 'article', 'update_own', 'Allow modifying only own articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('4bb2b7d8-b228-50e3-bab2-13fa89d67d71', 'Delete All Articles', 'article.delete', 'article', 'delete', 'Allow soft deleting any article')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e22626cb-9644-5280-8d0b-3128e224269c', 'Delete Own Articles', 'article.delete_own', 'article', 'delete_own', 'Allow soft deleting only own articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('6fbe15f0-769f-5dd4-9a2e-1ff1443acdb8', 'Publish Articles', 'article.publish', 'article', 'publish', 'Allow publishing articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('2ab5a9c8-2da9-552a-be96-61b0768b831b', 'Unpublish Articles', 'article.unpublish', 'article', 'unpublish', 'Allow unpublishing articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e95ff30e-c305-5e26-9988-0f6a9a3d65ed', 'Restore Articles', 'article.restore', 'article', 'restore', 'Allow restoring soft-deleted articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('4fd59c68-c4fc-58ca-82c4-90ec28f5753d', 'Force Delete Articles', 'article.force_delete', 'article', 'force_delete', 'Allow permanently deleting articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('5ac24c18-9c09-5077-9232-32d5dbc8ad8b', 'Schedule Articles', 'article.schedule', 'article', 'schedule', 'Allow scheduling article publication')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('1f1bdac8-df13-5f30-859e-908c6cb20774', 'Preview Articles', 'article.preview', 'article', 'preview', 'Allow previewing draft articles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('c83cb20b-6d15-5fa3-8607-7407236a1044', 'View Categories', 'category.view', 'category', 'view', 'Allow viewing categories')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('4bf25cc9-9072-5cf5-ba6e-0aea2293dddf', 'Create Categories', 'category.create', 'category', 'create', 'Allow creating categories')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('cd7552e7-cd83-53c7-ba2b-14e08115f421', 'Update Categories', 'category.update', 'category', 'update', 'Allow modifying categories')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('a947880b-76eb-5a8c-9ec7-063d1d049d92', 'Delete Categories', 'category.delete', 'category', 'delete', 'Allow deleting categories')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('42d417cd-9270-5290-b0e2-d5e954e3aa30', 'Restore Categories', 'category.restore', 'category', 'restore', 'Allow restoring deleted categories')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('0be5e6ad-c090-50d2-915a-c58661845abe', 'Force Delete Categories', 'category.force_delete', 'category', 'force_delete', 'Allow permanently deleting categories')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('0c531a7e-d806-5e55-9642-2ccac687c4d4', 'View Tags', 'tag.view', 'tag', 'view', 'Allow viewing tags')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('84d0348e-5baf-5668-b713-b6a83cb08c4c', 'Create Tags', 'tag.create', 'tag', 'create', 'Allow creating tags')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e610aad9-e786-5da2-b462-c593e0d18004', 'Update Tags', 'tag.update', 'tag', 'update', 'Allow modifying tags')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e41f829f-1c5f-51c7-af6d-dc296c0ecb5d', 'Delete Tags', 'tag.delete', 'tag', 'delete', 'Allow deleting tags')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('0ffd135a-93e4-5797-88ed-fed441274d53', 'Restore Tags', 'tag.restore', 'tag', 'restore', 'Allow restoring deleted tags')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('bba63633-3e24-5d9b-b8ee-6df23b4c7d61', 'View All Media', 'media.view', 'media', 'view', 'Allow viewing all media files')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('83eac11a-c780-5fc5-8ff0-5f6ea52b48af', 'View Own Media', 'media.view_own', 'media', 'view_own', 'Allow viewing own uploaded media files')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('8ed8964d-0b51-5ca4-9ad8-92c44346e4a8', 'Create Media', 'media.create', 'media', 'create', 'Allow creating and uploading new media files')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('17e30174-1c2d-5000-9e35-90c53e50a414', 'Update Media', 'media.update', 'media', 'update', 'Allow modifying media details')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('1692ed3d-fef3-585d-8069-5afd0f13ac59', 'Delete Media', 'media.delete', 'media', 'delete', 'Allow deleting media files')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('782ea306-2791-549f-b44f-4bf58f5251c4', 'Download Media', 'media.download', 'media', 'download', 'Allow downloading media files')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('f80f7d03-7af8-5e7d-9302-0789b4d23c6c', 'Copy Media URL', 'media.copy_url', 'media', 'copy_url', 'Allow copying media file public URLs')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('81256ae5-c5be-5a14-a4d3-422472d1e0a6', 'View Pages', 'page.view', 'page', 'view', 'Allow viewing pages')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('73dea63f-1e30-5f32-8e49-ff0894b5d8da', 'Create Pages', 'page.create', 'page', 'create', 'Allow creating pages')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('75bf8fd3-b877-558e-b00b-33c58814f6f2', 'Update Pages', 'page.update', 'page', 'update', 'Allow modifying pages')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('6c5b2580-ac9c-50e4-bcc5-cb5130d5c16b', 'Delete Pages', 'page.delete', 'page', 'delete', 'Allow deleting pages')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('769c964c-4fcd-5948-b5c0-04feba052149', 'Publish Pages', 'page.publish', 'page', 'publish', 'Allow publishing pages')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('d5842aea-8037-5ea8-a5e4-a1df4a2aeafb', 'Unpublish Pages', 'page.unpublish', 'page', 'unpublish', 'Allow unpublishing pages')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('eb97d0e6-7ccf-5573-bc6e-00c98275bab6', 'Preview Pages', 'page.preview', 'page', 'preview', 'Allow previewing draft pages')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('73695f7a-99e0-5925-86a8-d9fb74e2e070', 'View Menus', 'menu.view', 'menu', 'view', 'Allow viewing navigation menus')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e30ba963-4b3c-510a-a86a-c927b4c6ffc2', 'Create Menus', 'menu.create', 'menu', 'create', 'Allow creating navigation menus')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('5b23dba8-6d2e-56d2-a4f2-c7fe4a5c4c13', 'Update Menus', 'menu.update', 'menu', 'update', 'Allow modifying navigation menus')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('6f533e84-0a54-567d-a375-41f5502d4174', 'Delete Menus', 'menu.delete', 'menu', 'delete', 'Allow deleting navigation menus')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('3ea47b5c-6081-5fb0-8fce-80be59e14bf9', 'Sort Menus', 'menu.sort', 'menu', 'sort', 'Allow sorting menu items')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('eca382c1-d2b5-5b28-b82d-f8c8385cb5d2', 'View Banners', 'banner.view', 'banner', 'view', 'Allow viewing banners')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('ff5bf390-4044-55eb-bae2-a95115b9708f', 'Create Banners', 'banner.create', 'banner', 'create', 'Allow creating banners')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('ff91ace9-97e2-5538-acaf-5aae92279baa', 'Update Banners', 'banner.update', 'banner', 'update', 'Allow modifying banners')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('7eade393-957d-5efd-89c7-7a4ed37a2df1', 'Delete Banners', 'banner.delete', 'banner', 'delete', 'Allow deleting banners')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('c7d0d981-faac-5e11-b963-be008688e075', 'Enable Banners', 'banner.enable', 'banner', 'enable', 'Allow enabling banners')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('81783ef9-0cfe-5b8a-a6d4-417fb8b4230c', 'Disable Banners', 'banner.disable', 'banner', 'disable', 'Allow disabling banners')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('f944ed33-ae89-5774-9849-c04be4af9d09', 'View Users', 'user.view', 'user', 'view', 'Allow viewing users')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e9483d0a-d5b4-58b6-9505-ef5e55907188', 'Create Users', 'user.create', 'user', 'create', 'Allow creating users')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('3e62c0aa-a070-579b-9b15-ec132d50d5ed', 'Update Users', 'user.update', 'user', 'update', 'Allow modifying users')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('7a497a3e-9dd0-5874-aecd-36e3b329e74d', 'Delete Users', 'user.delete', 'user', 'delete', 'Allow deleting users')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('3211c3fc-156b-5804-8d5e-870e2dc81a46', 'Lock Users', 'user.lock', 'user', 'lock', 'Allow locking users')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('4e4dff33-4102-53c9-803f-8abaaf6012ae', 'Unlock Users', 'user.unlock', 'user', 'unlock', 'Allow unlocking users')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('6eadeabc-ab0c-5a19-93b4-b233ecb288b5', 'Reset User Password', 'user.reset_password', 'user', 'reset_password', 'Allow resetting passwords')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('4724f46a-1c13-5a45-94d9-73c6c404fc4e', 'Assign User Role', 'user.assign_role', 'user', 'assign_role', 'Allow assigning roles to users')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e371cc79-22bb-5ab0-9368-55fdccb5662a', 'View Roles', 'role.view', 'role', 'view', 'Allow viewing roles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('d29d24fa-e8f3-51c1-9503-23ecd000cccc', 'Create Roles', 'role.create', 'role', 'create', 'Allow creating roles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('71ba5dec-8fd0-5e99-b9cb-5d53de32390c', 'Update Roles', 'role.update', 'role', 'update', 'Allow modifying roles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('142364dd-4482-5391-af3a-d6c31acb02a6', 'Delete Roles', 'role.delete', 'role', 'delete', 'Allow deleting roles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('12a4cb4b-5951-5cf4-b92a-f04e4e4fb512', 'Assign Role Permissions', 'role.assign_permission', 'role', 'assign_permission', 'Allow assigning permissions to roles')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('33e48133-7b3e-53e3-aad1-89d2105132e5', 'View Permissions', 'permission.view', 'permission', 'view', 'Allow viewing permissions')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('a211d821-9905-55a6-a3eb-cd7103479d8b', 'Create Permissions', 'permission.create', 'permission', 'create', 'Allow creating permissions')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('c7b14997-b3ac-5f48-84a8-601d547f6038', 'Update Permissions', 'permission.update', 'permission', 'update', 'Allow modifying permissions')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('d3143542-8b99-52e3-8833-82a31e6d7736', 'Delete Permissions', 'permission.delete', 'permission', 'delete', 'Allow deleting permissions')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('fa26faf4-7ea1-5001-a278-1ab75f0a3753', 'View Features', 'feature.view', 'feature', 'view', 'Allow viewing features')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('45187f3d-16b8-52e6-9b08-d9e99d9012e9', 'Create Features', 'feature.create', 'feature', 'create', 'Allow creating features')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('dc526657-4f71-5d4a-97d4-f4e47c877ed7', 'Update Features', 'feature.update', 'feature', 'update', 'Allow modifying features')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('64142a92-6d5a-517b-a9b5-fdbd4e0bd773', 'Delete Features', 'feature.delete', 'feature', 'delete', 'Allow deleting features')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('a5266196-60d0-537e-b5bd-7354841079de', 'View Settings', 'setting.view', 'setting', 'view', 'Allow viewing system settings')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('c0369d82-32f7-5a89-b6ec-9c8fba144872', 'Update Settings', 'setting.update', 'setting', 'update', 'Allow modifying system settings')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('3bbe47c0-3a89-5e67-a8b3-6696342cb6c1', 'View Profile', 'profile.view', 'profile', 'view', 'Allow viewing profile information')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('58b0957b-852f-570b-97df-a3cec6187fbe', 'Update Profile', 'profile.update', 'profile', 'update', 'Allow updating profile information')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('54a314e8-544a-5193-8424-84bb18f21f90', 'Change Profile Password', 'profile.change_password', 'profile', 'change_password', 'Allow changing profile password')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('47da359c-7276-5d47-8359-72412246109f', 'Change Profile Avatar', 'profile.change_avatar', 'profile', 'change_avatar', 'Allow changing profile avatar')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('e9391c56-02e3-501c-b9a8-d9d960d8886e', 'View Login History', 'login_history.view', 'login_history', 'view', 'Allow viewing login history logs')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('8701264c-64eb-5241-9919-28833204738d', 'View Audit Logs', 'audit.view', 'audit', 'view', 'Allow viewing system audit logs')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('cbb21f4b-3b8d-5777-9d23-317596d0944e', 'Export Audit Logs', 'audit.export', 'audit', 'export', 'Allow exporting audit logs')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c01', 'View AI Settings', 'ai.view', 'ai', 'view', 'Allow viewing AI configuration, pricing, usage logs, and spending')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c02', 'Update AI Settings', 'ai.update', 'ai', 'update', 'Allow modifying AI configuration, budget, and model pricing')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c03', 'Test AI Connection', 'ai.test_connection', 'ai', 'test_connection', 'Allow testing AI provider connection and model discovery')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;
INSERT INTO permissions (id, name, code, module, action, description) VALUES
('b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c04', 'Generate AI SEO', 'ai.generate_seo', 'ai', 'generate_seo', 'Allow generating SEO content using AI assistant')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, module = EXCLUDED.module, action = EXCLUDED.action, description = EXCLUDED.description;

-- 4. Clean and Re-insert Mapping Tables to ensure no stale/duplicate links
DELETE FROM feature_permissions;
DELETE FROM role_permissions;

-- 5. Map Features to Permissions
INSERT INTO feature_permissions (feature_id, permission_id) VALUES
('f1017cf7-88b3-4f9e-c616-3e4b3c75af01', 'ae497478-f188-513c-939f-661a36bf5a76'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '92ec922a-df7b-5c8f-92ac-8ae3749126c6'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', 'e79a4192-f56a-537a-9398-a4b00fb2bd9b'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '8bf00c5b-e2f3-535f-8e1f-43e7f04009d5'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '83055417-e999-514a-84e5-7c603b7f9500'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', 'f237e8b7-1e62-5bd4-9668-932646c70027'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '4bb2b7d8-b228-50e3-bab2-13fa89d67d71'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', 'e22626cb-9644-5280-8d0b-3128e224269c'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '6fbe15f0-769f-5dd4-9a2e-1ff1443acdb8'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '2ab5a9c8-2da9-552a-be96-61b0768b831b'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', 'e95ff30e-c305-5e26-9988-0f6a9a3d65ed'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '4fd59c68-c4fc-58ca-82c4-90ec28f5753d'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '5ac24c18-9c09-5077-9232-32d5dbc8ad8b'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af02', '1f1bdac8-df13-5f30-859e-908c6cb20774'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af03', 'c83cb20b-6d15-5fa3-8607-7407236a1044'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af03', '4bf25cc9-9072-5cf5-ba6e-0aea2293dddf'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af03', 'cd7552e7-cd83-53c7-ba2b-14e08115f421'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af03', 'a947880b-76eb-5a8c-9ec7-063d1d049d92'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af03', '42d417cd-9270-5290-b0e2-d5e954e3aa30'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af03', '0be5e6ad-c090-50d2-915a-c58661845abe'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af04', '0c531a7e-d806-5e55-9642-2ccac687c4d4'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af04', '84d0348e-5baf-5668-b713-b6a83cb08c4c'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af04', 'e610aad9-e786-5da2-b462-c593e0d18004'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af04', 'e41f829f-1c5f-51c7-af6d-dc296c0ecb5d'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af04', '0ffd135a-93e4-5797-88ed-fed441274d53'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af05', 'bba63633-3e24-5d9b-b8ee-6df23b4c7d61'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af05', '83eac11a-c780-5fc5-8ff0-5f6ea52b48af'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af05', '8ed8964d-0b51-5ca4-9ad8-92c44346e4a8'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af05', '17e30174-1c2d-5000-9e35-90c53e50a414'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af05', '1692ed3d-fef3-585d-8069-5afd0f13ac59'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af05', '782ea306-2791-549f-b44f-4bf58f5251c4'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af05', 'f80f7d03-7af8-5e7d-9302-0789b4d23c6c'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af06', '81256ae5-c5be-5a14-a4d3-422472d1e0a6'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af06', '73dea63f-1e30-5f32-8e49-ff0894b5d8da'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af06', '75bf8fd3-b877-558e-b00b-33c58814f6f2'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af06', '6c5b2580-ac9c-50e4-bcc5-cb5130d5c16b'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af06', '769c964c-4fcd-5948-b5c0-04feba052149'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af06', 'd5842aea-8037-5ea8-a5e4-a1df4a2aeafb'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af06', 'eb97d0e6-7ccf-5573-bc6e-00c98275bab6'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af07', '73695f7a-99e0-5925-86a8-d9fb74e2e070'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af07', 'e30ba963-4b3c-510a-a86a-c927b4c6ffc2'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af07', '5b23dba8-6d2e-56d2-a4f2-c7fe4a5c4c13'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af07', '6f533e84-0a54-567d-a375-41f5502d4174'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af07', '3ea47b5c-6081-5fb0-8fce-80be59e14bf9'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af08', 'eca382c1-d2b5-5b28-b82d-f8c8385cb5d2'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af08', 'ff5bf390-4044-55eb-bae2-a95115b9708f'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af08', 'ff91ace9-97e2-5538-acaf-5aae92279baa'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af08', '7eade393-957d-5efd-89c7-7a4ed37a2df1'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af08', 'c7d0d981-faac-5e11-b963-be008688e075'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af08', '81783ef9-0cfe-5b8a-a6d4-417fb8b4230c'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', 'f944ed33-ae89-5774-9849-c04be4af9d09'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', 'e9483d0a-d5b4-58b6-9505-ef5e55907188'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', '3e62c0aa-a070-579b-9b15-ec132d50d5ed'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', '7a497a3e-9dd0-5874-aecd-36e3b329e74d'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', '3211c3fc-156b-5804-8d5e-870e2dc81a46'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', '4e4dff33-4102-53c9-803f-8abaaf6012ae'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', '6eadeabc-ab0c-5a19-93b4-b233ecb288b5'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af09', '4724f46a-1c13-5a45-94d9-73c6c404fc4e'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af10', 'e371cc79-22bb-5ab0-9368-55fdccb5662a'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af10', 'd29d24fa-e8f3-51c1-9503-23ecd000cccc'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af10', '71ba5dec-8fd0-5e99-b9cb-5d53de32390c'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af10', '142364dd-4482-5391-af3a-d6c31acb02a6'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af10', '12a4cb4b-5951-5cf4-b92a-f04e4e4fb512'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af11', '33e48133-7b3e-53e3-aad1-89d2105132e5'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af11', 'a211d821-9905-55a6-a3eb-cd7103479d8b'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af11', 'c7b14997-b3ac-5f48-84a8-601d547f6038'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af11', 'd3143542-8b99-52e3-8833-82a31e6d7736'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af12', 'fa26faf4-7ea1-5001-a278-1ab75f0a3753'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af12', '45187f3d-16b8-52e6-9b08-d9e99d9012e9'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af12', 'dc526657-4f71-5d4a-97d4-f4e47c877ed7'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af12', '64142a92-6d5a-517b-a9b5-fdbd4e0bd773'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af13', 'a5266196-60d0-537e-b5bd-7354841079de'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af13', 'c0369d82-32f7-5a89-b6ec-9c8fba144872'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af14', '3bbe47c0-3a89-5e67-a8b3-6696342cb6c1'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af14', '58b0957b-852f-570b-97df-a3cec6187fbe'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af14', '54a314e8-544a-5193-8424-84bb18f21f90'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af14', '47da359c-7276-5d47-8359-72412246109f'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af15', 'e9391c56-02e3-501c-b9a8-d9d960d8886e'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af16', '8701264c-64eb-5241-9919-28833204738d'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af16', 'cbb21f4b-3b8d-5777-9d23-317596d0944e'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af17', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c01'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af17', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c02'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af17', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c03'),
('f1017cf7-88b3-4f9e-c616-3e4b3c75af17', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c04');

-- 6. Assign Permissions to Roles
-- 6.1 Super Admin Mappings
INSERT INTO role_permissions (role_id, permission_id) VALUES
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'ae497478-f188-513c-939f-661a36bf5a76'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '92ec922a-df7b-5c8f-92ac-8ae3749126c6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e79a4192-f56a-537a-9398-a4b00fb2bd9b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '8bf00c5b-e2f3-535f-8e1f-43e7f04009d5'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '83055417-e999-514a-84e5-7c603b7f9500'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'f237e8b7-1e62-5bd4-9668-932646c70027'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '4bb2b7d8-b228-50e3-bab2-13fa89d67d71'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e22626cb-9644-5280-8d0b-3128e224269c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '6fbe15f0-769f-5dd4-9a2e-1ff1443acdb8'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '2ab5a9c8-2da9-552a-be96-61b0768b831b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e95ff30e-c305-5e26-9988-0f6a9a3d65ed'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '4fd59c68-c4fc-58ca-82c4-90ec28f5753d'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '5ac24c18-9c09-5077-9232-32d5dbc8ad8b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '1f1bdac8-df13-5f30-859e-908c6cb20774'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'c83cb20b-6d15-5fa3-8607-7407236a1044'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '4bf25cc9-9072-5cf5-ba6e-0aea2293dddf'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'cd7552e7-cd83-53c7-ba2b-14e08115f421'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'a947880b-76eb-5a8c-9ec7-063d1d049d92'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '42d417cd-9270-5290-b0e2-d5e954e3aa30'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '0be5e6ad-c090-50d2-915a-c58661845abe'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '0c531a7e-d806-5e55-9642-2ccac687c4d4'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '84d0348e-5baf-5668-b713-b6a83cb08c4c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e610aad9-e786-5da2-b462-c593e0d18004'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e41f829f-1c5f-51c7-af6d-dc296c0ecb5d'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '0ffd135a-93e4-5797-88ed-fed441274d53'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'bba63633-3e24-5d9b-b8ee-6df23b4c7d61'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '83eac11a-c780-5fc5-8ff0-5f6ea52b48af'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '8ed8964d-0b51-5ca4-9ad8-92c44346e4a8'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '17e30174-1c2d-5000-9e35-90c53e50a414'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '1692ed3d-fef3-585d-8069-5afd0f13ac59'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '782ea306-2791-549f-b44f-4bf58f5251c4'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'f80f7d03-7af8-5e7d-9302-0789b4d23c6c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '81256ae5-c5be-5a14-a4d3-422472d1e0a6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '73dea63f-1e30-5f32-8e49-ff0894b5d8da'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '75bf8fd3-b877-558e-b00b-33c58814f6f2'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '6c5b2580-ac9c-50e4-bcc5-cb5130d5c16b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '769c964c-4fcd-5948-b5c0-04feba052149'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'd5842aea-8037-5ea8-a5e4-a1df4a2aeafb'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'eb97d0e6-7ccf-5573-bc6e-00c98275bab6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '73695f7a-99e0-5925-86a8-d9fb74e2e070'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e30ba963-4b3c-510a-a86a-c927b4c6ffc2'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '5b23dba8-6d2e-56d2-a4f2-c7fe4a5c4c13'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '6f533e84-0a54-567d-a375-41f5502d4174'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '3ea47b5c-6081-5fb0-8fce-80be59e14bf9'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'eca382c1-d2b5-5b28-b82d-f8c8385cb5d2'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'ff5bf390-4044-55eb-bae2-a95115b9708f'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'ff91ace9-97e2-5538-acaf-5aae92279baa'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '7eade393-957d-5efd-89c7-7a4ed37a2df1'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'c7d0d981-faac-5e11-b963-be008688e075'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '81783ef9-0cfe-5b8a-a6d4-417fb8b4230c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'f944ed33-ae89-5774-9849-c04be4af9d09'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e9483d0a-d5b4-58b6-9505-ef5e55907188'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '3e62c0aa-a070-579b-9b15-ec132d50d5ed'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '7a497a3e-9dd0-5874-aecd-36e3b329e74d'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '3211c3fc-156b-5804-8d5e-870e2dc81a46'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '4e4dff33-4102-53c9-803f-8abaaf6012ae'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '6eadeabc-ab0c-5a19-93b4-b233ecb288b5'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '4724f46a-1c13-5a45-94d9-73c6c404fc4e'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e371cc79-22bb-5ab0-9368-55fdccb5662a'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'd29d24fa-e8f3-51c1-9503-23ecd000cccc'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '71ba5dec-8fd0-5e99-b9cb-5d53de32390c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '142364dd-4482-5391-af3a-d6c31acb02a6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '12a4cb4b-5951-5cf4-b92a-f04e4e4fb512'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '33e48133-7b3e-53e3-aad1-89d2105132e5'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'a211d821-9905-55a6-a3eb-cd7103479d8b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'c7b14997-b3ac-5f48-84a8-601d547f6038'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'd3143542-8b99-52e3-8833-82a31e6d7736'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'fa26faf4-7ea1-5001-a278-1ab75f0a3753'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '45187f3d-16b8-52e6-9b08-d9e99d9012e9'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'dc526657-4f71-5d4a-97d4-f4e47c877ed7'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '64142a92-6d5a-517b-a9b5-fdbd4e0bd773'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'a5266196-60d0-537e-b5bd-7354841079de'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'c0369d82-32f7-5a89-b6ec-9c8fba144872'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '3bbe47c0-3a89-5e67-a8b3-6696342cb6c1'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '58b0957b-852f-570b-97df-a3cec6187fbe'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '54a314e8-544a-5193-8424-84bb18f21f90'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '47da359c-7276-5d47-8359-72412246109f'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'e9391c56-02e3-501c-b9a8-d9d960d8886e'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', '8701264c-64eb-5241-9919-28833204738d'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'cbb21f4b-3b8d-5777-9d23-317596d0944e'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c01'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c02'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c03'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad01', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c04');

-- 6.2 Admin Mappings
INSERT INTO role_permissions (role_id, permission_id) VALUES
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'ae497478-f188-513c-939f-661a36bf5a76'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '92ec922a-df7b-5c8f-92ac-8ae3749126c6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e79a4192-f56a-537a-9398-a4b00fb2bd9b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '8bf00c5b-e2f3-535f-8e1f-43e7f04009d5'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '83055417-e999-514a-84e5-7c603b7f9500'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'f237e8b7-1e62-5bd4-9668-932646c70027'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '4bb2b7d8-b228-50e3-bab2-13fa89d67d71'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e22626cb-9644-5280-8d0b-3128e224269c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '6fbe15f0-769f-5dd4-9a2e-1ff1443acdb8'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '2ab5a9c8-2da9-552a-be96-61b0768b831b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e95ff30e-c305-5e26-9988-0f6a9a3d65ed'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '4fd59c68-c4fc-58ca-82c4-90ec28f5753d'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '5ac24c18-9c09-5077-9232-32d5dbc8ad8b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '1f1bdac8-df13-5f30-859e-908c6cb20774'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'c83cb20b-6d15-5fa3-8607-7407236a1044'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '4bf25cc9-9072-5cf5-ba6e-0aea2293dddf'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'cd7552e7-cd83-53c7-ba2b-14e08115f421'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'a947880b-76eb-5a8c-9ec7-063d1d049d92'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '42d417cd-9270-5290-b0e2-d5e954e3aa30'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '0be5e6ad-c090-50d2-915a-c58661845abe'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '0c531a7e-d806-5e55-9642-2ccac687c4d4'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '84d0348e-5baf-5668-b713-b6a83cb08c4c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e610aad9-e786-5da2-b462-c593e0d18004'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e41f829f-1c5f-51c7-af6d-dc296c0ecb5d'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '0ffd135a-93e4-5797-88ed-fed441274d53'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'bba63633-3e24-5d9b-b8ee-6df23b4c7d61'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '83eac11a-c780-5fc5-8ff0-5f6ea52b48af'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '8ed8964d-0b51-5ca4-9ad8-92c44346e4a8'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '17e30174-1c2d-5000-9e35-90c53e50a414'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '1692ed3d-fef3-585d-8069-5afd0f13ac59'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '782ea306-2791-549f-b44f-4bf58f5251c4'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'f80f7d03-7af8-5e7d-9302-0789b4d23c6c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '81256ae5-c5be-5a14-a4d3-422472d1e0a6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '73dea63f-1e30-5f32-8e49-ff0894b5d8da'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '75bf8fd3-b877-558e-b00b-33c58814f6f2'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '6c5b2580-ac9c-50e4-bcc5-cb5130d5c16b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '769c964c-4fcd-5948-b5c0-04feba052149'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'd5842aea-8037-5ea8-a5e4-a1df4a2aeafb'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'eb97d0e6-7ccf-5573-bc6e-00c98275bab6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '73695f7a-99e0-5925-86a8-d9fb74e2e070'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e30ba963-4b3c-510a-a86a-c927b4c6ffc2'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '5b23dba8-6d2e-56d2-a4f2-c7fe4a5c4c13'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '6f533e84-0a54-567d-a375-41f5502d4174'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '3ea47b5c-6081-5fb0-8fce-80be59e14bf9'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'eca382c1-d2b5-5b28-b82d-f8c8385cb5d2'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'ff5bf390-4044-55eb-bae2-a95115b9708f'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'ff91ace9-97e2-5538-acaf-5aae92279baa'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '7eade393-957d-5efd-89c7-7a4ed37a2df1'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'c7d0d981-faac-5e11-b963-be008688e075'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '81783ef9-0cfe-5b8a-a6d4-417fb8b4230c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'f944ed33-ae89-5774-9849-c04be4af9d09'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e9483d0a-d5b4-58b6-9505-ef5e55907188'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '3e62c0aa-a070-579b-9b15-ec132d50d5ed'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '7a497a3e-9dd0-5874-aecd-36e3b329e74d'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '3211c3fc-156b-5804-8d5e-870e2dc81a46'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '4e4dff33-4102-53c9-803f-8abaaf6012ae'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '6eadeabc-ab0c-5a19-93b4-b233ecb288b5'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '4724f46a-1c13-5a45-94d9-73c6c404fc4e'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e371cc79-22bb-5ab0-9368-55fdccb5662a'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'd29d24fa-e8f3-51c1-9503-23ecd000cccc'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '71ba5dec-8fd0-5e99-b9cb-5d53de32390c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '142364dd-4482-5391-af3a-d6c31acb02a6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '12a4cb4b-5951-5cf4-b92a-f04e4e4fb512'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '33e48133-7b3e-53e3-aad1-89d2105132e5'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'a211d821-9905-55a6-a3eb-cd7103479d8b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'c7b14997-b3ac-5f48-84a8-601d547f6038'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'fa26faf4-7ea1-5001-a278-1ab75f0a3753'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '45187f3d-16b8-52e6-9b08-d9e99d9012e9'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'dc526657-4f71-5d4a-97d4-f4e47c877ed7'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'a5266196-60d0-537e-b5bd-7354841079de'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'c0369d82-32f7-5a89-b6ec-9c8fba144872'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '3bbe47c0-3a89-5e67-a8b3-6696342cb6c1'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '58b0957b-852f-570b-97df-a3cec6187fbe'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '54a314e8-544a-5193-8424-84bb18f21f90'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '47da359c-7276-5d47-8359-72412246109f'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'e9391c56-02e3-501c-b9a8-d9d960d8886e'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', '8701264c-64eb-5241-9919-28833204738d'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'cbb21f4b-3b8d-5777-9d23-317596d0944e'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c01'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c02'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c03'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad02', 'b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c04');

-- 6.3 Editor Mappings
INSERT INTO role_permissions (role_id, permission_id) VALUES
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '664c9515-e4bc-5ead-bb63-336043bcd81a'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '5db3466e-ccbb-5f71-ace1-b7cf3f6f39bd'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '84cdb952-f765-57a4-ade9-fae2748603c2'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'f274cc64-5017-5c8d-8a55-714fb620c5aa'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'e51f0b77-fd7d-5959-8275-42fdcd85c2f6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '231565ce-92b7-58bd-b53d-3e3279a34c9e'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '19dec3d3-2b70-58f9-a5dd-37b29419ffd0'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'ae497478-f188-513c-939f-661a36bf5a76'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '92ec922a-df7b-5c8f-92ac-8ae3749126c6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '8bf00c5b-e2f3-535f-8e1f-43e7f04009d5'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '83055417-e999-514a-84e5-7c603b7f9500'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '1f1bdac8-df13-5f30-859e-908c6cb20774'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'c83cb20b-6d15-5fa3-8607-7407236a1044'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '4bf25cc9-9072-5cf5-ba6e-0aea2293dddf'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'cd7552e7-cd83-53c7-ba2b-14e08115f421'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '0c531a7e-d806-5e55-9642-2ccac687c4d4'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '84d0348e-5baf-5668-b713-b6a83cb08c4c'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'e610aad9-e786-5da2-b462-c593e0d18004'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'bba63633-3e24-5d9b-b8ee-6df23b4c7d61'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '8ed8964d-0b51-5ca4-9ad8-92c44346e4a8'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '81256ae5-c5be-5a14-a4d3-422472d1e0a6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '73dea63f-1e30-5f32-8e49-ff0894b5d8da'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '75bf8fd3-b877-558e-b00b-33c58814f6f2'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', 'eb97d0e6-7ccf-5573-bc6e-00c98275bab6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '3bbe47c0-3a89-5e67-a8b3-6696342cb6c1'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '58b0957b-852f-570b-97df-a3cec6187fbe'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '54a314e8-544a-5193-8424-84bb18f21f90'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad03', '47da359c-7276-5d47-8359-72412246109f');

-- 6.4 Author Mappings
INSERT INTO role_permissions (role_id, permission_id) VALUES
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '664c9515-e4bc-5ead-bb63-336043bcd81a'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '5db3466e-ccbb-5f71-ace1-b7cf3f6f39bd'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', 'e51f0b77-fd7d-5959-8275-42fdcd85c2f6'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', 'c83cb20b-6d15-5fa3-8607-7407236a1044'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', 'ae497478-f188-513c-939f-661a36bf5a76'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', 'e79a4192-f56a-537a-9398-a4b00fb2bd9b'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '8bf00c5b-e2f3-535f-8e1f-43e7f04009d5'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', 'f237e8b7-1e62-5bd4-9668-932646c70027'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '1f1bdac8-df13-5f30-859e-908c6cb20774'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '83eac11a-c780-5fc5-8ff0-5f6ea52b48af'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '8ed8964d-0b51-5ca4-9ad8-92c44346e4a8'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '3bbe47c0-3a89-5e67-a8b3-6696342cb6c1'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '58b0957b-852f-570b-97df-a3cec6187fbe'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '54a314e8-544a-5193-8424-84bb18f21f90'),
('d1017cf7-88b3-4f9e-c616-3e4b3c75ad04', '47da359c-7276-5d47-8359-72412246109f');

-- 7. Seed Default Menus
INSERT INTO menus (id, name, code, description, is_active) VALUES
('a0000000-0000-4000-a000-000000000001', 'Header Menu', 'header', 'Menu chính hiển thị trên đầu trang website', TRUE)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, description = EXCLUDED.description, is_active = EXCLUDED.is_active;
INSERT INTO menus (id, name, code, description, is_active) VALUES
('a0000000-0000-4000-a000-000000000002', 'Footer Menu', 'footer', 'Menu hiển thị ở chân trang website', TRUE)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, description = EXCLUDED.description, is_active = EXCLUDED.is_active;
INSERT INTO menus (id, name, code, description, is_active) VALUES
('a0000000-0000-4000-a000-000000000003', 'Sidebar Menu', 'sidebar', 'Menu hiển thị ở thanh bên website', TRUE)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code, description = EXCLUDED.description, is_active = EXCLUDED.is_active;
