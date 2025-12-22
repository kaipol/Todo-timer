"""
数据存储模块 - 持久化保存计时记录和应用使用时间
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict


class AppUsageRecord:
    """应用使用时间记录"""
    
    def __init__(self, app_name: str, exe_path: str, total_time: int,
                 app_type: str = 'normal', children: Optional[Dict] = None):
        self.app_name = app_name
        self.exe_path = exe_path
        self.total_time = total_time  # 秒数
        self.app_type = app_type
        self.children = children or {}  # 子窗口数据
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'app_name': self.app_name,
            'exe_path': self.exe_path,
            'total_time': self.total_time,
            'app_type': self.app_type,
            'children': self.children
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppUsageRecord':
        """从字典创建"""
        return cls(
            app_name=data['app_name'],
            exe_path=data['exe_path'],
            total_time=data['total_time'],
            app_type=data.get('app_type', 'normal'),
            children=data.get('children', {})
        )
    
    def format_time(self) -> str:
        """格式化时长"""
        hours = self.total_time // 3600
        minutes = (self.total_time % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


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


class TimerStorage:
    """计时记录存储管理"""
    
    def __init__(self):
        self.storage_dir = Path.home() / '.time_tracker'
        self.records_file = self.storage_dir / 'timer_records.json'
        self.records: List[TimerRecord] = []
        self._ensure_storage_dir()
        self.load()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True)
    
    def load(self):
        """加载记录"""
        if self.records_file.exists():
            try:
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [TimerRecord.from_dict(r) for r in data]
            except Exception as e:
                print(f"加载计时记录失败: {e}")
                self.records = []
    
    def save(self):
        """保存记录"""
        try:
            with open(self.records_file, 'w', encoding='utf-8') as f:
                data = [r.to_dict() for r in self.records]
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存计时记录失败: {e}")
    
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
        """获取周统计摘要"""
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        records = self.get_records_by_date_range(week_start, week_end)
        
        # 按日期分组统计
        daily_stats = defaultdict(lambda: {'duration': 0, 'count': 0})
        for r in records:
            date_key = r.timestamp.date()
            daily_stats[date_key]['duration'] += r.duration
            daily_stats[date_key]['count'] += 1
        
        # 计算统计数据
        total_duration = sum(r.duration for r in records)
        total_count = len(records)
        
        # 有记录的天数
        active_days = len(daily_stats)
        
        # 日均（基于有记录的天数）
        avg_daily_duration = total_duration // active_days if active_days > 0 else 0
        avg_daily_count = total_count // active_days if active_days > 0 else 0
        
        # 最长单日
        max_daily_duration = max((s['duration'] for s in daily_stats.values()), default=0)
        
        # 各类型统计
        pomodoro_count = len([r for r in records if r.mode == 'countdown'])
        stopwatch_count = len([r for r in records if r.mode == 'stopwatch'])
        pomodoro_duration = sum(r.duration for r in records if r.mode == 'countdown')
        stopwatch_duration = sum(r.duration for r in records if r.mode == 'stopwatch')
        
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


class AppUsageStorage:
    """应用使用时间存储管理"""
    
    def __init__(self):
        self.storage_dir = Path.home() / '.time_tracker'
        self.usage_dir = self.storage_dir / 'usage'
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True)
        if not self.usage_dir.exists():
            self.usage_dir.mkdir(parents=True)
    
    def _get_date_file(self, date) -> Path:
        """获取指定日期的存储文件路径"""
        return self.usage_dir / f"{date.strftime('%Y-%m-%d')}.json"
    
    def save_daily_usage(self, date, app_stats: Dict):
        """保存某日的应用使用数据"""
        file_path = self._get_date_file(date)
        
        # 转换为可序列化格式
        records = []
        for exe_path, info in app_stats.items():
            # 处理子窗口数据
            children_data = {}
            for key, child in info.get('children', {}).items():
                children_data[key] = {
                    'title': child.get('title', ''),
                    'total_time': int(child.get('total_time', 0)),
                    'domain': child.get('domain')
                }
            
            record = AppUsageRecord(
                app_name=info['name'],
                exe_path=exe_path,
                total_time=int(info['total_time']),
                app_type=info.get('app_type', 'normal'),
                children=children_data
            )
            records.append(record.to_dict())
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'date': date.isoformat(),
                    'records': records,
                    'saved_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存应用使用数据失败: {e}")
    
    def load_daily_usage(self, date) -> List[AppUsageRecord]:
        """加载某日的应用使用数据"""
        file_path = self._get_date_file(date)
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [AppUsageRecord.from_dict(r) for r in data.get('records', [])]
        except Exception as e:
            print(f"加载应用使用数据失败: {e}")
            return []
    
    def get_dates_with_usage(self) -> set:
        """获取有使用记录的日期集合"""
        dates = set()
        if self.usage_dir.exists():
            for file in self.usage_dir.glob('*.json'):
                try:
                    date_str = file.stem  # 文件名格式: YYYY-MM-DD
                    dates.add(datetime.strptime(date_str, '%Y-%m-%d').date())
                except ValueError:
                    pass
        return dates
    
    def get_daily_summary(self, date) -> dict:
        """获取单日使用摘要"""
        records = self.load_daily_usage(date)
        
        if not records:
            return {
                'total_time': 0,
                'app_count': 0,
                'top_apps': [],
                'records': []
            }
        
        total_time = sum(r.total_time for r in records)
        
        # 按使用时间排序
        sorted_records = sorted(records, key=lambda r: r.total_time, reverse=True)
        
        # 获取前5个应用
        top_apps = [
            {
                'name': r.app_name,
                'time': r.total_time,
                'time_str': r.format_time(),
                'app_type': r.app_type
            }
            for r in sorted_records[:5]
        ]
        
        return {
            'total_time': total_time,
            'app_count': len(records),
            'top_apps': top_apps,
            'records': sorted_records
        }
    
    def get_weekly_summary(self, week_start = None) -> dict:
        """获取周使用摘要"""
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        # 收集周内所有数据
        all_records = []
        daily_totals = {}
        active_days = 0
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            records = self.load_daily_usage(day)
            
            if records:
                active_days += 1
                day_total = sum(r.total_time for r in records)
                daily_totals[day] = {
                    'total_time': day_total,
                    'app_count': len(records)
                }
                all_records.extend(records)
        
        # 汇总应用使用时间
        app_totals = defaultdict(lambda: {'time': 0, 'name': '', 'app_type': 'normal'})
        for r in all_records:
            app_totals[r.exe_path]['time'] += r.total_time
            app_totals[r.exe_path]['name'] = r.app_name
            app_totals[r.exe_path]['app_type'] = r.app_type
        
        # 排序
        sorted_apps = sorted(app_totals.items(), key=lambda x: x[1]['time'], reverse=True)
        
        total_time = sum(info['time'] for _, info in sorted_apps)
        avg_daily = total_time // active_days if active_days > 0 else 0
        
        # 获取前10个应用
        top_apps = [
            {
                'name': info['name'],
                'time': info['time'],
                'time_str': self._format_time(info['time']),
                'app_type': info['app_type']
            }
            for _, info in sorted_apps[:10]
        ]
        
        return {
            'week_start': week_start,
            'week_end': week_end,
            'total_time': total_time,
            'active_days': active_days,
            'avg_daily_time': avg_daily,
            'daily_totals': daily_totals,
            'top_apps': top_apps
        }
    
    def _format_time(self, seconds: int) -> str:
        """格式化时间"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def delete_daily_usage(self, date) -> bool:
        """删除指定日期的应用使用数据"""
        file_path = self._get_date_file(date)
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                print(f"删除应用使用数据失败: {e}")
                return False
        return False


