"""
腾讯新闻数据采集器
"""
from typing import List, Dict
from datetime import datetime, timedelta
from loguru import logger
from collectors.base import BaseCollector, NewsItem


class TencentCollector(BaseCollector):
    """腾讯新闻数据采集器"""

    def get_source_name(self) -> str:
        return "腾讯新闻"

    async def collect(
        self,
        stock_list: List[Dict[str, str]],
        date_range: timedelta = timedelta(days=1)
    ) -> List[NewsItem]:
        """
        从腾讯新闻采集股票相关新闻

        腾讯新闻 API:
        - 搜索 API：https://smartbox.gtimg.cn/s
        - 财经新闻：https://news.qq.com/ch/finance
        """
        all_news = []

        for stock in stock_list:
            stock_name = stock["name"]
            stock_code = stock["code"]

            try:
                # 搜索相关新闻
                search_news = await self._search_news(stock_name)
                all_news.extend(search_news)

                # 获取财经新闻
                finance_news = await self._get_finance_news(stock_name)
                all_news.extend(finance_news)

            except Exception as e:
                logger.error(f"腾讯新闻采集 {stock_name} 失败：{e}")

        logger.info(f"腾讯新闻采集完成，共获取 {len(all_news)} 条新闻")
        return all_news

    async def _search_news(
        self,
        stock_name: str
    ) -> List[NewsItem]:
        """搜索相关新闻"""
        news_list = []

        # 腾讯智能盒搜索 API
        search_url = "https://smartbox.gtimg.cn/s"
        params = {
            "w": stock_name,
            "t": "news",
            "q": stock_name,
        }

        try:
            response = await self.safe_request(search_url, params=params)
            data = response.json()

            if data.get("result") and data["result"].get("news"):
                for item in data["result"]["news"]:
                    title = item.get("title", "")

                    # 检查是否包含股票名称
                    if stock_name not in title:
                        continue

                    news_item = NewsItem(
                        stock_name=stock_name,
                        title=title,
                        content=item.get("abstract", ""),
                        source=self.get_source_name(),
                        url=item.get("url", ""),
                        publish_time=self._parse_time_str(item.get("time")),
                        image_url=item.get("image", "")
                    )
                    news_list.append(news_item)

        except Exception as e:
            logger.warning(f"搜索 {stock_name} 新闻失败：{e}")

        return news_list

    async def _get_finance_news(
        self,
        stock_name: str
    ) -> List[NewsItem]:
        """获取财经新闻"""
        news_list = []

        # 腾讯财经新闻 API
        finance_url = "https://r.inews.qq.com/api/lbs_newlist"
        params = {
            "cid": "finance",
            "page_size": 30,
        }

        try:
            response = await self.safe_request(finance_url, params=params)
            data = response.json()

            if data.get("newlist"):
                for item in data["newlist"]:
                    title = item.get("title", "")
                    content = item.get("abstract", "")

                    # 检查是否包含股票名称
                    if stock_name not in title and stock_name not in content:
                        continue

                    news_item = NewsItem(
                        stock_name=stock_name,
                        title=title,
                        content=content,
                        source=self.get_source_name(),
                        url=item.get("url", ""),
                        publish_time=self._parse_timestamp(item.get("timestamp")),
                        image_url=item.get("imgurl", "")
                    )
                    news_list.append(news_item)

        except Exception as e:
            logger.warning(f"获取财经新闻失败：{e}")

        return news_list

    def _parse_time_str(self, time_str: str) -> datetime:
        """解析时间字符串"""
        if not time_str:
            return datetime.now()

        # 腾讯新闻的时间格式
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%H:%M",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                # 如果只有时间，使用今天
                if dt.year == 1900:
                    dt = dt.replace(year=datetime.now().year)
                return dt
            except ValueError:
                continue

        return self.parse_date(time_str)

    def _parse_timestamp(self, timestamp) -> datetime:
        """解析时间戳"""
        if not timestamp:
            return datetime.now()

        try:
            if timestamp > 1e12:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp)
        except Exception:
            return datetime.now()
