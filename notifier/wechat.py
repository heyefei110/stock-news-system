"""
微信推送模块 - 修正版
"""
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
from loguru import logger
from collectors.base import NewsItem
from config.settings import settings
import httpx


class WeChatNotifier:
    """微信推送器"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
        self.push_method = self._detect_push_method()

    def _detect_push_method(self) -> str:
        """检测可用的推送方式"""
        logger.info(f"检测推送方式：serverchan_sendkey={settings.serverchan_sendkey[:10] if settings.serverchan_sendkey else 'None'}...")
        if settings.serverchan_sendkey:
            logger.info("使用 Server 酱推送")
            return "serverchan"
        elif settings.geWe_bot_url:
            return "gewe"
        elif settings.wcf_host and settings.wcf_host != "127.0.0.1":
            return "wcf"
        else:
            logger.warning("未配置任何微信推送方式，将使用日志输出")
            return "log"

    async def push(
        self,
        stock_news_map: Dict[str, List[NewsItem]],
        retry_count: int = 3
    ) -> bool:
        """
        推送新闻到微信

        Args:
            stock_news_map: 按股票分组的新闻字典
            retry_count: 重试次数

        Returns:
            是否推送成功
        """
        if not stock_news_map:
            logger.info("没有需要推送的新闻")
            return True

        # 生成推送内容
        message = self._format_message(stock_news_map)

        # 尝试推送
        for attempt in range(retry_count):
            try:
                success = await self._do_push(message)
                if success:
                    logger.info("微信推送成功")
                    return True
                logger.warning(f"推送失败，第 {attempt + 1} 次重试")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"推送异常：{e}，第 {attempt + 1} 次重试")
                await asyncio.sleep(5)

        logger.error("微信推送失败，已达到最大重试次数")
        return False

    def _format_message(
        self,
        stock_news_map: Dict[str, List[NewsItem]]
    ) -> str:
        """
        格式化推送消息
        """
        lines = []
        total_news = sum(len(v) for v in stock_news_map.values())

        # 标题
        lines.append("【股票资讯日报】")
        lines.append(f"推送时间：{datetime.now().strftime('%m-%d %H:%M')}")
        lines.append(f"总计：{len(stock_news_map)} 只股票，{total_news} 条资讯")
        lines.append("=" * 40)

        # 按股票输出
        for stock_name, news_list in stock_news_map.items():
            if not news_list:
                continue

            lines.append("")
            lines.append(f"【{stock_name}】{len(news_list)} 条")
            lines.append("-" * 30)

            for i, news in enumerate(news_list[:10], 1):
                time_str = ""
                if news.publish_time:
                    time_str = news.publish_time.strftime("%H:%M")

                title = news.title[:50]
                lines.append(f"  {i}. [{time_str}] {title}")

                if news.summary:
                    summary = news.summary[:80]
                    lines.append(f"     - {summary}")

                lines.append(f"     来源：{news.source}")

            if len(news_list) > 10:
                lines.append(f"  ... 还有 {len(news_list) - 10} 条")

        lines.append("")
        lines.append("=" * 40)
        lines.append("详细资讯请登录相关网站查看")

        return "\n".join(lines)

    async def _do_push(self, message: str) -> bool:
        """执行推送"""
        if self.push_method == "serverchan":
            return await self._push_serverchan(message)
        elif self.push_method == "gewe":
            return await self._push_gewe(message)
        elif self.push_method == "wcf":
            return await self._push_wcf(message)
        else:
            return self._push_log(message)

    async def _push_serverchan(self, message: str) -> bool:
        """Server 酱推送"""
        if not settings.serverchan_sendkey:
            return False

        lines = message.split("\n")
        title = lines[0] if lines else "股票资讯"
        content = "\n".join(lines[1:])

        url = f"https://sctapi.ftqq.com/{settings.serverchan_sendkey}.send"
        data = {"title": title, "desp": content}

        response = await self.client.post(url, data=data)
        result = response.json()
        return result.get("code") == 0

    async def _push_gewe(self, message: str) -> bool:
        """Gewebot 推送"""
        if not settings.ge We_bot_url:
            return False

        url = f"{settings.ge We_bot_url}/api/v1/message/text"
        headers = {
            "Authorization": f"Bearer {settings.ge We_bot_token}",
            "Content-Type": "application/json"
        }
        data = {"content": message}

        response = await self.client.post(url, json=data, headers=headers)
        return response.status_code == 200

    async def _push_wcf(self, message: str) -> bool:
        """WeChatFerry 推送"""
        url = f"http://{settings.wcf_host}:{settings.wcf_port}/send_text"
        data = {"msg": message}

        try:
            response = await self.client.post(url, json=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"WeChatFerry 推送失败：{e}")
            return False

    def _push_log(self, message: str) -> bool:
        """日志输出"""
        logger.info("=== 微信推送内容 ===")
        logger.info(message)
        return True

    async def send_alert(
        self,
        alert_type: str,
        message: str,
        error: Optional[str] = None
    ) -> bool:
        """发送告警"""
        alert_msg = f"""[系统告警]
类型：{alert_type}
时间：{datetime.now().strftime('%m-%d %H:%M:%S')}
内容：{message}
{f'错误：{error}' if error else ''}"""

        success = await self._do_push(alert_msg)

        if not success and settings.smtp_user:
            await self._send_email_alert(alert_type, message, error)

        return success

    async def _send_email_alert(
        self,
        alert_type: str,
        message: str,
        error: Optional[str] = None
    ) -> bool:
        """邮件告警"""
        import smtplib
        from email.mime.text import MIMEText

        try:
            content = f"""
类型：{alert_type}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
内容：{message}
{f'错误：{error}' if error else ''}
            """.strip()

            msg = MIMEText(content, "plain", "utf-8")
            msg["Subject"] = f"[股票资讯系统告警] {alert_type}"
            msg["From"] = settings.smtp_user
            msg["To"] = settings.alert_email

            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info("邮件告警发送成功")
            return True
        except Exception as e:
            logger.error(f"邮件告警失败：{e}")
            return False

    async def close(self):
        await self.client.aclose()
