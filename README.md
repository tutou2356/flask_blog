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

### 2. 启动应用

```bash
python run.py
```

### 3. 访问博客

打开浏览器访问: http://127.0.0.1:5000

## 📁 项目结构

```
blog/
├── app_blog.py          # 主应用文件
├── run.py              # 启动脚本
├── migrate_db.py       # 数据库迁移脚本
├── requirements.txt    # 依赖文件
├── blog.db            # SQLite 数据库
├── templates/         # HTML 模板
│   ├── base.html      # 基础模板
│   ├── index.html     # 首页
│   ├── post.html      # 文章详情
│   ├── create.html    # 创建文章
│   ├── edit.html      # 编辑文章
│   └── search.html    # 搜索结果
└── static/           # 静态文件
    └── blog11.jpeg   # 头像图片
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