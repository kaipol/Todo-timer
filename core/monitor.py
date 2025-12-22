"""
应用监控模块 - 负责监控前台应用使用时间
支持窗口标题追踪（浏览器标签页、聊天窗口等）
"""
import time
import re
from datetime import datetime
import psutil
import win32gui
import win32process
import win32con
from PyQt6.QtCore import pyqtSignal, QThread


# 需要追踪子窗口的应用配置
# key: 进程名(小写), value: {'type': 类型, 'extract': 提取函数名}
TRACKED_APPS = {
    # 浏览器
    'chrome.exe': {'type': 'browser', 'name': 'Google Chrome'},
    'msedge.exe': {'type': 'browser', 'name': 'Microsoft Edge'},
    'firefox.exe': {'type': 'browser', 'name': 'Firefox'},
    'opera.exe': {'type': 'browser', 'name': 'Opera'},
    'brave.exe': {'type': 'browser', 'name': 'Brave'},
    '360se.exe': {'type': 'browser', 'name': '360浏览器'},
    'qqbrowser.exe': {'type': 'browser', 'name': 'QQ浏览器'},
    'sogouexplorer.exe': {'type': 'browser', 'name': '搜狗浏览器'},
    # 聊天软件
    'wechat.exe': {'type': 'chat', 'name': '微信'},
    'qq.exe': {'type': 'chat', 'name': 'QQ'},
    'tim.exe': {'type': 'chat', 'name': 'TIM'},
    'telegram.exe': {'type': 'chat', 'name': 'Telegram'},
    'discord.exe': {'type': 'chat', 'name': 'Discord'},
    'slack.exe': {'type': 'chat', 'name': 'Slack'},
    'dingtalk.exe': {'type': 'chat', 'name': '钉钉'},
    'wework.exe': {'type': 'chat', 'name': '企业微信'},
    'feishu.exe': {'type': 'chat', 'name': '飞书'},
    # 编辑器/IDE
    'code.exe': {'type': 'editor', 'name': 'VS Code'},
    'devenv.exe': {'type': 'editor', 'name': 'Visual Studio'},
    'idea64.exe': {'type': 'editor', 'name': 'IntelliJ IDEA'},
    'pycharm64.exe': {'type': 'editor', 'name': 'PyCharm'},
    'webstorm64.exe': {'type': 'editor', 'name': 'WebStorm'},
    'sublime_text.exe': {'type': 'editor', 'name': 'Sublime Text'},
    'notepad++.exe': {'type': 'editor', 'name': 'Notepad++'},
}


def extract_browser_info(window_title):
    """从浏览器窗口标题提取网站信息"""
    if not window_title:
        return None, None
    
    # 常见浏览器标题格式: "页面标题 - 浏览器名称" 或 "页面标题 — 浏览器名称"
    # 移除浏览器名称后缀
    browser_suffixes = [
        ' - Google Chrome', ' - Mozilla Firefox', ' - Microsoft Edge',
        ' - Opera', ' - Brave', ' — Mozilla Firefox', ' - 360安全浏览器',
        ' - QQ浏览器', ' - 搜狗浏览器', ' - Chromium'
    ]
    
    title = window_title
    for suffix in browser_suffixes:
        if title.endswith(suffix):
            title = title[:-len(suffix)]
            break
    
    # 尝试从标题提取域名（如果标题包含URL特征）
    domain = None
    # 检查是否是常见网站的标题模式
    domain_patterns = [
        (r'bilibili', 'bilibili.com'),
        (r'哔哩哔哩', 'bilibili.com'),
        (r'YouTube', 'youtube.com'),
        (r'知乎', 'zhihu.com'),
        (r'百度', 'baidu.com'),
        (r'Google', 'google.com'),
        (r'GitHub', 'github.com'),
        (r'Stack Overflow', 'stackoverflow.com'),
        (r'微博', 'weibo.com'),
        (r'淘宝', 'taobao.com'),
        (r'京东', 'jd.com'),
        (r'抖音', 'douyin.com'),
        (r'今日头条', 'toutiao.com'),
        (r'网易', '163.com'),
        (r'腾讯', 'qq.com'),
        (r'CSDN', 'csdn.net'),
        (r'掘金', 'juejin.cn'),
        (r'简书', 'jianshu.com'),
    ]
    
    for pattern, dom in domain_patterns:
        if re.search(pattern, title, re.IGNORECASE):
            domain = dom
            break
    
    return title.strip() if title.strip() else None, domain


