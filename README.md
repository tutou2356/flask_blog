# 🌟 个人博客系统

一个基于 Flask 的现代化个人博客系统，支持 Markdown 写作、分类标签管理、全文搜索和深色模式。

## ✨ 功能特性

- 📝 **Markdown 支持** - 完整的 Markdown 语法支持，包括代码高亮
- 🏷️ **分类标签** - 灵活的文章分类和标签系统
- 🔍 **全文搜索** - 支持标题、内容、标签的全文搜索
- 🌙 **深色模式** - 优雅的深色主题切换
- 📱 **响应式设计** - 完美适配桌面和移动设备
- ⚡ **轻量快速** - 基于 SQLite，部署简单

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用（唯一开发入口）

```bash
python run.py
```

### 3. 访问博客

打开浏览器访问: http://127.0.0.1:5000

### 4. 创建管理员账号（首次）

```bash
python create_admin.py --username admin --email admin@example.com --password "ChangeMe123"
```

验证方式：
- 使用 `/login` 登录管理员账号
- 打开 `/create` 或 `/admin/visits` 确认拥有管理权限

## 📁 项目结构

```
blog/
├── app/                # 应用包（factory + 蓝图 + 扩展 + 模型）
├── migrations/         # Alembic 迁移目录
├── alembic.ini         # Alembic 配置
├── legacy/             # 旧迁移脚本存档（已弃用）
├── wsgi.py             # 生产入口
├── run.py              # 启动脚本
├── requirements.txt    # 依赖文件
├── blog.db             # SQLite 数据库
├── templates/          # HTML 模板
└── static/             # 静态文件
```

## 🧩 数据库迁移（Flask-Migrate）

迁移目录已内置，无需重复 `flask db init`。

### 旧库接入（不丢数据）
1. **备份数据库**：复制 `blog.db` 到安全位置。
2. 设置环境变量：
   - PowerShell:
     ```powershell
     $env:FLASK_APP = "wsgi.py"
     ```
   - Bash:
     ```bash
     export FLASK_APP=wsgi.py
     ```
3. 标记当前库为基线（不执行建表）：
   ```bash
   flask db stamp head
   ```
4. 验证迁移状态：
   ```bash
   flask db current
   ```

之后的结构变更使用：
```bash
flask db migrate -m "your message"
flask db upgrade
```

### 新库初始化
```bash
flask db upgrade
```


## 🎯 使用说明

### 创建文章
1. 点击导航栏的"撰写新文章"按钮
2. 填写标题、选择分类、添加标签
3. 使用 Markdown 语法编写内容
4. 点击"发布文章"

### 管理文章
- **编辑**: 在文章详情页或首页点击"编辑"按钮
- **删除**: 点击"删除"按钮并确认
- **搜索**: 使用顶部搜索框或点击分类/标签

### 深色模式
点击导航栏右侧的月亮/太阳图标切换主题

## 🔐 权限模型与访问控制点

- **角色**：`admin` 与普通访客
- **访问策略**：
  - 未登录访问 admin-only 路由 → 重定向到 `/login`
  - 已登录但非 admin → 返回 403
- **控制点**：
  - 路由统一通过 `@admin_required` 控制：`/create`、`/<id>/edit`、`/<id>/delete`、`/comment/<id>/delete`、`/admin/visits`
  - 模板入口仅对管理员显示（导航栏写文章、访问记录，文章编辑/删除）

## 🛠️ 技术栈

- **后端**: Flask + SQLAlchemy
- **前端**: HTML5 + TailwindCSS + JavaScript
- **数据库**: SQLite
- **Markdown**: Python-Markdown + Pygments

## 📝 更新日志

### v1.0.0
- ✅ 基础博客功能
- ✅ Markdown 支持
- ✅ 分类标签系统
- ✅ 全文搜索
- ✅ 深色模式
- ✅ 响应式设计

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
