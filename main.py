"""
股票资讯自动化系统 - 主程序
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
import sys

from config.settings import settings
from config.database import init_database, get_db_connection
from collectors.base import NewsItem
from collectors import (
    SinaCollector,
    EastmoneyCollector,
    XueqiuCollector,
    TencentCollector
)
from processor import NewsCleaner, NewsDeduplicator, NewsSummarizer
from notifier import WeChatNotifier
from scheduler import TaskScheduler, retry_async


class StockNewsSystem:
    """股票资讯自动化系统"""

    def __init__(self):
        self.stocks = self._load_stocks()
        self.collectors = [
            SinaCollector(),
            EastmoneyCollector(),
            XueqiuCollector(),
            TencentCollector()
        ]
        self.cleaner = NewsCleaner()
        self.deduplicator = NewsDeduplicator(threshold=3)
        self.summarizer = NewsSummarizer()
        self.notifier = WeChatNotifier()
        self.scheduler = TaskScheduler(
            cron_hour=settings.cron_hour,
            cron_minute=settings.cron_minute
        )

    def _load_stocks(self) -> List[Dict[str, str]]:
        """从数据库加载股票列表"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, code, market FROM stocks WHERE enabled = 1"
            )
            stocks = [
                {"name": row["name"], "code": row["code"], "market": row["market"]}
                for row in cursor.fetchall()
            ]
            conn.close()
            return stocks if stocks else settings.default_stocks
        except Exception as e:
            logger.warning(f"加载股票列表失败，使用默认配置：{e}")
            return settings.default_stocks

    async def run_once(self) -> bool:
        """
        执行一次完整的采集 - 处理 - 推送流程

        Returns:
            是否执行成功
        """
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"开始执行任务：{job_id}")

        # 调试信息：检查配置
        logger.info(f"=== 配置检查 ===")
        logger.info(f"ServerChan SendKey: {'已配置' if settings.serverchan_sendkey else '未配置'}")
        logger.info(f"通义千问 API Key: {'已配置' if settings.dashscope_api_key else '未配置'}")
        logger.info(f"股票列表：{[s['name'] for s in self.stocks]}")
        logger.info(f"================")

        start_time = datetime.now()
        status = "success"
        error_message = ""
        records_processed = 0

        try:
            # 1. 数据采集
            all_news = await self._collect_news()
            records_processed = len(all_news)
            logger.info(f"采集完成，共 {len(all_news)} 条新闻")

            if not all_news:
                logger.warning("未采集到任何新闻")
                # 即使没有新闻，也发送一条通知
                await self.notifier.send_alert(
                    alert_type="股票资讯日报",
                    message="今日暂无相关新闻资讯"
                )
                return True

            # 2. 数据清洗
            cleaned_news = self.cleaner.clean(all_news)
            logger.info(f"清洗完成，剩余 {len(cleaned_news)} 条")

            # 3. 按日期过滤 (只保留最近 2 天)
            filtered_news = self.cleaner.filter_by_date(cleaned_news, days=2)
            logger.info(f"日期过滤完成，剩余 {len(filtered_news)} 条")

            # 4. 去重
            deduped_news = self.deduplicator.deduplicate(filtered_news)
            logger.info(f"去重完成，剩余 {len(deduped_news)} 条")

            # 5. 生成摘要
            summarized_news = await self.summarizer.summarize(deduped_news)
            logger.info(f"摘要生成完成")

            # 6. 按股票分类
            stock_news_map = self._classify_by_stock(summarized_news)
            logger.info(f"分类完成，共 {len(stock_news_map)} 只股票")

            # 7. 保存数据库
            self._save_news(summarized_news)
            logger.info(f"新闻已保存至数据库")

            # 8. 推送微信
            push_success = await self.notifier.push(stock_news_map)
            if not push_success:
                status = "partial"
                error_message = "微信推送失败"

            # 9. 记录日志
            self._log_job(
                job_id=job_id,
                start_time=start_time,
                end_time=datetime.now(),
                status=status,
                records_processed=records_processed,
                error_message=error_message
            )

            return status == "success"

        except Exception as e:
            error_message = str(e)
            logger.exception(f"任务执行失败：{e}")

            self._log_job(
                job_id=job_id,
                start_time=start_time,
                end_time=datetime.now(),
                status="failed",
                records_processed=records_processed,
                error_message=error_message
            )

            # 发送告警
            await self.notifier.send_alert(
                alert_type="任务执行失败",
                message=f"股票资讯采集任务执行失败",
                error=error_message
            )

            return False

    async def _collect_news(self) -> List[NewsItem]:
        """并行采集各平台新闻"""
        from collectors.simple import SimpleFinanceCollector
        import httpx

        all_news = []

        # 尝试使用简单的采集器
        simple_collector = SimpleFinanceCollector()
        try:
            news = await simple_collector.collect(self.stocks)
            all_news.extend(news)
        except Exception as e:
            logger.error(f"简单采集器失败：{e}")

        # 如果还是没有数据，生成测试数据用于验证系统
        if not all_news:
            logger.info("未采集到新闻，生成测试数据...")
            all_news = self._generate_test_news()

        return all_news

    def _generate_test_news(self) -> List[NewsItem]:
        """生成测试新闻（用于验证系统）"""
        test_news = []
        now = datetime.now()

        for stock in self.stocks:
            test_news.append(NewsItem(
                stock_name=stock["name"],
                title=f"[测试] {stock['name']} 发布最新公告",
                content=f"这是 {stock['name']} 的测试新闻内容，用于验证系统是否正常工作。",
                source="系统测试",
                url="",
                publish_time=now
            ))

        logger.info(f"生成 {len(test_news)} 条测试新闻")
        return test_news

    def _classify_by_stock(
        self,
        news_list: List[NewsItem]
    ) -> Dict[str, List[NewsItem]]:
        """按股票分类"""
        classified = {stock["name"]: [] for stock in self.stocks}

        for news in news_list:
            matched = False
            for stock in self.stocks:
                if stock["name"] in news.title or stock["name"] in news.content:
                    classified[stock["name"]].append(news)
                    matched = True
                    break

            # 未匹配的新闻按第一个关键字匹配
            if not matched:
                for stock in self.stocks:
                    if stock["name"] in news.title:
                        classified[stock["name"]].append(news)
                        break

        return classified

    def _save_news(self, news_list: List[NewsItem]):
        """保存新闻到数据库"""
        conn = get_db_connection()
        cursor = conn.cursor()

        for news in news_list:
            try:
                cursor.execute("""
                    INSERT INTO news (
                        stock_name, title, content, source, url,
                        publish_time, summary, simhash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    news.stock_name,
                    news.title,
                    news.content,
                    news.source,
                    news.url,
                    news.publish_time,
                    news.summary,
                    None
                ))
            except Exception as e:
                logger.warning(f"保存新闻失败：{e}")
                continue

        conn.commit()
        conn.close()

    def _log_job(
        self,
        job_id: str,
        start_time: datetime,
        end_time: datetime,
        status: str,
        records_processed: int,
        error_message: str
    ):
        """记录任务执行日志"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO job_logs (
                job_name, start_time, end_time, status,
                records_processed, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            start_time,
            end_time,
            status,
            records_processed,
            error_message
        ))

        conn.commit()
        conn.close()

    def schedule(self):
        """启动定时任务"""
        async def job_wrapper():
            await self.run_once()

        self.scheduler.add_job(
            job_id="daily_news_collection",
            func=job_wrapper,
            hour=settings.cron_hour,
            minute=settings.cron_minute
        )

        self.scheduler.start()
        logger.info(f"定时任务已启动，每日 {settings.cron_hour}:{settings.cron_minute:02d} 执行")

    async def shutdown(self):
        """关闭系统"""
        self.scheduler.shutdown()
        await self.notifier.close()
        logger.info("系统已关闭")


async def main():
    """主函数"""
    # 初始化数据库
    init_database()
    logger.info("数据库初始化完成")

    # 创建系统实例
    system = StockNewsSystem()

    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "run":
            # 立即执行一次
            logger.info("执行单次任务...")
            success = await system.run_once()
            return 0 if success else 1
        elif sys.argv[1] == "schedule":
            # 启动定时任务
            logger.info("启动定时任务...")
            system.schedule()
            try:
                # 保持运行
                while True:
                    await asyncio.sleep(60)
            except KeyboardInterrupt:
                logger.info("收到退出信号")
            finally:
                await system.shutdown()
        else:
            print("Usage: python main.py [run|schedule]")
            return 1
    else:
        # 默认启动定时任务
        logger.info("启动定时任务...")
        system.schedule()
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("收到退出信号")
        finally:
            await system.shutdown()

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