class MemoItem:
    """备忘录/待办事项数据类"""
    
    def __init__(self, content: str, completed: bool = False,
                 created_at: Optional[datetime] = None,
                 completed_at: Optional[datetime] = None,
                 priority: int = 0, category: str = "默认",
                 item_id: Optional[str] = None,
                 reminder_enabled: bool = False,
                 reminder_datetime: Optional[datetime] = None,
                 reminder_repeat: str = "none",  # none, daily, weekly, monthly
                 reminder_notified: bool = False):
        self.id = item_id or datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.content = content
        self.completed = completed
        self.created_at = created_at or datetime.now()
        self.completed_at = completed_at
        self.priority = priority  # 0: 普通, 1: 重要, 2: 紧急
        self.category = category
        # 提醒相关
        self.reminder_enabled = reminder_enabled
        self.reminder_datetime = reminder_datetime
        self.reminder_repeat = reminder_repeat
        self.reminder_notified = reminder_notified
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'completed': self.completed,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'priority': self.priority,
            'category': self.category,
            'reminder_enabled': self.reminder_enabled,
            'reminder_datetime': self.reminder_datetime.isoformat() if self.reminder_datetime else None,
            'reminder_repeat': self.reminder_repeat,
            'reminder_notified': self.reminder_notified
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MemoItem':
        """从字典创建"""
        return cls(
            item_id=data.get('id'),
            content=data['content'],
            completed=data.get('completed', False),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            priority=data.get('priority', 0),
            category=data.get('category', '默认'),
            reminder_enabled=data.get('reminder_enabled', False),
            reminder_datetime=datetime.fromisoformat(data['reminder_datetime']) if data.get('reminder_datetime') else None,
            reminder_repeat=data.get('reminder_repeat', 'none'),
            reminder_notified=data.get('reminder_notified', False)
        )
    
    def get_priority_icon(self) -> str:
        """获取优先级图标"""
        icons = {0: "📝", 1: "⭐", 2: "🔥"}
        return icons.get(self.priority, "📝")
    
    def get_priority_name(self) -> str:
        """获取优先级名称"""
        names = {0: "普通", 1: "重要", 2: "紧急"}
        return names.get(self.priority, "普通")
    
    def format_created_time(self) -> str:
        """格式化创建时间"""
        now = datetime.now()
        if self.created_at.date() == now.date():
            return f"今天 {self.created_at.strftime('%H:%M')}"
        elif self.created_at.date() == (now - timedelta(days=1)).date():
            return f"昨天 {self.created_at.strftime('%H:%M')}"
        else:
            return self.created_at.strftime('%m/%d %H:%M')
    
    def format_reminder_time(self) -> str:
        """格式化提醒时间"""
        if not self.reminder_enabled or not self.reminder_datetime:
            return ""
        
        now = datetime.now()
        rd = self.reminder_datetime
        
        # 周期性提醒标识
        repeat_icons = {
            'none': '',
            'daily': '🔄日',
            'weekly': '🔄周',
            'monthly': '🔄月'
        }
        repeat_str = repeat_icons.get(self.reminder_repeat, '')
        
        if rd.date() == now.date():
            time_str = f"今天 {rd.strftime('%H:%M')}"
        elif rd.date() == (now + timedelta(days=1)).date():
            time_str = f"明天 {rd.strftime('%H:%M')}"
        elif rd.date() == (now - timedelta(days=1)).date():
            time_str = f"昨天 {rd.strftime('%H:%M')}"
        else:
            time_str = rd.strftime('%m/%d %H:%M')
        
        return f"⏰{time_str} {repeat_str}".strip()
    
    def is_reminder_due(self) -> bool:
        """检查提醒是否到期"""
        if not self.reminder_enabled or not self.reminder_datetime:
            return False
        if self.completed:
            return False
        return datetime.now() >= self.reminder_datetime and not self.reminder_notified
    
    def get_next_reminder(self) -> Optional[datetime]:
        """获取下一次提醒时间（用于周期性提醒）"""
        if not self.reminder_enabled or not self.reminder_datetime:
            return None
        
        if self.reminder_repeat == 'none':
            return None
        
        now = datetime.now()
        next_time = self.reminder_datetime
        
        while next_time <= now:
            if self.reminder_repeat == 'daily':
                next_time += timedelta(days=1)
            elif self.reminder_repeat == 'weekly':
                next_time += timedelta(weeks=1)
            elif self.reminder_repeat == 'monthly':
                # 简单处理：加30天
                next_time += timedelta(days=30)
            else:
                return None
        
        return next_time


