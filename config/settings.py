"""
系统配置模块
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from datetime import time


class Settings(BaseSettings):
    """系统配置"""

    # API Keys
    anthropic_api_key: str = ""

    # WeChat 推送配置
    wcf_host: str = "127.0.0.1"
    wcf_port: int = 8080
    serverchan_sendkey: str = ""
    gewe_bot_url: str = ""
    gewe_bot_token: str = ""

    # 邮件告警配置
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email: str = ""

    # 系统设置
    log_level: str = "INFO"
    database_path: str = "./data/stock_news.db"
    redis_url: str = "redis://localhost:6379/0"

    # 定时任务配置
    cron_hour: int = 6  # 6 点开始执行，确保 8:30 前完成
    cron_minute: int = 0

    # 重试配置
    max_retries: int = 3
    retry_delay: int = 60  # 秒

    # 股票列表 (默认配置)
    default_stocks: List[dict] = [
        {"name": "首程控股", "code": "00666.HK", "market": "HK"},
        {"name": "宝龙商业", "code": "09909.HK", "market": "HK"},
        {"name": "宝龙地产", "code": "01238.HK", "market": "HK"},
        {"name": "壁仞科技", "code": "", "market": "PRIVATE"},
        {"name": "九方智投控股", "code": "09977.HK", "market": "HK"},
    ]

    # 推送时间 (24 小时制)
    push_hour: int = 8
    push_minute: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
