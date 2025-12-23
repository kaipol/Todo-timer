"""
日记存储模块 - 管理日记条目
"""
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from collections import defaultdict

from .base import BaseStorage


class DiaryEntry:
    """日记条目数据类"""
    
    def __init__(self, title: str, content: str,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 entry_id: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 mood: str = "neutral",
                 weather: str = "",
                 images: Optional[List[str]] = None):
        self.id = entry_id or datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.title = title
        self.content = content  # Markdown格式内容
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.tags = tags or []
        self.mood = mood  # happy, neutral, sad, excited, tired
        self.weather = weather
        self.images = images or []  # 图片路径列表
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'mood': self.mood,
            'weather': self.weather,
            'images': self.images
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DiaryEntry':
        """从字典创建"""
        return cls(
            entry_id=data.get('id'),
            title=data['title'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            tags=data.get('tags', []),
            mood=data.get('mood', 'neutral'),
            weather=data.get('weather', ''),
            images=data.get('images', [])
        )
    
    def get_mood_icon(self) -> str:
        """获取心情图标"""
        icons = {
            'happy': '😊',
            'neutral': '😐',
            'sad': '😢',
            'excited': '🤩',
            'tired': '😴',
            'angry': '😠',
            'love': '🥰'
        }
        return icons.get(self.mood, '😐')
    
    def get_preview(self, max_length: int = 100) -> str:
        """获取内容预览（去除Markdown标记）"""
        # 简单去除常见Markdown标记
        text = self.content
        # 去除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 去除粗体/斜体
        text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
        text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
        # 去除链接
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # 去除图片
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        # 去除代码块
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 去除多余空白
        text = ' '.join(text.split())
        
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text
    
    def format_date(self) -> str:
        """格式化日期"""
        now = datetime.now()
        if self.created_at.date() == now.date():
            return f"今天 {self.created_at.strftime('%H:%M')}"
        elif self.created_at.date() == (now - timedelta(days=1)).date():
            return f"昨天 {self.created_at.strftime('%H:%M')}"
        else:
            return self.created_at.strftime('%Y/%m/%d %H:%M')


class DiaryStorage(BaseStorage):
    """日记存储管理"""
    
    def __init__(self):
        # 先设置存储目录和缓存（不调用父类的 _ensure_storage_dir）
        self.storage_dir = Path.home() / '.time_tracker'
        self._cache = {}  # 初始化缓存
        
        # 设置子目录
        self.diary_dir = self.storage_dir / 'diary'
        self.index_file = self.diary_dir / 'index.json'
        self.images_dir = self.diary_dir / 'images'
        self.entries: List[DiaryEntry] = []
        self.tags: List[str] = ["日常", "工作", "学习", "生活", "旅行", "读书", "电影", "美食"]
        self._ensure_storage_dir()
        self.load()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True)
        if not self.diary_dir.exists():
            self.diary_dir.mkdir(parents=True)
        if not self.images_dir.exists():
            self.images_dir.mkdir(parents=True)
    
    def load(self):
        """加载日记索引"""
        data = self._load_json(self.index_file)
        if data:
            try:
                self.entries = [DiaryEntry.from_dict(entry) for entry in data.get('entries', [])]
                self.tags = data.get('tags', self.tags)
            except Exception as e:
                print(f"加载日记索引失败: {e}")
                self.entries = []
    
    def save(self):
        """保存日记索引"""
        data = {
            'entries': [entry.to_dict() for entry in self.entries],
            'tags': self.tags,
            'saved_at': datetime.now().isoformat()
        }
        self._save_json(self.index_file, data)
    
    def add_entry(self, title: str, content: str, tags: List[str] = None,
                  mood: str = "neutral", weather: str = "", images: List[str] = None) -> DiaryEntry:
        """添加日记条目"""
        entry = DiaryEntry(
            title=title,
            content=content,
            tags=tags or [],
            mood=mood,
            weather=weather,
            images=images or []
        )
        self.entries.insert(0, entry)  # 新条目添加到开头
        self.save()
        return entry
    
    def update_entry(self, entry_id: str, title: str = None, content: str = None,
                     tags: List[str] = None, mood: str = None, weather: str = None,
                     images: List[str] = None) -> bool:
        """更新日记条目"""
        for entry in self.entries:
            if entry.id == entry_id:
                if title is not None:
                    entry.title = title
                if content is not None:
                    entry.content = content
                if tags is not None:
                    entry.tags = tags
                if mood is not None:
                    entry.mood = mood
                if weather is not None:
                    entry.weather = weather
                if images is not None:
                    entry.images = images
                entry.updated_at = datetime.now()
                self.save()
                return True
        return False
    
    def delete_entry(self, entry_id: str) -> bool:
        """删除日记条目"""
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                del self.entries[i]
                self.save()
                return True
        return False
    
    def get_entry(self, entry_id: str) -> Optional[DiaryEntry]:
        """获取单个日记条目"""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def get_all_entries(self) -> List[DiaryEntry]:
        """获取所有日记条目"""
        return self.entries
    
    def get_entries_by_date(self, date) -> List[DiaryEntry]:
        """获取指定日期的日记"""
        return [entry for entry in self.entries if entry.created_at.date() == date]
    
    def get_entries_by_date_range(self, start_date, end_date) -> List[DiaryEntry]:
        """获取日期范围内的日记"""
        return [entry for entry in self.entries
                if start_date <= entry.created_at.date() <= end_date]
    
    def get_entries_by_tag(self, tag: str) -> List[DiaryEntry]:
        """按标签获取日记"""
        return [entry for entry in self.entries if tag in entry.tags]
    
    def get_entries_by_mood(self, mood: str) -> List[DiaryEntry]:
        """按心情获取日记"""
        return [entry for entry in self.entries if entry.mood == mood]
    
    def search_entries(self, keyword: str) -> List[DiaryEntry]:
        """搜索日记（标题和内容）"""
        keyword = keyword.lower()
        return [entry for entry in self.entries
                if keyword in entry.title.lower() or keyword in entry.content.lower()]
    
    def get_dates_with_entries(self) -> set:
        """获取有日记的日期集合"""
        return {entry.created_at.date() for entry in self.entries}
    
    def add_tag(self, tag: str) -> bool:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save()
            return True
        return False
    
    def delete_tag(self, tag: str) -> bool:
        """删除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
            # 从所有日记中移除该标签
            for entry in self.entries:
                if tag in entry.tags:
                    entry.tags.remove(tag)
            self.save()
            return True
        return False
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        total = len(self.entries)
        
        # 按月统计
        monthly_stats = defaultdict(int)
        for entry in self.entries:
            month_key = entry.created_at.strftime('%Y-%m')
            monthly_stats[month_key] += 1
        
        # 按心情统计
        mood_stats = defaultdict(int)
        for entry in self.entries:
            mood_stats[entry.mood] += 1
        
        # 按标签统计
        tag_stats = defaultdict(int)
        for entry in self.entries:
            for tag in entry.tags:
                tag_stats[tag] += 1
        
        # 连续写日记天数
        dates = sorted(self.get_dates_with_entries(), reverse=True)
        streak = 0
        if dates:
            today = datetime.now().date()
            current = today
            for date in dates:
                if date == current:
                    streak += 1
                    current -= timedelta(days=1)
                elif date < current:
                    break
        
        return {
            'total': total,
            'monthly_stats': dict(monthly_stats),
            'mood_stats': dict(mood_stats),
            'tag_stats': dict(tag_stats),
            'streak': streak
        }
    
    def save_image(self, image_path: str) -> str:
        """保存图片到日记图片目录，返回新路径"""
        src = Path(image_path)
        if not src.exists():
            return ""
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        new_name = f"{timestamp}_{src.name}"
        dest = self.images_dir / new_name
        
        try:
            shutil.copy2(src, dest)
            return str(dest)
        except Exception as e:
            print(f"保存图片失败: {e}")
            return ""


# 全局实例
diary_storage = DiaryStorage()