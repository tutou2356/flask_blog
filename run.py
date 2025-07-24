#!/usr/bin/env python3
"""
博客应用启动脚本
"""
import os
from app_blog import app, db

def init_database():
    """初始化数据库"""
    if not os.path.exists('blog.db'):
        with app.app_context():
            db.create_all()
            print("✅ 数据库初始化完成")
    else:
        print("✅ 数据库已存在")

if __name__ == '__main__':
    print("🚀 启动博客应用...")
    init_database()
    print("🌐 访问地址: http://127.0.0.1:5000")
    print("📝 管理后台: 直接在网页上创建和编辑文章")
    print("🎨 功能特性: Markdown支持、分类标签、搜索、深色模式")
    print("-" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)