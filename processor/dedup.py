"""
新闻去重模块 - 使用 SimHash 算法
"""
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from loguru import logger
from collectors.base import NewsItem
import simhash


class NewsDeduplicator:
    """新闻去重器"""

    def __init__(self, threshold: int = 3):
        """
        初始化去重器

        Args:
            threshold: SimHash 相似度阈值，越小去重越严格
        """
        self.threshold = threshold
        self.hash_to_news: Dict[int, List[NewsItem]] = defaultdict(list)

    def deduplicate(
        self,
        news_list: List[NewsItem],
        respect_source: bool = True
    ) -> List[NewsItem]:
        """
        对新闻列表进行去重

        Args:
            news_list: 新闻列表
            respect_source: 是否区分来源，True 时不同来源的相似新闻不会去重

        Returns:
            去重后的新闻列表
        """
        if not news_list:
            return []

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

        logger.info(f"去重完成，原始：{len(news_list)}, 去重后：{len(deduped_list)}")
        return deduped_list

    def _deduplicate_group(
        self,
        news_list: List[NewsItem]
    ) -> List[NewsItem]:
        """对一组新闻进行去重"""
        deduped_list = []
        seen_hashes: Set[Tuple[int, int]] = set()  # (title_hash, content_hash)

        # 首先按 URL 去重
        url_seen: Set[str] = set()
        unique_news = []

        for news in news_list:
            if news.url and news.url in url_seen:
                continue
            if news.url:
                url_seen.add(news.url)
            unique_news.append(news)

        # 然后按 SimHash 去重
        for news in unique_news:
            title_hash = self._compute_title_hash(news.title)
            content_hash = self._compute_content_hash(news.content)

            hash_key = (title_hash, content_hash)

            # 检查是否与已见过的新闻相似
            is_duplicate = False
            for seen_hash in seen_hashes:
                if self._is_similar(hash_key, seen_hash):
                    is_duplicate = True
                    # 保留发布时间更新的
                    if news.publish_time > self._find_news_by_hash(
                        deduped_list, seen_hash
                    ).publish_time:
                        deduped_list = [
                            n for n in deduped_list
                            if self._get_hash_key(n) != seen_hash
                        ]
                        seen_hashes.discard(seen_hash)
                        seen_hashes.add(hash_key)
                        deduped_list.append(news)
                    break

            if not is_duplicate:
                seen_hashes.add(hash_key)
                deduped_list.append(news)

        return deduped_list

    def _compute_title_hash(self, title: str) -> int:
        """计算标题的 SimHash"""
        if not title:
            return 0

        # 将标题分词
        words = self._tokenize(title)
        return simhash.SimHash(words).hash

    def _compute_content_hash(self, content: str) -> int:
        """计算内容的 SimHash"""
        if not content:
            return 0

        # 取内容前 500 字计算
        content = content[:500]
        words = self._tokenize(content)
        return simhash.SimHash(words).hash

    def _tokenize(self, text: str) -> List[str]:
        """
        简单分词 (按字符和词语边界)

        为了更好的效果，可以引入 jieba 分词
        """
        # 简单实现：按 2-gram 分词
        words = []
        for i in range(len(text) - 1):
            words.append(text[i:i+2])
        return words if words else [text]

    def _is_similar(
        self,
        hash1: Tuple[int, int],
        hash2: Tuple[int, int]
    ) -> bool:
        """检查两个 hash 是否相似"""
        title_sim = self._hamming_distance(hash1[0], hash2[0])
        content_sim = self._hamming_distance(hash1[1], hash2[1])

        # 标题或内容相似即判定为相似
        return title_sim <= self.threshold or content_sim <= self.threshold

    def _hamming_distance(self, hash1: int, hash2: int) -> int:
        """计算两个 hash 的汉明距离"""
        xor = hash1 ^ hash2
        distance = 0
        while xor:
            distance += xor & 1
            xor >>= 1
        return distance

    def _find_news_by_hash(
        self,
        news_list: List[NewsItem],
        hash_key: Tuple[int, int]
    ) -> NewsItem:
        """根据 hash 查找新闻"""
        for news in news_list:
            if self._get_hash_key(news) == hash_key:
                return news
        return news_list[0]  # fallback

    def _get_hash_key(self, news: NewsItem) -> Tuple[int, int]:
        """获取新闻的 hash 键"""
        return (
            self._compute_title_hash(news.title),
            self._compute_content_hash(news.content)
        )

    def get_similar_news(
        self,
        news: NewsItem,
        news_list: List[NewsItem]
    ) -> List[NewsItem]:
        """获取与指定新闻相似的所有新闻"""
        target_hash = self._get_hash_key(news)
        similar_list = []

        for item in news_list:
            if self._is_similar(target_hash, self._get_hash_key(item)):
                similar_list.append(item)

        return similar_list
