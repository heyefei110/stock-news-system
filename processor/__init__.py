"""
Processor package
"""
from processor.cleaner import NewsCleaner
from processor.dedup import NewsDeduplicator
from processor.summarizer import NewsSummarizer

__all__ = [
    "NewsCleaner",
    "NewsDeduplicator",
    "NewsSummarizer"
]
