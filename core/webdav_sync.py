"""
WebDAV 同步模块 - 支持双向同步、冲突处理和定时同步
电脑端和手机端统一使用ZIP格式进行数据同步
"""
import os
import json
import zipfile
import tempfile
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Callable
import urllib.request
import urllib.error
from urllib.parse import urljoin
import base64
import ssl
import hashlib


class WebDAVSync:
    """WebDAV同步管理类 - 支持双向同步和冲突处理"""
    
    # 同步文件名（统一格式，手机端和电脑端共用）
    SYNC_FILENAME = 'timetracker_sync.zip'
    SYNC_META_FILENAME = 'sync_meta.json'
    
    def __init__(self):
        self.storage_dir = Path.home() / '.time_tracker'
        self.config_file = self.storage_dir / 'webdav_config.json'
        self.local_meta_file = self.storage_dir / 'local_sync_meta.json'
        self.config = self._load_config()
        
        # 需要同步的文件和目录
        self.sync_items = [
            'timer_records.json',  # 计时记录
            'memos.json',          # 备忘录/待办
            'config.json',         # 配置
            'usage',               # 应用使用记录目录
            'diary',               # 日记目录
        ]
        
        # 同步状态
        self._sync_timer = None
        self._sync_lock = threading.Lock()
        self._is_syncing = False
        self._sync_callbacks: List[Callable] = []
        
        # 设备标识
        self._device_id = self._get_device_id()
    
    def _get_device_id(self) -> str:
        """获取设备唯一标识"""
        device_file = self.storage_dir / '.device_id'
        if device_file.exists():
            return device_file.read_text().strip()
        
        # 生成新的设备ID
        import uuid
        device_id = f"desktop_{uuid.uuid4().hex[:8]}"
        device_file.parent.mkdir(parents=True, exist_ok=True)
        device_file.write_text(device_id)
        return device_id
    
    def _load_config(self) -> dict:
        """加载WebDAV配置"""
        default_config = {
            'enabled': False,
            'server_url': '',
            'username': '',
            'password': '',
            'remote_path': '/TimeTracker/',
            'auto_sync': True,           # 默认启用自动同步
            'sync_interval': 30,         # 自动同步间隔（秒）
            'last_sync': None,
            'last_sync_status': None,
            'conflict_strategy': 'merge', # merge, local_first, remote_first
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    for key in default_config:
                        if key in saved_config:
                            default_config[key] = saved_config[key]
            except Exception as e:
                print(f"加载WebDAV配置失败: {e}")
        
        return default_config
    
    def save_config(self):
        """保存WebDAV配置"""
        try:
            if not self.storage_dir.exists():
                self.storage_dir.mkdir(parents=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存WebDAV配置失败: {e}")
    
    def get_config(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value):
        """设置配置项"""
        self.config[key] = value
        self.save_config()
    
    def update_config(self, **kwargs):
        """批量更新配置"""
        for key, value in kwargs.items():
            self.config[key] = value
        self.save_config()
    
    def is_configured(self) -> bool:
        """检查是否已配置WebDAV"""
        return bool(
            self.config.get('enabled') and
            self.config.get('server_url') and
            self.config.get('username')
        )
    
    def add_sync_callback(self, callback: Callable):
        """添加同步完成回调"""
        self._sync_callbacks.append(callback)
    
    def remove_sync_callback(self, callback: Callable):
        """移除同步完成回调"""
        if callback in self._sync_callbacks:
            self._sync_callbacks.remove(callback)
    
    def _notify_sync_complete(self, success: bool, message: str):
        """通知同步完成"""
        for callback in self._sync_callbacks:
            try:
                callback(success, message)
            except Exception as e:
                print(f"同步回调执行失败: {e}")
    
    # ==================== WebDAV 请求方法 ====================
    
    def _webdav_request(self, method: str, url: str, data: bytes = None,
                        headers: dict = None, redirect_count: int = 0) -> Tuple[bool, str, Optional[bytes]]:
        """
        发送WebDAV请求
        返回: (成功标志, 消息, 响应数据)
        """
        try:
            if redirect_count > 5:
                return False, "重定向次数过多", None
            
            auth_string = f"{self.config['username']}:{self.config['password']}"
            auth_bytes = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            
            req_headers = {
                'Authorization': f'Basic {auth_bytes}',
                'User-Agent': 'TimeTracker/1.0',
            }
            if headers:
                req_headers.update(headers)
            
            request = urllib.request.Request(
                url,
                data=data,
                headers=req_headers,
                method=method
            )
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(request, context=ssl_context, timeout=30) as response:
                response_data = response.read()
                return True, f"请求成功 ({response.status})", response_data
                
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                location = e.headers.get('Location')
                if location:
                    new_url = urljoin(url, location)
                    return self._webdav_request(method, new_url, data=data, headers=headers, redirect_count=redirect_count + 1)
            return False, f"HTTP错误: {e.code} {e.reason}", None
        except urllib.error.URLError as e:
            return False, f"连接错误: {str(e.reason)}", None
        except Exception as e:
            return False, f"请求失败: {str(e)}", None
    
    def _ensure_remote_directory(self) -> Tuple[bool, str]:
        """确保远程目录存在"""
        server_url = self.config['server_url'].rstrip('/')
        remote_path = self.config['remote_path'].strip('/')
        
        url = f"{server_url}/{remote_path}/"
        success, msg, _ = self._webdav_request('MKCOL', url)
        
        if success or '405' in msg or '301' in msg:
            return True, "目录就绪"
        
        return False, msg
    
    def test_connection(self) -> Tuple[bool, str]:
        """测试WebDAV连接"""
        if not self.config.get('server_url'):
            return False, "未配置服务器地址"
        
        server_url = self.config['server_url'].rstrip('/')
        
        success, msg, _ = self._webdav_request('PROPFIND', server_url, headers={'Depth': '0'})
        
        if success:
            return True, "连接成功"
        else:
            return False, msg
    
    # ==================== 本地元数据管理 ====================
    
    def _load_local_meta(self) -> dict:
        """加载本地同步元数据"""
        default_meta = {
            'last_sync_time': None,
            'last_sync_hash': None,
            'device_id': self._device_id,
            'records_modified': {},  # 记录每条数据的修改时间
        }
        
        if self.local_meta_file.exists():
            try:
                with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return default_meta
    
    def _save_local_meta(self, meta: dict):
        """保存本地同步元数据"""
        try:
            with open(self.local_meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存本地元数据失败: {e}")
    
    def _calculate_data_hash(self) -> str:
        """计算本地数据的哈希值"""
        hash_content = ""
        for item in self.sync_items:
            item_path = self.storage_dir / item
            if item_path.is_file():
                hash_content += item_path.read_text(encoding='utf-8')
            elif item_path.is_dir():
                for root, dirs, files in os.walk(item_path):
                    for file in sorted(files):
                        file_path = Path(root) / file
                        try:
                            hash_content += file_path.read_text(encoding='utf-8')
                        except:
                            pass
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    # ==================== ZIP 打包和解包 ====================
    
    def _create_sync_zip(self) -> Tuple[bool, str, Optional[str]]:
        """
        创建同步ZIP文件（统一格式，手机端和电脑端共用）
        返回: (成功标志, 消息, ZIP文件路径)
        """
        try:
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, self.SYNC_FILENAME)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in self.sync_items:
                    item_path = self.storage_dir / item
                    
                    if item_path.is_file():
                        zipf.write(item_path, item)
                    elif item_path.is_dir():
                        for root, dirs, files in os.walk(item_path):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = os.path.join(item, os.path.relpath(file_path, item_path))
                                zipf.write(file_path, arcname)
                
                # 添加同步元数据
                sync_meta = {
                    'sync_time': datetime.now().isoformat(),
                    'device_id': self._device_id,
                    'device_type': 'desktop',
                    'data_hash': self._calculate_data_hash(),
                    'version': '2.0',
                }
                zipf.writestr(self.SYNC_META_FILENAME, json.dumps(sync_meta, indent=2, ensure_ascii=False))
            
            return True, "ZIP创建成功", zip_path
            
        except Exception as e:
            return False, f"创建ZIP失败: {str(e)}", None
    
    def _extract_sync_zip(self, zip_path: str) -> Tuple[bool, str, Optional[dict]]:
        """
        解压同步ZIP文件并返回元数据
        返回: (成功标志, 消息, 元数据)
        """
        try:
            temp_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 读取元数据
            meta_path = os.path.join(temp_dir, self.SYNC_META_FILENAME)
            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            
            return True, "解压成功", {'temp_dir': temp_dir, 'meta': meta}
            
        except Exception as e:
            return False, f"解压ZIP失败: {str(e)}", None
    
    # ==================== 数据合并方法 ====================
    
    def _merge_json_data(self, local_data: dict, remote_data: dict, data_type: str) -> dict:
        """
        合并JSON数据（基于ID和时间戳）
        data_type: 'memos', 'timer_records', 'diary'
        """
        if data_type == 'memos':
            return self._merge_memos(local_data, remote_data)
        elif data_type == 'timer_records':
            return self._merge_timer_records(local_data, remote_data)
        elif data_type == 'diary':
            return self._merge_diary(local_data, remote_data)
        else:
            # 默认使用本地数据
            return local_data
    
    def _merge_memos(self, local_data: dict, remote_data: dict) -> dict:
        """合并备忘录数据"""
        local_items = local_data.get('items', [])
        remote_items = remote_data.get('items', [])
        
        # 创建ID到项目的映射
        merged = {}
        
        # 先添加本地数据
        for item in local_items:
            item_id = item.get('id')
            if item_id:
                merged[item_id] = item
        
        # 合并远程数据（基于更新时间）
        for item in remote_items:
            item_id = item.get('id')
            if not item_id:
                continue
            
            if item_id not in merged:
                merged[item_id] = item
            else:
                # 比较更新时间，保留较新的
                local_time = merged[item_id].get('updated_at', '')
                remote_time = item.get('updated_at', '')
                if remote_time > local_time:
                    merged[item_id] = item
        
        # 合并分类
        local_categories = set(local_data.get('categories', []))
        remote_categories = set(remote_data.get('categories', []))
        merged_categories = list(local_categories | remote_categories)
        
        return {
            'items': list(merged.values()),
            'categories': merged_categories,
            'saved_at': datetime.now().isoformat()
        }
    
    def _merge_timer_records(self, local_data: list, remote_data: list) -> list:
        """合并计时记录"""
        if isinstance(local_data, dict):
            local_data = local_data.get('records', [])
        if isinstance(remote_data, dict):
            remote_data = remote_data.get('records', [])
        
        merged = {}
        
        # 先添加本地数据
        for record in local_data:
            record_id = record.get('id') or f"{record.get('start_time', '')}_{record.get('note', '')}"
            merged[record_id] = record
        
        # 合并远程数据
        for record in remote_data:
            record_id = record.get('id') or f"{record.get('start_time', '')}_{record.get('note', '')}"
            if record_id not in merged:
                merged[record_id] = record
        
        return list(merged.values())
    
    def _merge_diary(self, local_data: dict, remote_data: dict) -> dict:
        """合并日记数据"""
        local_entries = local_data.get('entries', [])
        remote_entries = remote_data.get('entries', [])
        
        merged = {}
        
        # 先添加本地数据
        for entry in local_entries:
            entry_id = entry.get('id')
            if entry_id:
                merged[entry_id] = entry
        
        # 合并远程数据（基于更新时间）
        for entry in remote_entries:
            entry_id = entry.get('id')
            if not entry_id:
                continue
            
            if entry_id not in merged:
                merged[entry_id] = entry
            else:
                local_time = merged[entry_id].get('updated_at', '')
                remote_time = entry.get('updated_at', '')
                if remote_time > local_time:
                    merged[entry_id] = entry
        
        # 合并标签
        local_tags = set(local_data.get('tags', []))
        remote_tags = set(remote_data.get('tags', []))
        merged_tags = list(local_tags | remote_tags)
        
        return {
            'entries': list(merged.values()),
            'tags': merged_tags,
            'saved_at': datetime.now().isoformat()
        }
    
    # ==================== 数据合并方法 ====================
    
    def _merge_json_data(self, local_data: dict, remote_data: dict, data_type: str) -> dict:
        """
        合并JSON数据（按ID合并，保留最新的记录）
        data_type: 'memos', 'timer_records', 'diary'
        """
        if data_type == 'memos':
            # memos.json 格式: { items: [...], categories: [...] }
            local_items = local_data.get('items', []) if isinstance(local_data, dict) else local_data
            remote_items = remote_data.get('items', []) if isinstance(remote_data, dict) else remote_data
            
            merged = self._merge_by_id(local_items, remote_items)
            
            # 合并分类
            local_cats = local_data.get('categories', []) if isinstance(local_data, dict) else []
            remote_cats = remote_data.get('categories', []) if isinstance(remote_data, dict) else []
            merged_cats = list(set(local_cats + remote_cats))
            
            return {'items': merged, 'categories': merged_cats, 'saved_at': datetime.now().isoformat()}
        
        elif data_type == 'timer_records':
            # timer_records.json 格式: 直接数组 [...]
            local_items = local_data if isinstance(local_data, list) else []
            remote_items = remote_data if isinstance(remote_data, list) else []
            return self._merge_by_id(local_items, remote_items)
        
        elif data_type == 'diary':
            # diary 格式: { entries: [...], tags: [...] }
            local_entries = local_data.get('entries', []) if isinstance(local_data, dict) else local_data
            remote_entries = remote_data.get('entries', []) if isinstance(remote_data, dict) else remote_data
            
            merged = self._merge_by_id(local_entries, remote_entries)
            
            # 合并标签
            local_tags = local_data.get('tags', []) if isinstance(local_data, dict) else []
            remote_tags = remote_data.get('tags', []) if isinstance(remote_data, dict) else []
            merged_tags = list(set(local_tags + remote_tags))
            
            return {'entries': merged, 'tags': merged_tags, 'saved_at': datetime.now().isoformat()}
        
        return local_data
    
    def _merge_by_id(self, local_items: list, remote_items: list) -> list:
        """按ID合并两个列表，保留最新的记录"""
        merged = {}
        
        # 先添加本地数据
        for item in local_items:
            if isinstance(item, dict):
                item_id = item.get('id') or item.get('date') or str(hash(json.dumps(item, sort_keys=True)))
                merged[item_id] = item
        
        # 合并远程数据（如果更新时间更新则覆盖）
        for item in remote_items:
            if isinstance(item, dict):
                item_id = item.get('id') or item.get('date') or str(hash(json.dumps(item, sort_keys=True)))
                
                if item_id in merged:
                    # 比较更新时间
                    local_time = merged[item_id].get('updated_at') or merged[item_id].get('created_at') or ''
                    remote_time = item.get('updated_at') or item.get('created_at') or ''
                    
                    if remote_time > local_time:
                        merged[item_id] = item
                else:
                    merged[item_id] = item
        
        return list(merged.values())
    
    def _apply_remote_data(self, temp_dir: str) -> Tuple[bool, str]:
        """将远程数据应用到本地（根据冲突策略）"""
        strategy = self.config.get('conflict_strategy', 'merge')
        
        try:
            for item in self.sync_items:
                remote_path = os.path.join(temp_dir, item)
                local_path = self.storage_dir / item
                
                if os.path.isfile(remote_path):
                    if strategy == 'remote_first' or not local_path.exists():
                        # 直接使用远程数据
                        shutil.copy2(remote_path, local_path)
                    elif strategy == 'merge':
                        # 合并数据
                        with open(remote_path, 'r', encoding='utf-8') as f:
                            remote_data = json.load(f)
                        with open(local_path, 'r', encoding='utf-8') as f:
                            local_data = json.load(f)
                        
                        # 根据文件类型合并
                        if 'memos' in item:
                            merged = self._merge_json_data(local_data, remote_data, 'memos')
                        elif 'timer' in item:
                            merged = self._merge_json_data(local_data, remote_data, 'timer_records')
                        elif 'diary' in item:
                            merged = self._merge_json_data(local_data, remote_data, 'diary')
                        else:
                            merged = remote_data  # 其他文件直接使用远程
                        
                        with open(local_path, 'w', encoding='utf-8') as f:
                            json.dump(merged, f, indent=2, ensure_ascii=False)
                    # local_first 策略不做任何操作
                
                elif os.path.isdir(remote_path):
                    if strategy == 'remote_first':
                        if local_path.exists():
                            shutil.rmtree(local_path)
                        shutil.copytree(remote_path, local_path)
                    elif strategy == 'merge':
                        # 合并目录中的文件
                        if not local_path.exists():
                            local_path.mkdir(parents=True)
                        
                        for root, dirs, files in os.walk(remote_path):
                            rel_root = os.path.relpath(root, remote_path)
                            local_root = local_path / rel_root if rel_root != '.' else local_path
                            
                            for d in dirs:
                                (local_root / d).mkdir(exist_ok=True)
                            
                            for f in files:
                                remote_file = Path(root) / f
                                local_file = local_root / f
                                
                                if f.endswith('.json') and local_file.exists():
                                    # 合并JSON文件
                                    try:
                                        with open(remote_file, 'r', encoding='utf-8') as rf:
                                            remote_data = json.load(rf)
                                        with open(local_file, 'r', encoding='utf-8') as lf:
                                            local_data = json.load(lf)
                                        
                                        if 'diary' in str(local_file):
                                            merged = self._merge_json_data(local_data, remote_data, 'diary')
                                        else:
                                            merged = remote_data
                                        
                                        with open(local_file, 'w', encoding='utf-8') as wf:
                                            json.dump(merged, wf, indent=2, ensure_ascii=False)
                                    except:
                                        shutil.copy2(remote_file, local_file)
                                else:
                                    shutil.copy2(remote_file, local_file)
            
            return True, "数据合并成功"
        except Exception as e:
            return False, f"应用远程数据失败: {str(e)}"
    
    # ==================== 数据合并方法 ====================
    
    def _merge_json_arrays(self, local_data: list, remote_data: list, id_field: str = 'id') -> list:
        """
        合并两个JSON数组，基于ID字段去重，保留最新的记录
        """
        merged = {}
        
        # 先添加本地数据
        for item in local_data:
            item_id = item.get(id_field)
            if item_id:
                merged[item_id] = item
        
        # 合并远程数据，根据时间戳决定保留哪个
        for item in remote_data:
            item_id = item.get(id_field)
            if item_id:
                if item_id in merged:
                    # 比较更新时间
                    local_time = merged[item_id].get('updated_at') or merged[item_id].get('created_at') or ''
                    remote_time = item.get('updated_at') or item.get('created_at') or ''
                    if remote_time > local_time:
                        merged[item_id] = item
                else:
                    merged[item_id] = item
        
        return list(merged.values())
    
    def _merge_data(self, local_dir: str, remote_dir: str, strategy: str = 'merge') -> Tuple[bool, str]:
        """
        合并本地和远程数据
        strategy: merge(合并), local_first(本地优先), remote_first(远程优先)
        """
        try:
            if strategy == 'local_first':
                # 本地优先，不做任何操作
                return True, "使用本地数据"
            
            if strategy == 'remote_first':
                # 远程优先，直接复制远程数据到本地
                for item in self.sync_items:
                    remote_path = os.path.join(remote_dir, item)
                    local_path = self.storage_dir / item
                    
                    if os.path.exists(remote_path):
                        if os.path.isfile(remote_path):
                            shutil.copy2(remote_path, local_path)
                        elif os.path.isdir(remote_path):
                            if local_path.exists():
                                shutil.rmtree(local_path)
                            shutil.copytree(remote_path, local_path)
                
                return True, "使用远程数据"
            
            # 合并策略
            for item in self.sync_items:
                remote_path = os.path.join(remote_dir, item)
                local_path = self.storage_dir / item
                
                if not os.path.exists(remote_path):
                    continue
                
                if item.endswith('.json') and os.path.isfile(remote_path):
                    # JSON文件合并
                    try:
                        with open(remote_path, 'r', encoding='utf-8') as f:
                            remote_data = json.load(f)
                        
                        local_data = {}
                        if local_path.exists():
                            with open(local_path, 'r', encoding='utf-8') as f:
                                local_data = json.load(f)
                        
                        # 根据数据类型进行合并
                        if isinstance(remote_data, list) and isinstance(local_data, list):
                            merged = self._merge_json_arrays(local_data, remote_data)
                        elif isinstance(remote_data, dict) and isinstance(local_data, dict):
                            # 对于字典类型，检查是否有items或entries字段
                            if 'items' in remote_data or 'items' in local_data:
                                local_items = local_data.get('items', [])
                                remote_items = remote_data.get('items', [])
                                merged_items = self._merge_json_arrays(local_items, remote_items)
                                merged = {**local_data, **remote_data, 'items': merged_items}
                            elif 'entries' in remote_data or 'entries' in local_data:
                                local_entries = local_data.get('entries', [])
                                remote_entries = remote_data.get('entries', [])
                                merged_entries = self._merge_json_arrays(local_entries, remote_entries)
                                merged = {**local_data, **remote_data, 'entries': merged_entries}
                            else:
                                # 普通字典，远程覆盖本地
                                merged = {**local_data, **remote_data}
                        else:
                            merged = remote_data
                        
                        with open(local_path, 'w', encoding='utf-8') as f:
                            json.dump(merged, f, indent=2, ensure_ascii=False)
                    
                    except Exception as e:
                        print(f"合并 {item} 失败: {e}")
                
                elif os.path.isdir(remote_path):
                    # 目录合并（如diary目录）
                    if not local_path.exists():
                        local_path.mkdir(parents=True)
                    
                    for root, dirs, files in os.walk(remote_path):
                        rel_root = os.path.relpath(root, remote_path)
                        local_root = local_path / rel_root if rel_root != '.' else local_path
                        
                        if not local_root.exists():
                            local_root.mkdir(parents=True)
                        
                        for file in files:
                            remote_file = os.path.join(root, file)
                            local_file = local_root / file
                            
                            if file.endswith('.json'):
                                # JSON文件合并
                                try:
                                    with open(remote_file, 'r', encoding='utf-8') as f:
                                        remote_content = json.load(f)
                                    
                                    if local_file.exists():
                                        with open(local_file, 'r', encoding='utf-8') as f:
                                            local_content = json.load(f)
                                        
                                        if isinstance(remote_content, list) and isinstance(local_content, list):
                                            merged = self._merge_json_arrays(local_content, remote_content)
                                        else:
                                            # 比较时间戳
                                            remote_time = os.path.getmtime(remote_file)
                                            local_time = os.path.getmtime(local_file)
                                            merged = remote_content if remote_time > local_time else local_content
                                    else:
                                        merged = remote_content
                                    
                                    with open(local_file, 'w', encoding='utf-8') as f:
                                        json.dump(merged, f, indent=2, ensure_ascii=False)
                                except:
                                    shutil.copy2(remote_file, local_file)
                            else:
                                # 非JSON文件，比较时间戳
                                if not local_file.exists():
                                    shutil.copy2(remote_file, local_file)
                                else:
                                    remote_time = os.path.getmtime(remote_file)
                                    local_time = os.path.getmtime(local_file)
                                    if remote_time > local_time:
                                        shutil.copy2(remote_file, local_file)
            
            return True, "数据合并完成"
            
        except Exception as e:
            return False, f"合并数据失败: {str(e)}"
    
    # ==================== 上传和下载方法 ====================
    
    def upload_backup(self) -> Tuple[bool, str]:
        """上传备份到WebDAV服务器"""
        if not self.is_configured():
            return False, "WebDAV未配置"
        
        with self._sync_lock:
            if self._is_syncing:
                return False, "同步正在进行中"
            self._is_syncing = True
        
        try:
            # 确保远程目录存在
            success, msg = self._ensure_remote_directory()
            if not success:
                return False, f"创建远程目录失败: {msg}"
            
            # 创建ZIP文件
            success, msg, zip_path = self._create_sync_zip()
            if not success:
                return False, msg
            
            try:
                # 上传ZIP文件
                server_url = self.config['server_url'].rstrip('/')
                remote_path = self.config['remote_path'].strip('/')
                url = f"{server_url}/{remote_path}/{self.SYNC_FILENAME}"
                
                with open(zip_path, 'rb') as f:
                    zip_data = f.read()
                
                success, msg, _ = self._webdav_request(
                    'PUT', url, data=zip_data,
                    headers={'Content-Type': 'application/zip'}
                )
                
                if success:
                    # 更新本地元数据
                    meta = self._load_local_meta()
                    meta['last_sync_time'] = datetime.now().isoformat()
                    meta['last_sync_hash'] = self._calculate_data_hash()
                    self._save_local_meta(meta)
                    
                    # 更新配置
                    self.config['last_sync'] = datetime.now().isoformat()
                    self.config['last_sync_status'] = 'success'
                    self.save_config()
                    
                    return True, "备份上传成功"
                else:
                    return False, f"上传失败: {msg}"
            
            finally:
                # 清理临时文件
                if zip_path and os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                        os.rmdir(os.path.dirname(zip_path))
                    except:
                        pass
        
        except Exception as e:
            return False, f"上传备份失败: {str(e)}"
        
        finally:
            self._is_syncing = False
    
    def download_backup(self, filename: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        从WebDAV服务器下载备份
        返回: (成功标志, 消息, 本地文件路径)
        """
        if not self.is_configured():
            return False, "WebDAV未配置", None
        
        try:
            server_url = self.config['server_url'].rstrip('/')
            remote_path = self.config['remote_path'].strip('/')
            target_file = filename or self.SYNC_FILENAME
            url = f"{server_url}/{remote_path}/{target_file}"
            
            success, msg, data = self._webdav_request('GET', url)
            
            if not success:
                return False, f"下载失败: {msg}", None
            
            # 保存到临时文件
            temp_dir = tempfile.mkdtemp()
            local_path = os.path.join(temp_dir, target_file)
            
            with open(local_path, 'wb') as f:
                f.write(data)
            
            return True, "下载成功", local_path
            
        except Exception as e:
            return False, f"下载备份失败: {str(e)}", None
    
    def restore_from_backup(self, backup_path: str) -> Tuple[bool, str]:
        """从备份文件恢复数据"""
        try:
            success, msg, result = self._extract_sync_zip(backup_path)
            if not success:
                return False, msg
            
            temp_dir = result['temp_dir']
            
            # 复制文件到存储目录
            for item in self.sync_items:
                src_path = os.path.join(temp_dir, item)
                dst_path = self.storage_dir / item
                
                if os.path.exists(src_path):
                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dst_path)
                    elif os.path.isdir(src_path):
                        if dst_path.exists():
                            shutil.rmtree(dst_path)
                        shutil.copytree(src_path, dst_path)
            
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return True, "数据恢复成功"
            
        except Exception as e:
            return False, f"恢复失败: {str(e)}"
    
    def list_remote_backups(self) -> Tuple[bool, str, List[dict]]:
        """列出远程备份文件"""
        if not self.is_configured():
            return False, "WebDAV未配置", []
        
        try:
            server_url = self.config['server_url'].rstrip('/')
            remote_path = self.config['remote_path'].strip('/')
            url = f"{server_url}/{remote_path}/"
            
            success, msg, data = self._webdav_request('PROPFIND', url, headers={'Depth': '1'})
            
            if not success:
                return False, f"获取列表失败: {msg}", []
            
            # 解析响应（简单解析，查找.zip文件）
            backups = []
            if data:
                content = data.decode('utf-8', errors='ignore')
                # 简单查找zip文件名
                import re
                zip_files = re.findall(r'<d:href>.*?([^/]+\.zip)</d:href>', content, re.IGNORECASE)
                if not zip_files:
                    zip_files = re.findall(r'<D:href>.*?([^/]+\.zip)</D:href>', content, re.IGNORECASE)
                
                for filename in zip_files:
                    backups.append({
                        'filename': filename,
                        'display_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return True, "获取成功", backups
            
        except Exception as e:
            return False, f"列出备份失败: {str(e)}", []
    
    # ==================== 双向同步方法 ====================
    
    def bidirectional_sync(self) -> Tuple[bool, str]:
        """
        执行双向同步：
        1. 下载远程数据
        2. 与本地数据合并
        3. 上传合并后的数据
        """
        if not self.is_configured():
            return False, "WebDAV未配置"
        
        with self._sync_lock:
            if self._is_syncing:
                return False, "同步正在进行中"
            self._is_syncing = True
        
        try:
            # 1. 下载远程数据
            success, msg, remote_zip_path = self.download_backup()
            
            if success and remote_zip_path:
                # 2. 解压远程数据
                success, msg, result = self._extract_sync_zip(remote_zip_path)
                
                if success:
                    temp_dir = result['temp_dir']
                    remote_meta = result.get('meta', {})
                    
                    # 检查是否需要合并
                    local_hash = self._calculate_data_hash()
                    remote_hash = remote_meta.get('data_hash', '')
                    
                    if local_hash != remote_hash:
                        # 3. 合并数据
                        strategy = self.config.get('conflict_strategy', 'merge')
                        success, msg = self._merge_data(str(self.storage_dir), temp_dir, strategy)
                        
                        if not success:
                            return False, f"合并数据失败: {msg}"
                    
                    # 清理临时目录
                    shutil.rmtree(temp_dir, ignore_errors=True)
                
                # 清理下载的ZIP文件
                if remote_zip_path and os.path.exists(remote_zip_path):
                    try:
                        os.remove(remote_zip_path)
                        os.rmdir(os.path.dirname(remote_zip_path))
                    except:
                        pass
            
            # 4. 上传合并后的数据
            self._is_syncing = False  # 临时解锁以允许上传
            success, msg = self.upload_backup()
            
            if success:
                self._notify_sync_complete(True, "双向同步完成")
                return True, "双向同步完成"
            else:
                self._notify_sync_complete(False, msg)
                return False, f"上传失败: {msg}"
        
        except Exception as e:
            self._notify_sync_complete(False, str(e))
            return False, f"双向同步失败: {str(e)}"
        
        finally:
            self._is_syncing = False
    
    # ==================== 自动同步方法 ====================
    
    def start_auto_sync(self):
        """启动自动同步定时器"""
        if not self.is_configured():
            print("WebDAV未配置，无法启动自动同步")
            return
        
        if not self.config.get('auto_sync', True):
            print("自动同步已禁用")
            return
        
        # 停止现有定时器
        self.stop_auto_sync()
        
        interval = self.config.get('sync_interval', 30)
        
        def sync_loop():
            while self._sync_timer is not None:
                try:
                    if self.is_configured() and not self._is_syncing:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 执行自动同步...")
                        success, msg = self.bidirectional_sync()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 同步结果: {msg}")
                except Exception as e:
                    print(f"自动同步出错: {e}")
                
                # 等待指定间隔
                for _ in range(interval):
                    if self._sync_timer is None:
                        return
                    time.sleep(1)
        
        self._sync_timer = threading.Thread(target=sync_loop, daemon=True)
        self._sync_timer.start()
        print(f"自动同步已启动，间隔 {interval} 秒")
    
    def stop_auto_sync(self):
        """停止自动同步定时器"""
        if self._sync_timer is not None:
            timer = self._sync_timer
            self._sync_timer = None
            # 等待线程结束
            if timer.is_alive():
                timer.join(timeout=2)
            print("自动同步已停止")
    
    def is_auto_sync_running(self) -> bool:
        """检查自动同步是否正在运行"""
        return self._sync_timer is not None and self._sync_timer.is_alive()


# 创建全局实例
webdav_sync = WebDAVSync()