def extract_chat_info(window_title, app_type):
    """从聊天软件窗口标题提取聊天对象"""
    if not window_title:
        return None
    
    title = window_title.strip()
    
    # 微信: 标题通常就是聊天对象名称，或者是"微信"
    # QQ: 标题通常是 "聊天对象名称" 或 "QQ"
    # 过滤掉主窗口标题
    main_window_titles = [
        '微信', 'WeChat', 'QQ', 'TIM', 'Telegram', 'Discord', 'Slack',
        '钉钉', '企业微信', '飞书', 'Feishu', 'DingTalk', 'WeCom'
    ]
    
    if title in main_window_titles:
        return '主界面'
    
    # 提取聊天对象（去除可能的后缀）
    # QQ格式可能是 "好友名称 - QQ"
    if ' - ' in title:
        parts = title.split(' - ')
        # 通常第一部分是聊天对象
        return parts[0].strip()
    
    # 微信的群聊可能带有人数 "群名称(123)"
    match = re.match(r'^(.+?)\(\d+\)$', title)
    if match:
        return match.group(1).strip()
    
    return title


def extract_editor_info(window_title):
    """从编辑器窗口标题提取文件/项目信息"""
    if not window_title:
        return None
    
    title = window_title.strip()
    
    # VS Code 格式: "文件名 - 项目名 - Visual Studio Code"
    # 或 "文件名 — 项目名 — Visual Studio Code"
    if ' - Visual Studio Code' in title or ' — Visual Studio Code' in title:
        title = title.replace(' — Visual Studio Code', '').replace(' - Visual Studio Code', '')
        parts = title.split(' - ') if ' - ' in title else title.split(' — ')
        if len(parts) >= 2:
            return f"{parts[0]} ({parts[1]})"  # 文件名 (项目名)
        return parts[0] if parts else title
    
    # 其他编辑器类似处理
    editor_suffixes = [
        ' - Visual Studio', ' - IntelliJ IDEA', ' - PyCharm',
        ' - WebStorm', ' - Sublime Text', ' - Notepad++'
    ]
    
    for suffix in editor_suffixes:
        if suffix in title:
            return title.split(suffix)[0].strip()
    
    return title


