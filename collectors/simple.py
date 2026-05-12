"""
数据采集器 - 专注公司公告和重要消息
"""
from typing import List, Dict
from datetime import datetime, timedelta
from loguru import logger
from collectors.base import BaseCollector, NewsItem


class SimpleFinanceCollector(BaseCollector):
    """
    财经新闻采集器 - 专注公司公告和重要消息
    使用 akshare 获取东方财富的公告和要闻数据
    """

    def get_source_name(self) -> str:
        return "公司公告采集器"

    async def collect(
        self,
        stock_list: List[Dict[str, str]],
        date_range: timedelta = timedelta(days=3)
    ) -> List[NewsItem]:
        """
        采集新闻

        Args:
            stock_list: 股票列表
            date_range: 时间范围，默认 3 天
        """
        all_news = []

        for stock in stock_list:
            stock_name = stock["name"]
            stock_code = stock["code"]
            market = stock.get("market", "HK")

            logger.info(f"开始采集 {stock_name} ({stock_code}) 的信息...")

            try:
                # 获取公司公告和重要消息
                news = self._fetch_announcements_and_news(stock_name, stock_code, market, date_range)
                all_news.extend(news)

            except Exception as e:
                logger.error(f"采集 {stock_name} 失败：{e}")

        logger.info(f"采集完成，共获取 {len(all_news)} 条重要信息")
        return all_news

    def _fetch_announcements_and_news(self, stock_name: str, stock_code: str, market: str, date_range: timedelta) -> List[NewsItem]:
        """
        获取公司公告和重要消息
        """
        news_list = []

        try:
            import akshare as ak

            # 获取股票信息
            stock_news = ak.stock_news_em(symbol=stock_name)

            if stock_news is None or len(stock_news) == 0:
                logger.warning(f"akshare 未获取到 {stock_name} 的信息")
                return news_list

            # 计算 cutoff 日期
            cutoff_date = datetime.now() - date_range

            # 遍历新闻，筛选重要信息
            for _, row in stock_news.iterrows():
                try:
                    title = row.get("新闻标题", "")
                    content = row.get("新闻内容", "")
                    publish_time_str = row.get("发布时间", "")
                    source = row.get("文章来源", "东方财富")
                    url = row.get("新闻链接", "")

                    # 解析时间
                    publish_time = self._parse_publish_time(publish_time_str)

                    # 只保留最近 N 天的信息
                    if publish_time < cutoff_date:
                        continue

                    # 过滤：只保留重要信息
                    if not self._is_important_news(title, content):
                        logger.debug(f"跳过非重要新闻：{title[:30]}")
                        continue

                    # 创建新闻对象
                    news_item = NewsItem(
                        stock_name=stock_name,
                        title=title,
                        content=content[:500] if content else "",
                        source=f"东方财富-{source}",
                        url=url,
                        publish_time=publish_time
                    )
                    news_list.append(news_item)
                    logger.info(f"采集到重要信息：{title[:50]}")

                except Exception as e:
                    logger.warning(f"解析单条信息失败：{e}")
                    continue

            logger.info(f"从 akshare 获取 {stock_name} 共 {len(news_list)} 条重要信息")

        except ImportError:
            logger.error("akshare 未安装，请运行：pip install akshare")
        except Exception as e:
            logger.error(f"获取信息失败：{e}")

        return news_list

    def _is_important_news(self, title: str, content: str) -> bool:
        """判断是否为重要新闻"""
        text = title + " " + content

        # 重要信息关键词
        important_keywords = [
            # 公告类
            "公告", "公示", "披露", "宣布",
            # 业绩类
            "业绩", "财报", "年报", "中报", "季报", "盈利", "亏损", "营收", "利润", "净利润",
            # 回购类
            "回购", "增持", "减持",
            # 投资并购类
            "投资", "并购", "收购", "出售", "资产", "股权", "合资", "合作",
            # 合同类
            "合同", "订单", "中标",
            # 人事类
            "高管", "总裁", "CEO", "董事长", "总经理", "人事", "辞职", "任命",
            # 分红类
            "分红", "派息", "股息", "红利",
            # 停牌类
            "停牌", "复牌",
            # 法律类
            "诉讼", "仲裁", "调查",
            # 其他重要
            "战略", "重组", "重整", "破产", "清算", "配股", "供股", "可转债"
        ]

        # 排除关键词（纯股价报道）
        exclude_keywords = [
            "涨", "跌", "拉升", "下跌", "收涨", "收跌",
            "股价", "股价上涨", "股价下跌",
            "创历史新高", "创新低",
            "领涨", "领跌",
            "跑赢大盘", "跑输大盘",
            "异动", "跳水"
        ]

        # 检查是否包含重要信息关键词
        has_important = any(kw in title for kw in important_keywords)

        # 如果是标题包含重要关键词，直接返回 True
        if has_important:
            return True

        # 检查是否是纯股价报道
        is_price_only = any(kw in text for kw in exclude_keywords)

        # 如果是纯股价报道，排除
        if is_price_only:
            return False

        # 其他情况默认保留（可能是其他重要信息）
        return True

    def _parse_publish_time(self, time_str: str) -> datetime:
        """解析发布时间"""
        if not time_str:
            return datetime.now()

        try:
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        try:
            return datetime.strptime(time_str, "%Y-%m-%d")
        except ValueError:
            pass

        return datetime.now()


