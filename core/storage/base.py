"""
基础存储类 - 提供通用的存储功能

性能优化:
- 添加内存缓存减少磁盘I/O
- 缓存文件修改时间以检测外部更改
- 支持批量操作
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class BaseStorage:
    """基础存储类，提供通用的存储功能
    
    性能优化特性:
    - 内存缓存: 减少重复的磁盘读取
    - 缓存失效: 基于文件修改时间自动失效
    - 延迟写入: 可选的批量保存模式
    """
    
    # 类级别的缓存配置
    _CACHE_TTL = 5.0  # 缓存有效期（秒）
    
    def __init__(self, storage_dir_name: str = '.time_tracker'):
        """
        初始化基础存储
        
        Args:
            storage_dir_name: 存储目录名称
        """
        self.storage_dir = Path.home() / storage_dir_name
        self._ensure_storage_dir()
        
        # 内存缓存: {file_path_str: {'data': data, 'mtime': mtime, 'cached_at': time}}
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True)
    
    def _is_cache_valid(self, file_path: Path) -> bool:
        """检查缓存是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            缓存是否有效
        """
        cache_key = str(file_path)
        if cache_key not in self._cache:
            return False
        
        cache_entry = self._cache[cache_key]
        
        # 检查缓存是否过期
        if time.time() - cache_entry['cached_at'] > self._CACHE_TTL:
            return False
        
        # 检查文件是否被外部修改
        if file_path.exists():
            current_mtime = file_path.stat().st_mtime
            if current_mtime != cache_entry['mtime']:
                return False
        
        return True
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """
        保存数据到JSON文件并更新缓存
        
        Args:
            file_path: 文件路径
            data: 要保存的数据
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 更新缓存
            cache_key = str(file_path)
            self._cache[cache_key] = {
                'data': data,
                'mtime': file_path.stat().st_mtime,
                'cached_at': time.time()
            }
        except Exception as e:
            print(f"保存文件失败 {file_path}: {e}")
    
    def _load_json(self, file_path: Path, use_cache: bool = True) -> Dict[str, Any]:
        """
        从JSON文件加载数据（带缓存）
        
        Args:
            file_path: 文件路径
            use_cache: 是否使用缓存（默认True）
            
        Returns:
            加载的数据字典
        """
        cache_key = str(file_path)
        
        # 检查缓存
        if use_cache and self._is_cache_valid(file_path):
            return self._cache[cache_key]['data']
        
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新缓存
            self._cache[cache_key] = {
                'data': data,
                'mtime': file_path.stat().st_mtime,
                'cached_at': time.time()
            }
            
            return data
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return {}
    
    def _invalidate_cache(self, file_path: Optional[Path] = None):
        """使缓存失效
        
        Args:
            file_path: 指定文件路径，如果为None则清除所有缓存
        """
        if file_path is None:
            self._cache.clear()
        else:
            cache_key = str(file_path)
            if cache_key in self._cache:
                del self._cache[cache_key]
    
    def _get_date_file(self, date: datetime.date, subdir: str = None, 
                       suffix: str = '.json') -> Path:
        """
        获取指定日期的存储文件路径
        
        Args:
            date: 日期
            subdir: 子目录名
            suffix: 文件后缀
            
        Returns:
            文件路径
        """
        if subdir:
            dir_path = self.storage_dir / subdir
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
            return dir_path / f"{date.strftime('%Y-%m-%d')}{suffix}"
        return self.storage_dir / f"{date.strftime('%Y-%m-%d')}{suffix}"