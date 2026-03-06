# 架构与访问控制

## 组件概览

- `app/__init__.py`：应用工厂、扩展初始化、错误处理、访问记录
- `app/blog/`：博客内容、评论等读写路由
- `app/admin/`：后台访问记录
- `app/auth/`：注册、登录、登出
- `templates/`：页面模板与错误页

## 权限模型与访问控制点

- **角色模型**：`User.role` 使用 `admin`/`visitor` 区分
- **统一装饰器**：`app/admin/__init__.py` 中 `@admin_required`
- **访问策略**：
  - 未登录访问 admin-only 路由 → 重定向到 `/login`
  - 已登录但非 admin → 403 页面
- **admin-only 路由**：
  - `GET/POST /create`
  - `GET/POST /<id>/edit`
  - `POST /<id>/delete`
  - `POST /comment/<id>/delete`
  - `GET /admin/visits`
- **模板入口**：导航栏与文章管理按钮仅对管理员显示

## 错误处理

- 400/403/404/500 均渲染统一样式页面（`templates/400.html`、`403.html`、`404.html`、`500.html`）
- CSRF 失败返回 400 并提示刷新重试