class StockPriceCollector(BaseCollector):
    """
    股价数据采集器 - 获取港股股价信息
    """

    def get_source_name(self) -> str:
        return "股价数据"

    async def collect(
        self,
        stock_list: List[Dict[str, str]],
        date_range: timedelta = timedelta(days=1)
    ) -> List[NewsItem]:
        """采集股价信息"""
        all_news = []

        for stock in stock_list:
            stock_name = stock["name"]
            stock_code = stock["code"]
            market = stock.get("market", "HK")

            try:
                price_info = self._fetch_price_info(stock_code, market, stock_name)
                if price_info:
                    news_item = NewsItem(
                        stock_name=stock_name,
                        title=f"{stock_name} 股价信息",
                        content=price_info,
                        source=self.get_source_name(),
                        url="",
                        publish_time=datetime.now()
                    )
                    all_news.append(news_item)

            except Exception as e:
                logger.warning(f"采集 {stock_name} 股价失败：{e}")

        return all_news

    def _fetch_price_info(self, stock_code: str, market: str, stock_name: str) -> str:
        """获取股价信息"""
        try:
            import akshare as ak

            # 去除.HK 后缀
            code = stock_code.replace(".HK", "")

            if market == "HK":
                # 获取港股实时行情
                stock_hk_spot = ak.stock_hk_spot()
                if stock_hk_spot is not None and len(stock_hk_spot) > 0:
                    # 查找对应股票（通过代码）
                    # 列名：['日期时间', '代码', '中文名称', '英文名称', '交易类型', '最新价', '涨跌额', '涨跌幅', ...]
                    stock_data = stock_hk_spot[
                        (stock_hk_spot['代码'] == code) |
                        (stock_hk_spot['中文名称'].str.contains(stock_name, na=False))
                    ]

                    if len(stock_data) > 0:
                        row = stock_data.iloc[0]
                        latest_price = row.get('最新价', 'N/A')
                        change_pct = row.get('涨跌幅', 'N/A')
                        change = row.get('涨跌额', 'N/A')

                        return f"""【{stock_name} ({code}.HK) 股价摘要】
最新价：{latest_price} 港元
涨跌幅：{change_pct}%
涨跌额：{change} 港元
数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"""

            return f"暂无 {stock_name} 股价数据"

        except Exception as e:
            logger.debug(f"获取股价失败：{e}")
            return f"暂无 {stock_name} 股价数据"