class MemoStorage:
    """备忘录存储管理"""
    
    def __init__(self):
        self.storage_dir = Path.home() / '.time_tracker'
        self.memo_file = self.storage_dir / 'memos.json'
        self.items: List[MemoItem] = []
        self.categories: List[str] = ["默认", "工作", "学习", "生活"]
        self._ensure_storage_dir()
        self.load()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True)
    
    def load(self):
        """加载备忘录"""
        if self.memo_file.exists():
            try:
                with open(self.memo_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = [MemoItem.from_dict(item) for item in data.get('items', [])]
                    self.categories = data.get('categories', ["默认", "工作", "学习", "生活"])
            except Exception as e:
                print(f"加载备忘录失败: {e}")
                self.items = []
    
    def save(self):
        """保存备忘录"""
        try:
            with open(self.memo_file, 'w', encoding='utf-8') as f:
                data = {
                    'items': [item.to_dict() for item in self.items],
                    'categories': self.categories,
                    'saved_at': datetime.now().isoformat()
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存备忘录失败: {e}")
    
    def add_item(self, content: str, priority: int = 0, category: str = "默认",
                 reminder_enabled: bool = False, reminder_datetime: Optional[datetime] = None,
                 reminder_repeat: str = "none") -> MemoItem:
        """添加备忘录项"""
        item = MemoItem(
            content=content,
            priority=priority,
            category=category,
            reminder_enabled=reminder_enabled,
            reminder_datetime=reminder_datetime,
            reminder_repeat=reminder_repeat
        )
        self.items.insert(0, item)  # 新项目添加到开头
        self.save()
        return item
    
    def update_item(self, item_id: str, content: str = None, priority: int = None,
                    category: str = None, completed: bool = None,
                    reminder_enabled: bool = None, reminder_datetime: datetime = None,
                    reminder_repeat: str = None) -> bool:
        """更新备忘录项"""
        for item in self.items:
            if item.id == item_id:
                if content is not None:
                    item.content = content
                if priority is not None:
                    item.priority = priority
                if category is not None:
                    item.category = category
                if completed is not None:
                    item.completed = completed
                    item.completed_at = datetime.now() if completed else None
                if reminder_enabled is not None:
                    item.reminder_enabled = reminder_enabled
                if reminder_datetime is not None:
                    item.reminder_datetime = reminder_datetime
                    item.reminder_notified = False  # 重置通知状态
                if reminder_repeat is not None:
                    item.reminder_repeat = reminder_repeat
                self.save()
                return True
        return False
    
    def delete_item(self, item_id: str) -> bool:
        """删除备忘录项"""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[i]
                self.save()
                return True
        return False
    
    def toggle_complete(self, item_id: str) -> bool:
        """切换完成状态"""
        for item in self.items:
            if item.id == item_id:
                item.completed = not item.completed
                item.completed_at = datetime.now() if item.completed else None
                self.save()
                return item.completed
        return False
    
    def get_all_items(self, include_completed: bool = True) -> List[MemoItem]:
        """获取所有备忘录项"""
        if include_completed:
            return self.items
        return [item for item in self.items if not item.completed]
    
    def get_items_by_category(self, category: str) -> List[MemoItem]:
        """按分类获取备忘录项"""
        return [item for item in self.items if item.category == category]
    
    def get_pending_items(self) -> List[MemoItem]:
        """获取未完成的备忘录项"""
        return [item for item in self.items if not item.completed]
    
    def get_completed_items(self) -> List[MemoItem]:
        """获取已完成的备忘录项"""
        return [item for item in self.items if item.completed]
    
    def get_today_items(self) -> List[MemoItem]:
        """获取今日创建的备忘录项"""
        today = datetime.now().date()
        return [item for item in self.items if item.created_at.date() == today]
    
    def add_category(self, category: str) -> bool:
        """添加分类"""
        if category not in self.categories:
            self.categories.append(category)
            self.save()
            return True
        return False
    
    def delete_category(self, category: str) -> bool:
        """删除分类（将该分类下的项目移到默认分类）"""
        if category in self.categories and category != "默认":
            for item in self.items:
                if item.category == category:
                    item.category = "默认"
            self.categories.remove(category)
            self.save()
            return True
        return False
    
    def clear_completed(self) -> int:
        """清除所有已完成的项目"""
        original_count = len(self.items)
        self.items = [item for item in self.items if not item.completed]
        deleted_count = original_count - len(self.items)
        if deleted_count > 0:
            self.save()
        return deleted_count
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        total = len(self.items)
        completed = len([item for item in self.items if item.completed])
        pending = total - completed
        
        # 按优先级统计
        priority_stats = {0: 0, 1: 0, 2: 0}
        for item in self.items:
            if not item.completed:
                priority_stats[item.priority] = priority_stats.get(item.priority, 0) + 1
        
        # 按分类统计
        category_stats = {}
        for item in self.items:
            if not item.completed:
                category_stats[item.category] = category_stats.get(item.category, 0) + 1
        
        # 有提醒的数量
        with_reminder = len([item for item in self.items if item.reminder_enabled and not item.completed])
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'priority_stats': priority_stats,
            'category_stats': category_stats,
            'with_reminder': with_reminder
        }
    
    def get_due_reminders(self) -> List[MemoItem]:
        """获取到期的提醒"""
        return [item for item in self.items if item.is_reminder_due()]
    
    def mark_reminder_notified(self, item_id: str) -> bool:
        """标记提醒已通知"""
        for item in self.items:
            if item.id == item_id:
                item.reminder_notified = True
                # 如果是周期性提醒，更新到下一次
                if item.reminder_repeat != 'none':
                    next_time = item.get_next_reminder()
                    if next_time:
                        item.reminder_datetime = next_time
                        item.reminder_notified = False
                self.save()
                return True
        return False
    
    def get_upcoming_reminders(self, hours: int = 24) -> List[MemoItem]:
        """获取即将到期的提醒（指定小时内）"""
        now = datetime.now()
        future = now + timedelta(hours=hours)
        upcoming = []
        for item in self.items:
            if (item.reminder_enabled and item.reminder_datetime and
                not item.completed and now <= item.reminder_datetime <= future):
                upcoming.append(item)
        return sorted(upcoming, key=lambda x: x.reminder_datetime)


# 全局存储实例
timer_storage = TimerStorage()
app_usage_storage = AppUsageStorage()
memo_storage = MemoStorage()