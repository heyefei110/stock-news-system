"""
LLM 智能摘要模块 - 使用 Claude API
"""
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
from loguru import logger
from collectors.base import NewsItem
from config.settings import settings
import anthropic


class NewsSummarizer:
    """新闻摘要生成器"""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """
        初始化摘要生成器

        Args:
            model: Claude 模型名称
        """
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def summarize(
        self,
        news_list: List[NewsItem],
        batch_size: int = 10
    ) -> List[NewsItem]:
        """
        批量生成新闻摘要

        Args:
            news_list: 新闻列表
            batch_size: 批次大小

        Returns:
            包含摘要的新闻列表
        """
        if not news_list:
            return []

        # 分批处理
        all_summarized = []
        for i in range(0, len(news_list), batch_size):
            batch = news_list[i:i + batch_size]
            tasks = [self._summarize_single(news) for news in batch]
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for news, result in zip(batch, results):
                    if isinstance(result, Exception):
                        logger.warning(f"生成摘要失败：{result}")
                        news.summary = self._fallback_summary(news)
                    else:
                        news.summary = result
                    all_summarized.append(news)
            except Exception as e:
                logger.error(f"批量处理失败，使用降级方案：{e}")
                for news in batch:
                    news.summary = self._fallback_summary(news)
                all_summarized.extend(batch)

        logger.info(f"摘要生成完成：{len(all_summarized)} 条")
        return all_summarized

    async def _summarize_single(
        self,
        news: NewsItem
    ) -> str:
        """为单条新闻生成摘要"""
        prompt = self._build_prompt(news)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.3,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的财经新闻摘要生成器。你的任务是从新闻标题和内容中提取关键信息，生成简洁、准确的摘要。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            summary = response.content[0].text.strip()
            return summary[:300]  # 限制摘要长度

        except Exception as e:
            logger.warning(f"Claude API 调用失败：{e}")
            raise

    def _build_prompt(self, news: NewsItem) -> str:
        """构建摘要提示词"""
        prompt = f"""请为以下财经新闻生成摘要：

**股票**: {news.stock_name}
**标题**: {news.title}
**来源**: {news.source}
**内容**: {news.content[:500] if news.content else '无'}

请生成一段不超过 100 字的摘要，要求:
1. 包含核心事件/信息
2. 突出对股票可能的影响
3. 保持客观中立
4. 如果内容不足，基于标题生成简短说明

摘要:"""
        return prompt

    def _fallback_summary(self, news: NewsItem) -> str:
        """降级摘要方案（当 LLM 不可用时）"""
        # 提取标题关键词作为摘要
        summary_parts = []

        if news.title:
            summary_parts.append(f"标题：{news.title}")

        if news.content:
            # 提取内容前 50 字
            content_preview = news.content[:50]
            if len(news.content) > 50:
                content_preview += "..."
            summary_parts.append(f"内容：{content_preview}")

        if news.source:
            summary_parts.append(f"来源：{news.source}")

        return " | ".join(summary_parts)

    async def classify_by_stock(
        self,
        news_list: List[NewsItem],
        stock_names: List[str]
    ) -> Dict[str, List[NewsItem]]:
        """
        使用 LLM 辅助将新闻按股票分类

        Args:
            news_list: 新闻列表
            stock_names: 股票名称列表

        Returns:
            按股票名称分组的新闻字典
        """
        classified = {name: [] for name in stock_names}
        unclassified = []

        for news in news_list:
            matched = False
            for stock_name in stock_names:
                if stock_name in news.title or stock_name in news.content:
                    classified[stock_name].append(news)
                    matched = True
                    break

            # 未匹配的新闻归入"未分类"
            if not matched:
                # 尝试用 LLM 判断
                stock_name = await self._classify_single(news, stock_names)
                if stock_name:
                    classified[stock_name].append(news)
                else:
                    unclassified.append(news)

        if unclassified:
            logger.info(f"有 {len(unclassified)} 条新闻无法分类")

        return classified

    async def _classify_single(
        self,
        news: NewsItem,
        stock_names: List[str]
    ) -> Optional[str]:
        """使用 LLM 判断单条新闻属于哪个股票"""
        if not news.content or len(news.content) < 20:
            return None

        prompt = f"""判断以下新闻与哪个股票最相关:

候选股票：{', '.join(stock_names)}

新闻标题：{news.title}
新闻内容：{news.content[:200]}

请只返回最相关的股票名称，如果没有匹配的返回空字符串。"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            result = response.content[0].text.strip()
            if result in stock_names:
                return result
            return None

        except Exception:
            return None

    async def extract_key_info(
        self,
        news_list: List[NewsItem]
    ) -> List[Dict]:
        """
        提取新闻的关键信息

        Returns:
            包含关键信息的字典列表
        """
        tasks = []
        for news in news_list[:20]:  # 限制处理数量
            tasks.append(self._extract_single(news))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        key_info_list = []
        for news, result in zip(news_list[:20], results):
            if isinstance(result, Exception):
                key_info_list.append({
                    "title": news.title,
                    "type": "未知",
                    "impact": "未知",
                    "summary": self._fallback_summary(news)
                })
            else:
                key_info_list.append(result)

        return key_info_list

    async def _extract_single(self, news: NewsItem) -> Dict:
        """提取单条新闻的关键信息"""
        prompt = f"""分析以下财经新闻，提取关键信息:

**标题**: {news.title}
**内容**: {news.content[:500] if news.content else '无'}

请以 JSON 格式返回:
{{
    "type": "公告/业绩/并购/政策/市场/其他",
    "impact": "正面/负面/中性",
    "summary": "50 字以内的核心摘要"
}}

只返回 JSON，不要其他内容。"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            import json
            result = response.content[0].text.strip()
            # 提取 JSON 部分
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
            else:
                raise ValueError("无法解析 JSON")

        except Exception as e:
            logger.warning(f"提取关键信息失败：{e}")
            return {
                "type": "未知",
                "impact": "未知",
                "summary": self._fallback_summary(news)
            }
