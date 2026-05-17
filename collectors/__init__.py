# Collectors package - 数据采集器
from collectors.base import BaseCollector, NewsItem
from collectors.sina import SinaCollector
from collectors.eastmoney import EastmoneyCollector
from collectors.xueqiu import XueqiuCollector
from collectors.tencent import TencentCollector
from collectors.simple import SimpleFinanceCollector, StockPriceCollector

__all__ = [
    "BaseCollector",
    "NewsItem",
    "SinaCollector",
    "EastmoneyCollector",
    "XueqiuCollector",
    "TencentCollector",
    "SimpleFinanceCollector",
    "StockPriceCollector",
]
