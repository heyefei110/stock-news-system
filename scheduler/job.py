"""
定时任务调度模块
"""
from typing import Optional, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from loguru import logger
import asyncio


class TaskScheduler:
    """任务调度器"""

    def __init__(
        self,
        cron_hour: int = 6,
        cron_minute: int = 0,
        timezone: str = "Asia/Shanghai"
    ):
        """
        初始化调度器

        Args:
            cron_hour: 执行小时
            cron_minute: 执行分钟
            timezone: 时区
        """
        self.cron_hour = cron_hour
        self.cron_minute = cron_minute
        self.timezone = timezone

        # 配置作业存储和执行器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(max_workers=5)
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone=timezone
        )

        self.job_callbacks = {}

    def add_job(
        self,
        job_id: str,
        func: Callable,
        cron_expression: Optional[str] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        **kwargs
    ):
        """
        添加定时任务

        Args:
            job_id: 任务 ID
            func: 任务函数
            cron_expression: cron 表达式 (可选)
            hour: 执行小时 (可选)
            minute: 执行分钟 (可选)
        """
        if cron_expression:
            # 使用 cron 表达式
            trigger = CronTrigger.from_crontab(
                cron_expression,
                timezone=self.timezone
            )
        else:
            # 使用默认时间
            trigger = CronTrigger(
                hour=hour or self.cron_hour,
                minute=minute or self.cron_minute,
                timezone=self.timezone
            )

        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            name=job_id,
            **kwargs
        )

        logger.info(f"添加定时任务：{job_id}, 执行时间：{hour or self.cron_hour}:{minute or self.cron_minute:02d}")

    def remove_job(self, job_id: str):
        """移除定时任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"移除任务：{job_id}")
        except Exception as e:
            logger.warning(f"移除任务失败：{e}")

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("调度器已启动")

    def shutdown(self, wait: bool = True):
        """关闭调度器"""
        self.scheduler.shutdown(wait=wait)
        logger.info("调度器已关闭")

    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """获取任务下次执行时间"""
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None

    def pause_job(self, job_id: str):
        """暂停任务"""
        self.scheduler.pause_job(job_id)
        logger.info(f"任务已暂停：{job_id}")

    def resume_job(self, job_id: str):
        """恢复任务"""
        self.scheduler.resume_job(job_id)
        logger.info(f"任务已恢复：{job_id}")


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


async def retry_async(
    func: Callable,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable] = None,
    *args,
    **kwargs
):
    """
    异步重试执行

    Args:
        func: 异步函数
        config: 重试配置
        on_retry: 重试回调
        *args: 函数参数
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果
    """
    if config is None:
        config = RetryConfig()

    last_exception = None
    delay = config.initial_delay

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"执行失败 (第 {attempt + 1}/{config.max_retries + 1} 次): {e}")

            if attempt < config.max_retries:
                if on_retry:
                    await on_retry(attempt, e)

                # 计算延迟
                actual_delay = min(delay, config.max_delay)
                if config.jitter:
                    import random
                    actual_delay *= (0.5 + random.random() * 0.5)

                logger.info(f"{actual_delay:.2f} 秒后重试")
                await asyncio.sleep(actual_delay)
                delay *= config.exponential_base

    logger.error(f"达到最大重试次数，最后错误：{last_exception}")
    raise last_exception


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟 (秒)
        exceptions: 需要重试的异常类型
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"{func.__name__} 失败 (第 {attempt + 1}/{max_retries + 1} 次): {e}")

                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        logger.error(f"{func.__name__} 达到最大重试次数")
                        raise

            raise last_exception
        return wrapper
    return decorator
