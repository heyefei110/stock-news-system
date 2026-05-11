"""
雪球数据采集器
"""
from typing import List, Dict
from datetime import datetime, timedelta
from loguru import logger
from collectors.base import BaseCollector, NewsItem


class XueqiuCollector(BaseCollector):
    """雪球数据采集器"""

    def get_source_name(self) -> str:
        return "雪球"

    async def collect(
        self,
        stock_list: List[Dict[str, str]],
        date_range: timedelta = timedelta(days=1)
    ) -> List[NewsItem]:
        """
        从雪球采集股票相关新闻和讨论

        雪球 API (需要登录):
        - 股票动态：https://xueqiu.com/v4/statuses/list.json?symbol=XXXX
        - 股票新闻：https://xueqiu.com/query/v4/symbol/search/status.json?symbol=XXXX
        """
        all_news = []

        # 雪球需要登录才能访问 API
        # 用户可以通过 cookie 文件提供登录凭证
        cookie_path = "cookies/xueqiu.txt"
        cookies = await self._load_cookies(cookie_path)

        for stock in stock_list:
            stock_name = stock["name"]
            stock_code = stock["code"]
            market = stock.get("market", "HK")

            try:
                # 获取股票动态
                if stock_code:
                    stock_statuses = await self._get_stock_statuses(
                        stock_code, market, cookies
                    )
                    all_news.extend(stock_statuses)

                # 搜索相关讨论
                search_posts = await self._search_posts(stock_name, cookies)
                all_news.extend(search_posts)

            except Exception as e:
                logger.error(f"雪球采集 {stock_name} 失败：{e}")

        logger.info(f"雪球采集完成，共获取 {len(all_news)} 条内容")
        return all_news

    async def _load_cookies(self, cookie_path: str) -> Dict[str, str]:
        """加载 Cookie"""
        import os
        from pathlib import Path

        cookie_file = Path(cookie_path)
        if cookie_file.exists():
            try:
                content = cookie_file.read_text(encoding="utf-8")
                cookies = {}
                for line in content.strip().split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        cookies[key.strip()] = value.strip()
                return cookies
            except Exception as e:
                logger.warning(f"加载 Cookie 失败：{e}")

        return {}

    async def _get_stock_statuses(
        self,
        stock_code: str,
        market: str,
        cookies: Dict[str, str]
    ) -> List[NewsItem]:
        """获取股票动态"""
        news_list = []

        # 雪球股票动态 API
        statuses_url = "https://xueqiu.com/v4/statuses/list.json"

        # 股票代码格式转换
        symbol = self._format_stock_code(stock_code, market)

        params = {
            "symbol": symbol,
            "page": 1,
            "count": 20,
        }

        headers = self.get_headers()
        if cookies:
            headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        try:
            response = await self.client.get(
                statuses_url,
                params=params,
                headers=headers
            )

            if response.status_code == 401:
                logger.warning("雪球 API 需要登录，请提供 Cookie")
                return news_list

            data = response.json()

            if data.get("list"):
                for item in data["list"]:
                    title = item.get("title", "") or item.get("text", "")[:50]
                    text = item.get("text", "")

                    news_item = NewsItem(
                        stock_name=stock_code,
                        title=title,
                        content=text,
                        source=self.get_source_name(),
                        url=f"https://xueqiu.com{item.get('target', '')}" if item.get("target") else "",
                        publish_time=self._parse_timestamp(item.get("created_at")),
                        image_url=item.get("pic", "")
                    )
                    news_list.append(news_item)

        except Exception as e:
            logger.warning(f"获取 {stock_code} 动态失败：{e}")

        return news_list

    async def _search_posts(
        self,
        stock_name: str,
        cookies: Dict[str, str]
    ) -> List[NewsItem]:
        """搜索相关讨论"""
        news_list = []

        search_url = "https://xueqiu.com/query/v4/symbol/search/status.json"
        params = {
            "q": stock_name,
            "page": 1,
            "count": 20,
            "sort": "time"
        }

        headers = self.get_headers()
        if cookies:
            headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        try:
            response = await self.client.get(
                search_url,
                params=params,
                headers=headers
            )

            if response.status_code == 401:
                return news_list

            data = response.json()

            if data.get("list"):
                for item in data["list"]:
                    title = item.get("title", "") or item.get("text", "")[:50]
                    text = item.get("text", "")

                    # 检查是否包含股票名称
                    if stock_name not in text and stock_name not in title:
                        continue

                    news_item = NewsItem(
                        stock_name=stock_name,
                        title=title,
                        content=text,
                        source=self.get_source_name(),
                        url=f"https://xueqiu.com{item.get('target', '')}" if item.get("target") else "",
                        publish_time=self._parse_timestamp(item.get("created_at")),
                        image_url=item.get("pic", "")
                    )
                    news_list.append(news_item)

        except Exception as e:
            logger.warning(f"搜索 {stock_name} 失败：{e}")

        return news_list

    def _format_stock_code(self, code: str, market: str) -> str:
        """格式化股票代码为雪球格式"""
        if market == "HK":
            # 港股格式：HK00666
            return f"HK{code.replace('.HK', '')}"
        elif market == "US":
            # 美股格式：XXX
            return code
        else:
            # A 股格式：SH600000 或 SZ000001
            if code.startswith("6"):
                return f"SH{code}"
            else:
                return f"SZ{code}"

    def _parse_timestamp(self, timestamp) -> datetime:
        """解析时间戳"""
        if not timestamp:
            return datetime.now()

        try:
            # 毫秒级时间戳
            if timestamp > 1e12:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp)
        except Exception:
            return datetime.now()
