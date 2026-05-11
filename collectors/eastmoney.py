"""
东方财富数据采集器
"""
from typing import List, Dict
from datetime import datetime, timedelta
from loguru import logger
from collectors.base import BaseCollector, NewsItem


class EastmoneyCollector(BaseCollector):
    """东方财富数据采集器"""

    def get_source_name(self) -> str:
        return "东方财富"

    async def collect(
        self,
        stock_list: List[Dict[str, str]],
        date_range: timedelta = timedelta(days=1)
    ) -> List[NewsItem]:
        """
        从东方财富采集股票新闻

        东方财富 API:
        - 个股新闻：https://push2.eastmoney.com/api/qt/stock_announcement/get
        - 快讯：https://api.eastmoney.com/news/api/gettypearticlelist
        """
        all_news = []

        for stock in stock_list:
            stock_name = stock["name"]
            stock_code = stock["code"]
            market = stock.get("market", "HK")

            try:
                # 获取个股新闻
                if stock_code:
                    stock_news = await self._get_stock_news(stock_code, market)
                    all_news.extend(stock_news)

                # 搜索相关新闻
                search_news = await self._search_news(stock_name)
                all_news.extend(search_news)

                # 获取个股公告
                if stock_code:
                    announcements = await self._get_announcements(stock_code, market)
                    all_news.extend(announcements)

            except Exception as e:
                logger.error(f"东方财富采集 {stock_name} 失败：{e}")

        logger.info(f"东方财富采集完成，共获取 {len(all_news)} 条新闻")
        return all_news

    async def _get_stock_news(
        self,
        stock_code: str,
        market: str
    ) -> List[NewsItem]:
        """获取个股新闻"""
        news_list = []

        # 东方财富个股新闻 API
        news_url = "https://push2.eastmoney.com/api/qt/stock_announcement/get"

        # 处理股票代码格式
        api_code = self._format_stock_code(stock_code, market)

        params = {
            "secid": api_code,
            "pageIndex": 1,
            "pageSize": 20,
            "fields": "title,content,publish_time,url",
        }

        try:
            response = await self.safe_request(news_url, params=params)
            data = response.json()

            if data.get("data") and data["data"].get("articles"):
                for article in data["data"]["articles"]:
                    news_item = NewsItem(
                        stock_name=stock_code,
                        title=article.get("title", ""),
                        content=article.get("content", ""),
                        source=self.get_source_name(),
                        url=article.get("url", ""),
                        publish_time=self._parse_timestamp(article.get("publish_time"))
                    )
                    news_list.append(news_item)

        except Exception as e:
            logger.warning(f"获取 {stock_code} 新闻失败：{e}")

        return news_list

    async def _search_news(
        self,
        stock_name: str
    ) -> List[NewsItem]:
        """搜索相关新闻"""
        news_list = []

        # 东方财富搜索 API
        search_url = "https://search.eastmoney.com/api/json/search"
        params = {
            "keyword": stock_name,
            "pageIndex": 1,
            "pageSize": 20,
            "sort": "time",
            "t": "news"
        }

        try:
            response = await self.safe_request(search_url, params=params)
            data = response.json()

            if data.get("result"):
                for item in data["result"]:
                    title = item.get("title", "")
                    if stock_name not in title:
                        continue

                    news_item = NewsItem(
                        stock_name=stock_name,
                        title=title,
                        content=item.get("content", ""),
                        source=self.get_source_name(),
                        url=item.get("url", ""),
                        publish_time=self._parse_timestamp(item.get("pub_time"))
                    )
                    news_list.append(news_item)

        except Exception as e:
            logger.warning(f"搜索 {stock_name} 新闻失败：{e}")

        return news_list

    async def _get_announcements(
        self,
        stock_code: str,
        market: str
    ) -> List[NewsItem]:
        """获取公司公告"""
        news_list = []

        api_code = self._format_stock_code(stock_code, market)
        announcement_url = "https://push2.eastmoney.com/api/qt/stock_announcement/get"

        params = {
            "secid": api_code,
            "pageIndex": 1,
            "pageSize": 10,
        }

        try:
            response = await self.safe_request(announcement_url, params=params)
            data = response.json()

            if data.get("data") and data["data"].get("announcements"):
                for ann in data["data"]["announcements"]:
                    news_item = NewsItem(
                        stock_name=stock_code,
                        title=ann.get("title", ""),
                        content=ann.get("content", ""),
                        source=f"{self.get_source_name()}-公告",
                        url=ann.get("url", ""),
                        publish_time=self._parse_timestamp(ann.get("publish_time"))
                    )
                    news_list.append(news_item)

        except Exception as e:
            logger.warning(f"获取 {stock_code} 公告失败：{e}")

        return news_list

    def _format_stock_code(self, code: str, market: str) -> str:
        """格式化股票代码为东方财富 API 格式"""
        if market == "HK":
            # 港股格式：116.00666
            return f"116.{code.replace('.HK', '')}"
        elif market == "US":
            # 美股格式：105.XXX
            return f"105.{code}"
        else:
            # A 股格式：000001.XX 或 600000.XX
            if code.startswith("6"):
                return f"1.{code}"
            else:
                return f"0.{code}"

    def _parse_timestamp(self, timestamp) -> datetime:
        """解析时间戳"""
        if not timestamp:
            return datetime.now()

        try:
            # 秒级时间戳
            if timestamp > 1e12:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp)
        except Exception:
            return datetime.now()
