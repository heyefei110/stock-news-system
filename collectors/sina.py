"""
新浪财经数据采集器
"""
from typing import List, Dict
from datetime import datetime, timedelta
from loguru import logger
from collectors.base import BaseCollector, NewsItem


class SinaCollector(BaseCollector):
    """新浪财经数据采集器"""

    def get_source_name(self) -> str:
        return "新浪财经"

    async def collect(
        self,
        stock_list: List[Dict[str, str]],
        date_range: timedelta = timedelta(days=1)
    ) -> List[NewsItem]:
        """
        从新浪财经采集股票新闻

        新浪财经 API:
        - 港股实时新闻：https://quote.sina.com.cn/hkstock/news/
        - 新闻列表 API：https://finance.sina.com.cn/stock/relnews/[market]/2024-01-01/[code].json
        """
        all_news = []

        for stock in stock_list:
            stock_name = stock["name"]
            stock_code = stock["code"]
            market = stock.get("market", "HK")

            try:
                # 搜索股票相关新闻
                news_list = await self._search_stock_news(stock_name, stock_code)
                all_news.extend(news_list)

                # 如果有股票代码，尝试获取特定股票新闻
                if stock_code:
                    specific_news = await self._get_stock_specific_news(stock_code, market)
                    all_news.extend(specific_news)

            except Exception as e:
                logger.error(f"新浪财经采集 {stock_name} 失败：{e}")

        logger.info(f"新浪财经采集完成，共获取 {len(all_news)} 条新闻")
        return all_news

    async def _search_stock_news(
        self,
        stock_name: str,
        stock_code: str
    ) -> List[NewsItem]:
        """搜索股票相关新闻"""
        news_list = []

        # 使用新浪财经搜索 API
        search_url = "https://search.sina.com.cn/"
        params = {
            "q": stock_name,
            "range": "news",
            "c": "stock",
            "num": 20,
            "ie": "utf-8"
        }

        try:
            response = await self.safe_request(search_url, params=params)
            results = self._parse_search_results(response.text, stock_name)
            news_list.extend(results)
        except Exception as e:
            logger.warning(f"新浪财经搜索 {stock_name} 失败：{e}")

        return news_list

    async def _get_stock_specific_news(
        self,
        stock_code: str,
        market: str
    ) -> List[NewsItem]:
        """获取特定股票的新闻"""
        news_list = []

        # 港股新闻 API
        market_code = "hk" if market == "HK" else market.lower()
        news_url = f"https://finance.sina.com.cn/stock/relnews/{market_code}/"

        try:
            response = await self.safe_request(news_url)
            # 解析 HTML 获取新闻列表
            news_items = self._parse_stock_news_html(response.text, stock_code)
            news_list.extend(news_items)
        except Exception as e:
            logger.warning(f"获取 {stock_code} 特定新闻失败：{e}")

        return news_list

    def _parse_search_results(
        self,
        html: str,
        stock_name: str
    ) -> List[NewsItem]:
        """解析搜索结果"""
        from bs4 import BeautifulSoup

        news_list = []
        soup = BeautifulSoup(html, "lxml")

        # 查找新闻条目
        for item in soup.select(".result, .news-result"):
            try:
                title_elem = item.select_one(".title, h3 a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # 检查是否包含股票名称
                if stock_name not in title:
                    continue

                url = title_elem.get("href", "")
                if url.startswith("//"):
                    url = "https:" + url

                content_elem = item.select_one(".content, .summary")
                content = content_elem.get_text(strip=True) if content_elem else ""

                date_elem = item.select_one(".date, .time")
                date_str = date_elem.get_text(strip=True) if date_elem else ""
                publish_time = self.parse_date(date_str)

                news_item = NewsItem(
                    stock_name=stock_name,
                    title=title,
                    content=content,
                    source=self.get_source_name(),
                    url=url,
                    publish_time=publish_time
                )
                news_list.append(news_item)

            except Exception as e:
                logger.warning(f"解析新闻条目失败：{e}")
                continue

        return news_list

    def _parse_stock_news_html(
        self,
        html: str,
        stock_code: str
    ) -> List[NewsItem]:
        """解析股票新闻 HTML"""
        from bs4 import BeautifulSoup
        import json

        news_list = []

        try:
            # 新浪财经返回的可能是 JSONP 或 JSON
            soup = BeautifulSoup(html, "lxml")

            # 查找新闻列表
            for item in soup.select(".list-item, .news-item"):
                title_elem = item.select_one("a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")

                date_elem = item.select_one(".date, .time")
                date_str = date_elem.get_text(strip=True) if date_elem else ""
                publish_time = self.parse_date(date_str)

                news_item = NewsItem(
                    stock_name=stock_code,
                    title=title,
                    source=self.get_source_name(),
                    url=url,
                    publish_time=publish_time
                )
                news_list.append(news_item)

        except Exception as e:
            logger.error(f"解析 HTML 失败：{e}")

        return news_list
