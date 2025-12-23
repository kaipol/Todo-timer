"""
备忘录存储模块 - 管理备忘录和待办事项
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from .base import BaseStorage


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


class MemoStorage(BaseStorage):
    """备忘录存储管理"""
    
    def __init__(self):
        super().__init__()
        self.memo_file = self.storage_dir / 'memos.json'
        self.items: List[MemoItem] = []
        self.categories: List[str] = ["默认", "工作", "学习", "生活"]
        self.load()
    
    def load(self):
        """加载备忘录"""
        data = self._load_json(self.memo_file)
        if data:
            try:
                self.items = [MemoItem.from_dict(item) for item in data.get('items', [])]
                self.categories = data.get('categories', ["默认", "工作", "学习", "生活"])
            except Exception as e:
                print(f"加载备忘录失败: {e}")
                self.items = []
    
    def save(self):
        """保存备忘录"""
        data = {
            'items': [item.to_dict() for item in self.items],
            'categories': self.categories,
            'saved_at': datetime.now().isoformat()
        }
        self._save_json(self.memo_file, data)
    
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


# 全局实例
memo_storage = MemoStorage()