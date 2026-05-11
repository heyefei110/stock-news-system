"""
新闻去重模块 - 纯 Python 实现
"""
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from loguru import logger
from collectors.base import NewsItem
import hashlib


class NewsDeduplicator:
    """新闻去重器"""

    def __init__(self, threshold: int = 3):
        """
        初始化去重器

        Args:
            threshold: 相似度阈值（保留用于兼容）
        """
        self.threshold = threshold

    def deduplicate(
        self,
        news_list: List[NewsItem],
        respect_source: bool = True
    ) -> List[NewsItem]:
        """
        对新闻列表进行去重

        Args:
            news_list: 新闻列表
            respect_source: 是否区分来源

        Returns:
            去重后的新闻列表
        """
        if not news_list:
            return []

        original_count = len(news_list)

        # 按来源分组
        if respect_source:
            source_groups = defaultdict(list)
            for news in news_list:
                source_groups[news.source].append(news)

            deduped_list = []
            for source, items in source_groups.items():
                deduped_items = self._deduplicate_group(items)
                deduped_list.extend(deduped_items)
                logger.info(f"来源 {source}: {len(items)} -> {len(deduped_items)} 条")
        else:
            deduped_list = self._deduplicate_group(news_list)

        logger.info(f"去重完成，原始：{original_count}, 去重后：{len(deduped_list)}")
        return deduped_list

    def _deduplicate_group(
        self,
        news_list: List[NewsItem]
    ) -> List[NewsItem]:
        """对一组新闻进行去重"""
        seen_urls: Set[str] = set()
        seen_titles: Set[str] = set()
        deduped_list = []

        for news in news_list:
            # 检查 URL 是否重复
            if news.url:
                url_hash = self._hash(news.url)
                if url_hash in seen_urls:
                    logger.debug(f"URL 重复：{news.url}")
                    continue
                seen_urls.add(url_hash)

            # 检查标题是否重复
            title_hash = self._hash(news.title)
            if title_hash in seen_titles:
                logger.debug(f"标题重复：{news.title}")
                continue
            seen_titles.add(title_hash)

            deduped_list.append(news)

        return deduped_list

    def _hash(self, text: str) -> str:
        """计算文本的 MD5 哈希"""
        if not text:
            return ""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get_similar_news(
        self,
        news: NewsItem,
        news_list: List[NewsItem]
    ) -> List[NewsItem]:
        """获取相似新闻（简化版：只匹配标题）"""
        title_hash = self._hash(news.title)
        similar_list = []

        for item in news_list:
            if self._hash(item.title) == title_hash:
                similar_list.append(item)

        return similar_list
