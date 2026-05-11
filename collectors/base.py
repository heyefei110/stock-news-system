"""
数据采集器基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class NewsItem:
    """新闻数据模型"""

    def __init__(
        self,
        stock_name: str,
        title: str,
        content: str = "",
        source: str = "",
        url: str = "",
        publish_time: Optional[datetime] = None,
        image_url: Optional[str] = None
    ):
        self.stock_name = stock_name
        self.title = title
        self.content = content
        self.source = source
        self.url = url
        self.publish_time = publish_time or datetime.now()
        self.image_url = image_url

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stock_name": self.stock_name,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "image_url": self.image_url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsItem":
        publish_time = data.get("publish_time")
        if isinstance(publish_time, str):
            publish_time = datetime.fromisoformat(publish_time)

        return cls(
            stock_name=data.get("stock_name", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            url=data.get("url", ""),
            publish_time=publish_time,
            image_url=data.get("image_url")
        )


class BaseCollector(ABC):
    """数据采集器基类"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.get_headers()
        )

    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    @abstractmethod
    async def collect(
        self,
        stock_list: List[Dict[str, str]],
        date_range: timedelta = timedelta(days=1)
    ) -> List[NewsItem]:
        """
        采集新闻数据

        Args:
            stock_list: 股票列表，包含 name 和 code
            date_range: 时间范围，默认 1 天

        Returns:
            NewsItem 列表
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """获取数据源名称"""
        pass

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def safe_request(self, url: str, **kwargs) -> httpx.Response:
        """安全请求，带重试机制"""
        response = await self.client.get(url, **kwargs)
        response.raise_for_status()
        return response

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串，支持多种格式

        Returns:
            datetime 对象
        """
        if not date_str:
            return None

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%m-%d %H:%M",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # 处理相对时间
        now = datetime.now()
        if "刚刚" in date_str or "分钟前" in date_str:
            return now
        elif "小时前" in date_str:
            hours = int(date_str.replace("小时前", ""))
            return now - timedelta(hours=hours)
        elif "昨天" in date_str or "昨日" in date_str:
            return now - timedelta(days=1)
        elif "今天" in date_str or "今日" in date_str:
            return now

        return None
