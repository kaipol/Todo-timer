"""
WebDAV 同步模块 - 将数据打包为ZIP并同步到WebDAV服务器
"""
import os
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import urllib.error
import base64
import ssl


class WebDAVSync:
    """WebDAV同步管理类"""
    
    def __init__(self):
        self.storage_dir = Path.home() / '.time_tracker'
        self.config_file = self.storage_dir / 'webdav_config.json'
        self.config = self._load_config()
        
        # 需要同步的文件和目录
        self.sync_items = [
            'timer_records.json',  # 计时记录
            'memos.json',          # 备忘录/待办
            'config.json',         # 配置
            'usage',               # 应用使用记录目录
            'diary',               # 日记目录
        ]
    
    def _load_config(self) -> dict:
        """加载WebDAV配置"""
        default_config = {
            'enabled': False,
            'server_url': '',      # WebDAV服务器地址
            'username': '',
            'password': '',
            'remote_path': '/TimeTracker/',  # 远程存储路径
            'auto_sync': False,    # 是否自动同步
            'sync_interval': 30,   # 自动同步间隔（分钟）
            'last_sync': None,     # 上次同步时间
            'last_sync_status': None,  # 上次同步状态
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
    
    def _create_backup_zip(self) -> Tuple[bool, str, Optional[str]]:
        """
        创建数据备份ZIP文件
        返回: (成功标志, 消息, ZIP文件路径)
        """
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f'timetracker_backup_{timestamp}.zip'
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in self.sync_items:
                    item_path = self.storage_dir / item
                    
                    if item_path.is_file():
                        # 单个文件
                        zipf.write(item_path, item)
                    elif item_path.is_dir():
                        # 目录 - 递归添加
                        for root, dirs, files in os.walk(item_path):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = os.path.join(
                                    item,
                                    os.path.relpath(file_path, item_path)
                                )
                                zipf.write(file_path, arcname)
                
                # 添加元数据
                metadata = {
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'items': self.sync_items
                }
                zipf.writestr('_metadata.json', json.dumps(metadata, indent=2))
            
            return True, "备份创建成功", zip_path
            
        except Exception as e:
            return False, f"创建备份失败: {str(e)}", None
    
    def _webdav_request(self, method: str, url: str, data: bytes = None,
                        headers: dict = None) -> Tuple[bool, str, Optional[bytes]]:
        """
        发送WebDAV请求
        返回: (成功标志, 消息, 响应数据)
        """
        try:
            # 构建认证头
            auth_string = f"{self.config['username']}:{self.config['password']}"
            auth_bytes = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            
            req_headers = {
                'Authorization': f'Basic {auth_bytes}',
                'User-Agent': 'TimeTracker/1.0',
            }
            if headers:
                req_headers.update(headers)
            
            # 创建请求
            request = urllib.request.Request(
                url,
                data=data,
                headers=req_headers,
                method=method
            )
            
            # 创建SSL上下文（允许自签名证书）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 发送请求
            with urllib.request.urlopen(request, context=ssl_context, timeout=30) as response:
                response_data = response.read()
                return True, f"请求成功 ({response.status})", response_data
                
        except urllib.error.HTTPError as e:
            return False, f"HTTP错误: {e.code} {e.reason}", None
        except urllib.error.URLError as e:
            return False, f"连接错误: {str(e.reason)}", None
        except Exception as e:
            return False, f"请求失败: {str(e)}", None
    
    def _ensure_remote_directory(self) -> Tuple[bool, str]:
        """确保远程目录存在"""
        server_url = self.config['server_url'].rstrip('/')
        remote_path = self.config['remote_path'].strip('/')
        
        # 尝试创建目录（MKCOL）
        url = f"{server_url}/{remote_path}/"
        success, msg, _ = self._webdav_request('MKCOL', url)
        
        # 如果目录已存在，MKCOL会返回405，这是正常的
        if success or '405' in msg or '301' in msg:
            return True, "目录就绪"
        
        return False, msg
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        测试WebDAV连接
        返回: (成功标志, 消息)
        """
        if not self.config.get('server_url'):
            return False, "未配置服务器地址"
        
        server_url = self.config['server_url'].rstrip('/')
        
        # 使用PROPFIND测试连接
        success, msg, _ = self._webdav_request(
            'PROPFIND',
            server_url,
            headers={'Depth': '0'}
        )
        
        if success:
            return True, "连接成功"
        else:
            return False, msg
    
    def upload_backup(self) -> Tuple[bool, str]:
        """
        上传备份到WebDAV
        返回: (成功标志, 消息)
        """
        if not self.is_configured():
            return False, "WebDAV未配置"
        
        # 创建备份ZIP
        success, msg, zip_path = self._create_backup_zip()
        if not success:
            return False, msg
        
        try:
            # 确保远程目录存在
            success, msg = self._ensure_remote_directory()
            if not success:
                return False, f"创建远程目录失败: {msg}"
            
            # 读取ZIP文件
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            
            # 构建上传URL
            server_url = self.config['server_url'].rstrip('/')
            remote_path = self.config['remote_path'].strip('/')
            zip_filename = os.path.basename(zip_path)
            upload_url = f"{server_url}/{remote_path}/{zip_filename}"
            
            # 上传文件
            success, msg, _ = self._webdav_request(
                'PUT',
                upload_url,
                data=zip_data,
                headers={'Content-Type': 'application/zip'}
            )
            
            if success:
                # 更新同步状态
                self.config['last_sync'] = datetime.now().isoformat()
                self.config['last_sync_status'] = 'success'
                self.save_config()
                
                # 清理旧备份（保留最近5个）
                self._cleanup_old_backups()
                
                return True, f"同步成功: {zip_filename}"
            else:
                self.config['last_sync_status'] = 'failed'
                self.save_config()
                return False, f"上传失败: {msg}"
                
        finally:
            # 清理临时文件
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                    os.rmdir(os.path.dirname(zip_path))
                except:
                    pass
    
    def _cleanup_old_backups(self, keep_count: int = 5):
        """清理旧备份，保留最近的N个"""
        try:
            server_url = self.config['server_url'].rstrip('/')
            remote_path = self.config['remote_path'].strip('/')
            list_url = f"{server_url}/{remote_path}/"
            
            # 获取目录列表
            success, msg, data = self._webdav_request(
                'PROPFIND',
                list_url,
                headers={'Depth': '1'}
            )
            
            if not success or not data:
                return
            
            # 解析响应获取文件列表（简单解析）
            content = data.decode('utf-8', errors='ignore')
            
            # 查找所有备份文件
            import re
            backup_files = re.findall(
                r'timetracker_backup_(\d{8}_\d{6})\.zip',
                content
            )
            
            if len(backup_files) <= keep_count:
                return
            
            # 按时间排序，删除旧的
            backup_files.sort(reverse=True)
            files_to_delete = backup_files[keep_count:]
            
            for timestamp in files_to_delete:
                filename = f'timetracker_backup_{timestamp}.zip'
                delete_url = f"{server_url}/{remote_path}/{filename}"
                self._webdav_request('DELETE', delete_url)
                
        except Exception as e:
            print(f"清理旧备份失败: {e}")
    
    def list_remote_backups(self) -> Tuple[bool, str, list]:
        """
        列出远程备份文件
        返回: (成功标志, 消息, 文件列表)
        """
        if not self.is_configured():
            return False, "WebDAV未配置", []
        
        try:
            server_url = self.config['server_url'].rstrip('/')
            remote_path = self.config['remote_path'].strip('/')
            list_url = f"{server_url}/{remote_path}/"
            
            success, msg, data = self._webdav_request(
                'PROPFIND',
                list_url,
                headers={'Depth': '1'}
            )
            
            if not success:
                return False, msg, []
            
            if not data:
                return True, "目录为空", []
            
            # 解析响应
            content = data.decode('utf-8', errors='ignore')
            
            import re
            backups = []
            matches = re.findall(
                r'timetracker_backup_(\d{8}_\d{6})\.zip',
                content
            )
            
            for timestamp in matches:
                try:
                    dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                    backups.append({
                        'filename': f'timetracker_backup_{timestamp}.zip',
                        'timestamp': timestamp,
                        'datetime': dt,
                        'display_time': dt.strftime('%Y-%m-%d %H:%M:%S')
                    })
                except:
                    pass
            
            # 按时间排序
            backups.sort(key=lambda x: x['datetime'], reverse=True)
            
            return True, f"找到 {len(backups)} 个备份", backups
            
        except Exception as e:
            return False, f"获取备份列表失败: {str(e)}", []
    
    def download_backup(self, filename: str) -> Tuple[bool, str, Optional[str]]:
        """
        下载指定的备份文件
        返回: (成功标志, 消息, 本地文件路径)
        """
        if not self.is_configured():
            return False, "WebDAV未配置", None
        
        try:
            server_url = self.config['server_url'].rstrip('/')
            remote_path = self.config['remote_path'].strip('/')
            download_url = f"{server_url}/{remote_path}/{filename}"
            
            success, msg, data = self._webdav_request('GET', download_url)
            
            if not success or not data:
                return False, f"下载失败: {msg}", None
            
            # 保存到临时文件
            temp_dir = tempfile.mkdtemp()
            local_path = os.path.join(temp_dir, filename)
            
            with open(local_path, 'wb') as f:
                f.write(data)
            
            return True, "下载成功", local_path
            
        except Exception as e:
            return False, f"下载失败: {str(e)}", None
    
    def restore_from_backup(self, zip_path: str, 
                           restore_items: list = None) -> Tuple[bool, str]:
        """
        从备份ZIP恢复数据
        参数:
            zip_path: ZIP文件路径
            restore_items: 要恢复的项目列表，None表示全部恢复
        返回: (成功标志, 消息)
        """
        if not os.path.exists(zip_path):
            return False, "备份文件不存在"
        
        try:
            # 创建备份目录（以防恢复失败）
            backup_dir = self.storage_dir / '_restore_backup'
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            backup_dir.mkdir(parents=True)
            
            # 备份当前数据
            for item in self.sync_items:
                item_path = self.storage_dir / item
                if item_path.exists():
                    if item_path.is_file():
                        shutil.copy2(item_path, backup_dir / item)
                    else:
                        shutil.copytree(item_path, backup_dir / item)
            
            # 解压恢复
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # 获取要恢复的项目
                items_to_restore = restore_items or self.sync_items
                
                for item in items_to_restore:
                    # 查找ZIP中匹配的文件
                    matching_files = [
                        name for name in zipf.namelist()
                        if name == item or name.startswith(item + '/')
                    ]
                    
                    if not matching_files:
                        continue
                    
                    # 删除现有项目
                    item_path = self.storage_dir / item
                    if item_path.exists():
                        if item_path.is_file():
                            item_path.unlink()
                        else:
                            shutil.rmtree(item_path)
                    
                    # 解压
                    for file_name in matching_files:
                        if file_name.startswith('_'):  # 跳过元数据
                            continue
                        zipf.extract(file_name, self.storage_dir)
            
            # 清理备份目录
            shutil.rmtree(backup_dir)
            
            return True, "恢复成功，请重启应用以加载新数据"
            
        except Exception as e:
            # 尝试恢复原数据
            try:
                if backup_dir.exists():
                    for item in self.sync_items:
                        backup_item = backup_dir / item
                        if backup_item.exists():
                            target = self.storage_dir / item
                            if target.exists():
                                if target.is_file():
                                    target.unlink()
                                else:
                                    shutil.rmtree(target)
                            if backup_item.is_file():
                                shutil.copy2(backup_item, target)
                            else:
                                shutil.copytree(backup_item, target)
                    shutil.rmtree(backup_dir)
            except:
                pass
            
            return False, f"恢复失败: {str(e)}"
    
    def get_last_sync_info(self) -> dict:
        """获取上次同步信息"""
        last_sync = self.config.get('last_sync')
        status = self.config.get('last_sync_status')
        
        if last_sync:
            try:
                dt = datetime.fromisoformat(last_sync)
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = last_sync
        else:
            time_str = "从未同步"
        
        return {
            'last_sync': last_sync,
            'last_sync_display': time_str,
            'status': status,
            'status_display': '成功' if status == 'success' else ('失败' if status == 'failed' else '未知')
        }


# 全局WebDAV同步实例
webdav_sync = WebDAVSync()
