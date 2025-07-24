import sqlite3
from datetime import datetime
import os

def migrate_database():
    """安全地迁移数据库，添加新字段"""
    db_path = 'blog.db'
    
    # 备份数据库
    if os.path.exists(db_path):
        backup_path = f'blog_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经有新字段
        cursor.execute("PRAGMA table_info(post)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加 created_at 字段 - 使用NULL默认值，然后更新
        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE post ADD COLUMN created_at DATETIME")
            print("添加 created_at 字段成功")
        
        # 添加 category 字段
        if 'category' not in columns:
            cursor.execute("ALTER TABLE post ADD COLUMN category VARCHAR(50)")
            print("添加 category 字段成功")
        
        # 添加 tags 字段
        if 'tags' not in columns:
            cursor.execute("ALTER TABLE post ADD COLUMN tags TEXT")
            print("添加 tags 字段成功")
        
        # 为现有文章设置默认值
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("UPDATE post SET created_at = ? WHERE created_at IS NULL", (current_time,))
        cursor.execute("UPDATE post SET category = '未分类' WHERE category IS NULL OR category = ''")
        cursor.execute("UPDATE post SET tags = '' WHERE tags IS NULL")
        
        conn.commit()
        print("数据库迁移完成！")
        print(f"现有文章的发布时间已设置为: {current_time}")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()