class AppMonitor(QThread):
    """应用监控线程，实时追踪前台应用使用时间"""
    update_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = True
        self.current_app = None
        self.current_sub_window = None  # 当前子窗口标识
        self.start_time = time.time()
        # 数据结构: {exe_path: {'name': name, 'total_time': seconds, 'children': {子窗口标识: {...}}, ...}}
        self.app_stats = {}
        self.last_check_time = time.time()
        self.today_date = datetime.now().date()  # 记录今日日期，用于跨天检测
        
        # 启动时加载今日已保存的数据
        self._load_today_data()
    
    def _load_today_data(self):
        """从存储中加载今日已保存的应用使用数据"""
        try:
            from core.storage import app_usage_storage
            
            today = datetime.now().date()
            records = app_usage_storage.load_daily_usage(today)
            
            if records:
                for record in records:
                    exe_path = record.exe_path
                    # 恢复应用数据
                    self.app_stats[exe_path] = {
                        'name': record.app_name,
                        'total_time': record.total_time,
                        'path': exe_path,
                        'session_time': 0,  # 会话时间重新计算
                        'is_active': False,
                        'app_type': record.app_type,
                        'children': {},
                        'current_child': None
                    }
                    
                    # 恢复子窗口数据
                    if record.children:
                        for key, child_data in record.children.items():
                            self.app_stats[exe_path]['children'][key] = {
                                'title': child_data.get('title', ''),
                                'total_time': int(child_data.get('total_time', 0)),
                                'session_time': 0,  # 会话时间重新计算
                                'is_active': False,
                                'domain': child_data.get('domain')
                            }
                
                print(f"已恢复今日 {len(records)} 个应用的使用记录")
        except Exception as e:
            print(f"加载今日数据失败: {e}")
    
    def _check_day_change(self):
        """检查是否跨天，如果跨天则重置数据"""
        current_date = datetime.now().date()
        if current_date != self.today_date:
            # 跨天了，清空统计数据
            print(f"检测到日期变化: {self.today_date} -> {current_date}，重置统计数据")
            self.app_stats = {}
            self.today_date = current_date
            self.current_app = None
            self.current_sub_window = None

    def get_active_window_info(self):
        """获取当前活动窗口信息"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            # 过滤逻辑：检查是否在任务栏可见
            # 1. 窗口必须可见
            if not win32gui.IsWindowVisible(hwnd):
                return None
            
            # 2. 获取扩展样式
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            
            # 3. 排除工具窗口，除非它显式设置了 APPWINDOW
            if (ex_style & win32con.WS_EX_TOOLWINDOW) and not (ex_style & win32con.WS_EX_APPWINDOW):
                return None
                
            # 4. 获取所有者。如果它是被拥有的窗口，通常不在任务栏显示，除非是 APPWINDOW
            owner = win32gui.GetWindow(hwnd, win32con.GW_OWNER)
            if owner and not (ex_style & win32con.WS_EX_APPWINDOW):
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                exe_path = process.exe()
                process_name = process.name().lower()
                
                # 过滤掉一些系统进程或特定的非应用进程
                if "explorer.exe" in exe_path.lower() and win32gui.GetWindowText(hwnd) == "":
                    return None
                
                # 获取窗口标题
                window_title = win32gui.GetWindowText(hwnd)
                
                # 确定应用名称和类型
                app_config = TRACKED_APPS.get(process_name, None)
                
                if app_config:
                    app_name = app_config['name']
                    app_type = app_config['type']
                else:
                    app_type = 'normal'
                    # 普通应用：使用窗口标题或进程名
                    app_name = process.name()
                    if window_title and " - " in window_title:
                        potential_name = window_title.split(" - ")[-1]
                        if len(potential_name) > 2:
                            app_name = potential_name
                    elif window_title:
                        app_name = window_title
                
                # 提取子窗口信息
                sub_window_title = None
                sub_window_key = None
                sub_window_domain = None
                
                if app_type == 'browser':
                    sub_title, domain = extract_browser_info(window_title)
                    if sub_title:
                        sub_window_title = sub_title
                        # 使用域名作为key（如果有），否则使用标题的前30字符
                        sub_window_key = domain if domain else (sub_title[:50] if len(sub_title) > 50 else sub_title)
                        sub_window_domain = domain
                elif app_type == 'chat':
                    chat_target = extract_chat_info(window_title, app_type)
                    if chat_target:
                        sub_window_title = chat_target
                        sub_window_key = chat_target
                elif app_type == 'editor':
                    editor_info = extract_editor_info(window_title)
                    if editor_info:
                        sub_window_title = editor_info
                        sub_window_key = editor_info[:50] if len(editor_info) > 50 else editor_info
                
                return {
                    'pid': pid,
                    'path': exe_path,
                    'name': app_name,
                    'hwnd': hwnd,
                    'window_title': window_title,
                    'app_type': app_type,
                    'sub_window_title': sub_window_title,
                    'sub_window_key': sub_window_key,
                    'sub_window_domain': sub_window_domain
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        except Exception:
            return None

    def run(self):
        """监控线程主循环"""
        while self.running:
            # 检查是否跨天
            self._check_day_change()
            
            now = time.time()
            elapsed = now - self.last_check_time
            self.last_check_time = now

            info = self.get_active_window_info()
            
            if info:
                exe_path = info['path']
                app_name = info['name']
                sub_key = info.get('sub_window_key')
                sub_title = info.get('sub_window_title')
                app_type = info.get('app_type', 'normal')

                # 初始化应用记录
                if exe_path not in self.app_stats:
                    self.app_stats[exe_path] = {
                        'name': app_name,
                        'total_time': 0,
                        'path': exe_path,
                        'session_time': 0,
                        'is_active': False,
                        'app_type': app_type,
                        'children': {},  # 子窗口记录
                        'current_child': None  # 当前子窗口
                    }

                # 累加应用总时间
                self.app_stats[exe_path]['total_time'] += elapsed
                
                # 处理子窗口时间
                if sub_key and app_type in ('browser', 'chat', 'editor'):
                    children = self.app_stats[exe_path]['children']
                    if sub_key not in children:
                        children[sub_key] = {
                            'title': sub_title,
                            'total_time': 0,
                            'session_time': 0,
                            'is_active': False,
                            'domain': info.get('sub_window_domain')  # 浏览器专用
                        }
                    
                    # 累加子窗口时间
                    children[sub_key]['total_time'] += elapsed
                    
                    # 子窗口会话时间处理
                    current_child_key = self.app_stats[exe_path].get('current_child')
                    if current_child_key != sub_key:
                        # 切换了子窗口
                        if current_child_key and current_child_key in children:
                            children[current_child_key]['is_active'] = False
                        self.app_stats[exe_path]['current_child'] = sub_key
                        if not children[sub_key]['is_active']:
                            children[sub_key]['session_time'] = 0
                        children[sub_key]['is_active'] = True
                    
                    children[sub_key]['session_time'] += elapsed
                
                # 会话时间处理
                if self.current_app != exe_path:
                    # 切换了应用，标记旧应用为非活动状态
                    if self.current_app and self.current_app in self.app_stats:
                        self.app_stats[self.current_app]['is_active'] = False
                        # 同时标记其当前子窗口为非活动
                        old_child = self.app_stats[self.current_app].get('current_child')
                        if old_child and old_child in self.app_stats[self.current_app]['children']:
                            self.app_stats[self.current_app]['children'][old_child]['is_active'] = False
                    
                    self.current_app = exe_path
                    # 只有当应用是新记录或从后台切回前台时，才重置会话时间
                    if not self.app_stats[exe_path]['is_active']:
                        self.app_stats[exe_path]['session_time'] = 0
                    self.app_stats[exe_path]['is_active'] = True
                
                self.app_stats[exe_path]['session_time'] += elapsed

                # 发送更新信号
                current_app_data = self.app_stats[exe_path].copy()
                current_app_data['current_sub_title'] = sub_title
                
                self.update_signal.emit({
                    'current_app': current_app_data,
                    'all_stats': self.app_stats
                })
            else:
                # 没有前台应用，标记当前应用为非活动但保留会话时间记录
                if self.current_app:
                    if self.current_app in self.app_stats:
                        self.app_stats[self.current_app]['is_active'] = False
                        # 同时标记其当前子窗口为非活动
                        old_child = self.app_stats[self.current_app].get('current_child')
                        if old_child and old_child in self.app_stats[self.current_app]['children']:
                            self.app_stats[self.current_app]['children'][old_child]['is_active'] = False
                    self.current_app = None
                
                self.update_signal.emit({
                    'current_app': None,
                    'all_stats': self.app_stats
                })

            time.sleep(1.0)

    def stop(self):
        """停止监控线程"""
        self.running = False
        self.wait()