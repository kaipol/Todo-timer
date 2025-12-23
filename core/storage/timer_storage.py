"""
计时器存储模块 - 管理计时记录
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from .base import BaseStorage


class TimerRecord:
    """计时记录数据类"""
    
    def __init__(self, mode: str, duration: int, note: str, 
                 timestamp: Optional[datetime] = None, completed: bool = True):
        self.mode = mode  # 'countdown' or 'stopwatch'
        self.duration = duration  # 秒数
        self.note = note
        self.timestamp = timestamp or datetime.now()
        self.completed = completed  # 是否完成（倒计时是否到0）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'mode': self.mode,
            'duration': self.duration,
            'note': self.note,
            'timestamp': self.timestamp.isoformat(),
            'completed': self.completed
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TimerRecord':
        """从字典创建"""
        return cls(
            mode=data['mode'],
            duration=data['duration'],
            note=data['note'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            completed=data.get('completed', True)
        )
    
    def format_duration(self) -> str:
        """格式化时长"""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def format_time(self) -> str:
        """格式化时间戳"""
        return self.timestamp.strftime("%H:%M")
    
    def get_mode_icon(self) -> str:
        """获取模式图标"""
        return "🍅" if self.mode == 'countdown' else "⏱"


class TimerStorage(BaseStorage):
    """计时记录存储管理"""
    
    def __init__(self):
        super().__init__()
        self.records_file = self.storage_dir / 'timer_records.json'
        self.records: List[TimerRecord] = []
        self.load()
    
    def load(self):
        """加载记录"""
        data = self._load_json(self.records_file)
        if data:
            try:
                self.records = [TimerRecord.from_dict(r) for r in data]
            except Exception as e:
                print(f"加载计时记录失败: {e}")
                self.records = []
    
    def save(self):
        """保存记录"""
        data = [r.to_dict() for r in self.records]
        self._save_json(self.records_file, data)
    
    def add_record(self, record: TimerRecord):
        """添加记录"""
        self.records.append(record)
        self.save()
    
    def get_records_by_date(self, date: datetime.date) -> List[TimerRecord]:
        """获取指定日期的记录"""
        return [r for r in self.records if r.timestamp.date() == date]
    
    def get_records_by_date_range(self, start_date: datetime.date, 
                                   end_date: datetime.date) -> List[TimerRecord]:
        """获取日期范围内的记录"""
        return [r for r in self.records 
                if start_date <= r.timestamp.date() <= end_date]
    
    def get_today_records(self) -> List[TimerRecord]:
        """获取今日记录"""
        return self.get_records_by_date(datetime.now().date())
    
    def get_week_records(self, week_start: Optional[datetime.date] = None) -> List[TimerRecord]:
        """获取指定周的记录（默认本周）"""
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return self.get_records_by_date_range(week_start, week_end)
    
    def get_dates_with_records(self) -> set:
        """获取有记录的日期集合"""
        return {r.timestamp.date() for r in self.records}
    
    def get_daily_summary(self, date: datetime.date) -> dict:
        """获取单日统计摘要"""
        records = self.get_records_by_date(date)
        if not records:
            return {
                'total_duration': 0,
                'count': 0,
                'pomodoro_count': 0,
                'stopwatch_count': 0,
                'avg_duration': 0
            }
        
        total_duration = sum(r.duration for r in records)
        pomodoro_count = len([r for r in records if r.mode == 'countdown'])
        stopwatch_count = len([r for r in records if r.mode == 'stopwatch'])
        
        return {
            'total_duration': total_duration,
            'count': len(records),
            'pomodoro_count': pomodoro_count,
            'stopwatch_count': stopwatch_count,
            'avg_duration': total_duration // len(records) if records else 0
        }
    
    def get_weekly_summary(self, week_start: Optional[datetime.date] = None) -> dict:
        """获取周统计摘要
        
        性能优化: 使用单次遍历计算所有统计数据，避免多次遍历记录列表
        """
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        records = self.get_records_by_date_range(week_start, week_end)
        
        # 使用单次遍历计算所有统计数据
        daily_stats = defaultdict(lambda: {'duration': 0, 'count': 0})
        total_duration = 0
        total_count = len(records)
        pomodoro_count = 0
        stopwatch_count = 0
        pomodoro_duration = 0
        stopwatch_duration = 0
        
        for r in records:
            # 按日期分组
            date_key = r.timestamp.date()
            daily_stats[date_key]['duration'] += r.duration
            daily_stats[date_key]['count'] += 1
            
            # 累计总时长
            total_duration += r.duration
            
            # 按类型统计
            if r.mode == 'countdown':
                pomodoro_count += 1
                pomodoro_duration += r.duration
            else:
                stopwatch_count += 1
                stopwatch_duration += r.duration
        
        # 有记录的天数
        active_days = len(daily_stats)
        
        # 日均（基于有记录的天数）
        avg_daily_duration = total_duration // active_days if active_days > 0 else 0
        avg_daily_count = total_count // active_days if active_days > 0 else 0
        
        # 最长单日
        max_daily_duration = max((s['duration'] for s in daily_stats.values()), default=0)
        
        return {
            'week_start': week_start,
            'week_end': week_end,
            'total_duration': total_duration,
            'total_count': total_count,
            'active_days': active_days,
            'avg_daily_duration': avg_daily_duration,
            'avg_daily_count': avg_daily_count,
            'max_daily_duration': max_daily_duration,
            'pomodoro_count': pomodoro_count,
            'stopwatch_count': stopwatch_count,
            'pomodoro_duration': pomodoro_duration,
            'stopwatch_duration': stopwatch_duration,
            'daily_stats': dict(daily_stats)
        }
    
    def delete_record(self, index: int):
        """删除指定索引的记录"""
        if 0 <= index < len(self.records):
            del self.records[index]
            self.save()
    
    def delete_records_by_date(self, date) -> int:
        """删除指定日期的所有记录，返回删除的数量"""
        original_count = len(self.records)
        self.records = [r for r in self.records if r.timestamp.date() != date]
        deleted_count = original_count - len(self.records)
        if deleted_count > 0:
            self.save()
        return deleted_count
    
    def clear_all(self):
        """清除所有记录"""
        self.records = []
        self.save()


# 全局实例
timer_storage = TimerStorage()