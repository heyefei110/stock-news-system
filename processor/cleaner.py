"""
数据清洗模块
"""
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger
from collectors.base import NewsItem
import re


class NewsCleaner:
    """新闻数据清洗器"""

    # 需要去除的无用词汇
    NOISE_WORDS = [
        "点击查看全文", "查看更多", "展开全文", "收起",
        "广告", "推广", " Sponsored", "广告链接",
        "阅读本文前，请您先关注", "欢迎点击关注",
        "投资有风险，入市需谨慎",
        "本文来源", "图片来源",
        "免责声明", "风险提示",
    ]

    # HTML 标签正则
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

    # 多余空白正则
    WHITESPACE_PATTERN = re.compile(r'\s+')

    # URL 正则
    URL_PATTERN = re.compile(r'http[s]?://\S+')

    def clean(self, news_list: List[NewsItem]) -> List[NewsItem]:
        """
        清洗新闻数据

        Args:
            news_list: 原始新闻列表

        Returns:
            清洗后的新闻列表
        """
        cleaned_list = []

        for news in news_list:
            try:
                cleaned_news = self._clean_single_news(news)
                if cleaned_news and self._is_valid_news(cleaned_news):
                    cleaned_list.append(cleaned_news)
            except Exception as e:
                logger.warning(f"清洗新闻失败：{e}")
                continue

        logger.info(f"数据清洗完成，原始：{len(news_list)}, 清洗后：{len(cleaned_list)}")
        return cleaned_list

    def _clean_single_news(self, news: NewsItem) -> Optional[NewsItem]:
        """清洗单条新闻"""
        # 清洗标题
        title = self._clean_title(news.title)
        if not title:
            return None

        # 清洗内容
        content = self._clean_content(news.content)

        # 创建新的 NewsItem
        return NewsItem(
            stock_name=news.stock_name,
            title=title,
            content=content,
            source=news.source,
            url=news.url,
            publish_time=news.publish_time,
            image_url=news.image_url
        )

    def _clean_title(self, title: str) -> str:
        """清洗标题"""
        if not title:
            return ""

        # 去除 HTML 标签
        title = self.HTML_TAG_PATTERN.sub('', title)

        # 去除多余空白
        title = self.WHITESPACE_PATTERN.sub(' ', title).strip()

        # 去除噪声词汇
        for noise in self.NOISE_WORDS:
            title = title.replace(noise, '')

        # 去除首尾特殊字符
        title = title.strip('[]()【】""''-_:;,.!? \t\n\r')

        # 限制标题长度
        if len(title) > 200:
            title = title[:200]

        return title

    def _clean_content(self, content: str) -> str:
        """清洗内容"""
        if not content:
            return ""

        # 去除 HTML 标签
        content = self.HTML_TAG_PATTERN.sub('', content)

        # 解码 HTML 实体
        content = self._decode_html_entities(content)

        # 去除 URL (保留第一个作为来源链接)
        content = self.URL_PATTERN.sub('', content)

        # 去除噪声词汇
        for noise in self.NOISE_WORDS:
            content = content.replace(noise, '')

        # 去除多余空白
        content = self.WHITESPACE_PATTERN.sub(' ', content).strip()

        # 去除首尾特殊字符
        content = content.strip('[]()【】""''-_:;,.!? \t\n\r')

        # 限制内容长度
        if len(content) > 2000:
            content = content[:2000]

        return content

    def _decode_html_entities(self, text: str) -> str:
        """解码 HTML 实体"""
        entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
            '&mdash;': '—',
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&lsquo;': ''',
            '&rsquo;': ''',
        }

        for entity, char in entities.items():
            text = text.replace(entity, char)

        return text

    def _is_valid_news(self, news: NewsItem) -> bool:
        """验证新闻是否有效"""
        # 标题不能为空
        if not news.title or len(news.title) < 5:
            return False

        # 标题不能全是特殊字符
        if re.match(r'^[^\w一-龥]+$', news.title):
            return False

        # 排除广告嫌疑
        ad_keywords = ['广告', '推广', '赞助', '合作', '招商', '招聘']
        for keyword in ad_keywords:
            if keyword in news.title or keyword in news.content:
                return False

        return True

    def filter_by_date(
        self,
        news_list: List[NewsItem],
        days: int = 2
    ) -> List[NewsItem]:
        """
        按日期过滤新闻

        Args:
            news_list: 新闻列表
            days: 保留最近 N 天的新闻

        Returns:
            过滤后的新闻列表
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_list = []

        for news in news_list:
            if news.publish_time and news.publish_time >= cutoff_date:
                filtered_list.append(news)

        logger.info(f"日期过滤完成，保留：{len(filtered_list)} 条")
        return filtered_list

    def filter_by_keywords(
        self,
        news_list: List[NewsItem],
        keywords: List[str]
    ) -> List[NewsItem]:
        """
        按关键词过滤新闻

        Args:
            news_list: 新闻列表
            keywords: 关键词列表

        Returns:
            包含关键词的新闻列表
        """
        filtered_list = []

        for news in news_list:
            # 检查标题或内容是否包含关键词
            for keyword in keywords:
                if keyword in news.title or keyword in news.content:
                    filtered_list.append(news)
                    break

        logger.info(f"关键词过滤完成，保留：{len(filtered_list)} 条")
        return filtered_list
