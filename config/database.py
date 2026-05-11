"""
数据库连接和初始化
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from config.settings import settings


def get_db_path() -> str:
    """获取数据库路径"""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


def init_database():
    """初始化数据库表"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # 股票配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT,
            market TEXT DEFAULT 'HK',
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 新闻数据表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_name TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            source TEXT NOT NULL,
            url TEXT,
            publish_time TIMESTAMP,
            collected_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            simhash TEXT,
            is_pushed INTEGER DEFAULT 0,
            pushed_time TIMESTAMP,
            summary TEXT,
            FOREIGN KEY (stock_name) REFERENCES stocks(name)
        )
    """)

    # 推送记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS push_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            push_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stock_count INTEGER,
            news_count INTEGER,
            status TEXT DEFAULT 'success',
            error_message TEXT,
            retry_count INTEGER DEFAULT 0
        )
    """)

    # 任务执行日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT,
            records_processed INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_stock ON news(stock_name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_time ON news(publish_time)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_simhash ON news(simhash)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_time ON push_records(push_time)
    """)

    # 初始化默认股票
    for stock in settings.default_stocks:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO stocks (name, code, market)
                VALUES (?, ?, ?)
            """, (stock["name"], stock["code"], stock["market"]))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    init_database()
    print("数据库初始化完成")
