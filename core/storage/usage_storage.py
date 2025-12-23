"""
应用使用时间存储模块 - 管理应用使用记录
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from .base import BaseStorage


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


class AppUsageStorage(BaseStorage):
    """应用使用时间存储管理"""
    
    def __init__(self):
        # 先设置存储目录和缓存（不调用父类的 _ensure_storage_dir）
        self.storage_dir = Path.home() / '.time_tracker'
        self._cache = {}  # 初始化缓存
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
        
        data = {
            'date': date.isoformat(),
            'records': records,
            'saved_at': datetime.now().isoformat()
        }
        self._save_json(file_path, data)
    
    def load_daily_usage(self, date) -> List[AppUsageRecord]:
        """加载某日的应用使用数据"""
        file_path = self._get_date_file(date)
        
        if not file_path.exists():
            return []
        
        data = self._load_json(file_path)
        if not data:
            return []
        
        try:
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
        """获取周使用摘要
        
        性能优化: 使用批量加载和内存缓存，避免重复读取文件
        """
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        # 批量收集周内所有数据（利用基类的缓存机制）
        all_records = []
        daily_totals = {}
        active_days = 0
        
        # 预先计算所有日期，减少循环中的计算
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        
        for day in week_days:
            records = self.load_daily_usage(day)
            
            if records:
                active_days += 1
                # 使用生成器表达式计算总时间，避免创建中间列表
                day_total = sum(r.total_time for r in records)
                daily_totals[day] = {
                    'total_time': day_total,
                    'app_count': len(records)
                }
                all_records.extend(records)
        
        # 使用单次遍历汇总应用使用时间
        app_totals = defaultdict(lambda: {'time': 0, 'name': '', 'app_type': 'normal'})
        total_time = 0
        for r in all_records:
            app_totals[r.exe_path]['time'] += r.total_time
            app_totals[r.exe_path]['name'] = r.app_name
            app_totals[r.exe_path]['app_type'] = r.app_type
            total_time += r.total_time
        
        # 排序
        sorted_apps = sorted(app_totals.items(), key=lambda x: x[1]['time'], reverse=True)
        
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


# 全局实例
app_usage_storage = AppUsageStorage()