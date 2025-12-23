"""
存储模块 - 分割后的存储组件
"""

from .base import BaseStorage
from .timer_storage import TimerRecord, TimerStorage
from .usage_storage import AppUsageRecord, AppUsageStorage
from .memo_storage import MemoItem, MemoStorage
from .diary_storage import DiaryEntry, DiaryStorage

# 导出全局实例
from .timer_storage import timer_storage
from .usage_storage import app_usage_storage
from .memo_storage import memo_storage
from .diary_storage import diary_storage

__all__ = [
    'BaseStorage',
    'TimerRecord', 'TimerStorage', 'timer_storage',
    'AppUsageRecord', 'AppUsageStorage', 'app_usage_storage',
    'MemoItem', 'MemoStorage', 'memo_storage',
    'DiaryEntry', 'DiaryStorage', 'diary_storage'
]