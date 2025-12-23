"""
UI工具函数模块 - 提取通用的工具函数
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

# ============== 预编译正则表达式 ==============
class RegexPatterns:
    """预编译的正则表达式模式"""
    
    # Markdown 相关
    HEADER = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    BOLD = re.compile(r'\*\*(.+?)\*\*')
    ITALIC = re.compile(r'\*(.+?)\*')
    CODE_BLOCK = re.compile(r'```[\s\S]*?```')
    INLINE_CODE = re.compile(r'`([^`]+)`')
    LINK = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    BLOCKQUOTE = re.compile(r'^>\s*(.+)$', re.MULTILINE)
    UNORDERED_LIST = re.compile(r'^[\s]*[-*+]\s+(.+)$', re.MULTILINE)
    ORDERED_LIST = re.compile(r'^[\s]*\d+\.\s+(.+)$', re.MULTILINE)
    HORIZONTAL_RULE = re.compile(r'^[-*_]{3,}$', re.MULTILINE)
    STRIKETHROUGH = re.compile(r'~~(.+?)~~')
    
    # 内容处理相关
    HTML_TAGS = re.compile(r'<[^>]+>')
    MULTIPLE_NEWLINES = re.compile(r'\n{3,}')
    MULTIPLE_SPACES = re.compile(r' {2,}')
    
    # 时间相关
    TIME_FORMAT = re.compile(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$')
    DATE_FORMAT = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')


# ============== 时间格式化函数 ==============
class TimeFormatter:
    """时间格式化工具类"""
    
    WEEKDAY_NAMES = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    MONTH_NAMES = ['一月', '二月', '三月', '四月', '五月', '六月', 
                   '七月', '八月', '九月', '十月', '十一月', '十二月']
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """
        格式化时长为可读字符串
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时长字符串，如 "2小时30分钟"
        """
        if seconds < 60:
            return f"{seconds}秒"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            if minutes > 0:
                return f"{hours}小时{minutes}分钟"
            return f"{hours}小时"
        return f"{minutes}分钟"
    
    @staticmethod
    def format_duration_short(seconds: int) -> str:
        """
        格式化时长为简短字符串
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时长字符串，如 "2h 30m"
        """
        if seconds < 60:
            return f"{seconds}s"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        return f"{minutes}m"
    
    @staticmethod
    def format_duration_hms(seconds: int) -> str:
        """
        格式化时长为 HH:MM:SS 格式
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时长字符串，如 "02:30:45"
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def format_time(dt: datetime) -> str:
        """
        格式化时间为 HH:MM 格式
        
        Args:
            dt: datetime对象
            
        Returns:
            格式化的时间字符串，如 "14:30"
        """
        return dt.strftime("%H:%M")
    
    @staticmethod
    def format_date(dt: datetime) -> str:
        """
        格式化日期为 YYYY-MM-DD 格式
        
        Args:
            dt: datetime对象
            
        Returns:
            格式化的日期字符串，如 "2024-01-15"
        """
        return dt.strftime("%Y-%m-%d")
    
    @staticmethod
    def format_date_chinese(dt: datetime) -> str:
        """
        格式化日期为中文格式
        
        Args:
            dt: datetime对象
            
        Returns:
            格式化的日期字符串，如 "2024年1月15日"
        """
        return f"{dt.year}年{dt.month}月{dt.day}日"
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """
        格式化日期时间
        
        Args:
            dt: datetime对象
            
        Returns:
            格式化的日期时间字符串，如 "2024-01-15 14:30"
        """
        return dt.strftime("%Y-%m-%d %H:%M")
    
    @staticmethod
    def format_relative_date(dt: datetime) -> str:
        """
        格式化为相对日期
        
        Args:
            dt: datetime对象
            
        Returns:
            相对日期字符串，如 "今天"、"昨天"、"3天前"
        """
        today = datetime.now().date()
        target_date = dt.date()
        delta = (today - target_date).days
        
        if delta == 0:
            return "今天"
        elif delta == 1:
            return "昨天"
        elif delta == 2:
            return "前天"
        elif delta < 7:
            return f"{delta}天前"
        elif delta < 30:
            weeks = delta // 7
            return f"{weeks}周前"
        elif delta < 365:
            months = delta // 30
            return f"{months}个月前"
        else:
            years = delta // 365
            return f"{years}年前"
    
    @staticmethod
    def get_weekday_name(dt: datetime) -> str:
        """
        获取星期名称
        
        Args:
            dt: datetime对象
            
        Returns:
            星期名称，如 "周一"
        """
        return TimeFormatter.WEEKDAY_NAMES[dt.weekday()]
    
    @staticmethod
    def get_week_range(dt: datetime) -> Tuple[datetime, datetime]:
        """
        获取指定日期所在周的起止日期
        
        Args:
            dt: datetime对象
            
        Returns:
            (周一日期, 周日日期) 元组
        """
        weekday = dt.weekday()
        start = dt - timedelta(days=weekday)
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def get_month_range(dt: datetime) -> Tuple[datetime, datetime]:
        """
        获取指定日期所在月的起止日期
        
        Args:
            dt: datetime对象
            
        Returns:
            (月初日期, 月末日期) 元组
        """
        start = dt.replace(day=1)
        # 获取下个月第一天，然后减一天
        if dt.month == 12:
            end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = dt.replace(month=dt.month + 1, day=1) - timedelta(days=1)
        return start, end


# ============== 文本处理函数 ==============
class TextProcessor:
    """文本处理工具类"""
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """
        截断文本
        
        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 截断后缀
            
        Returns:
            截断后的文本
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def strip_html(text: str) -> str:
        """
        移除HTML标签
        
        Args:
            text: 包含HTML的文本
            
        Returns:
            纯文本
        """
        return RegexPatterns.HTML_TAGS.sub('', text)
    
    @staticmethod
    def strip_markdown(text: str) -> str:
        """
        移除Markdown格式
        
        Args:
            text: Markdown文本
            
        Returns:
            纯文本
        """
        # 移除代码块
        text = RegexPatterns.CODE_BLOCK.sub('', text)
        # 移除内联代码
        text = RegexPatterns.INLINE_CODE.sub(r'\1', text)
        # 移除图片
        text = RegexPatterns.IMAGE.sub('', text)
        # 移除链接，保留文本
        text = RegexPatterns.LINK.sub(r'\1', text)
        # 移除标题标记
        text = RegexPatterns.HEADER.sub(r'\2', text)
        # 移除粗体
        text = RegexPatterns.BOLD.sub(r'\1', text)
        # 移除斜体
        text = RegexPatterns.ITALIC.sub(r'\1', text)
        # 移除删除线
        text = RegexPatterns.STRIKETHROUGH.sub(r'\1', text)
        # 移除引用标记
        text = RegexPatterns.BLOCKQUOTE.sub(r'\1', text)
        # 移除列表标记
        text = RegexPatterns.UNORDERED_LIST.sub(r'\1', text)
        text = RegexPatterns.ORDERED_LIST.sub(r'\1', text)
        # 移除水平线
        text = RegexPatterns.HORIZONTAL_RULE.sub('', text)
        
        return text.strip()
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        规范化空白字符
        
        Args:
            text: 原始文本
            
        Returns:
            规范化后的文本
        """
        # 将多个换行替换为两个
        text = RegexPatterns.MULTIPLE_NEWLINES.sub('\n\n', text)
        # 将多个空格替换为一个
        text = RegexPatterns.MULTIPLE_SPACES.sub(' ', text)
        return text.strip()
    
    @staticmethod
    def get_preview(text: str, max_length: int = 100) -> str:
        """
        获取文本预览
        
        Args:
            text: 原始文本
            max_length: 最大长度
            
        Returns:
            预览文本
        """
        # 移除Markdown格式
        plain_text = TextProcessor.strip_markdown(text)
        # 规范化空白
        plain_text = TextProcessor.normalize_whitespace(plain_text)
        # 替换换行为空格
        plain_text = plain_text.replace('\n', ' ')
        # 截断
        return TextProcessor.truncate(plain_text, max_length)
    
    @staticmethod
    def count_words(text: str) -> int:
        """
        统计字数（中英文混合）
        
        Args:
            text: 文本
            
        Returns:
            字数
        """
        # 移除Markdown格式
        plain_text = TextProcessor.strip_markdown(text)
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', plain_text))
        # 统计英文单词
        english_words = len(re.findall(r'[a-zA-Z]+', plain_text))
        return chinese_chars + english_words


# ============== UI辅助函数 ==============
class UIHelper:
    """UI辅助工具类"""
    
    @staticmethod
    def create_separator_line() -> str:
        """创建分隔线样式"""
        return """
            QFrame {
                background-color: #3c3c3c;
                max-height: 1px;
                min-height: 1px;
            }
        """
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """
        根据状态获取颜色
        
        Args:
            status: 状态字符串
            
        Returns:
            颜色代码
        """
        status_colors = {
            'success': '#4CAF50',
            'warning': '#FFC107',
            'error': '#f44336',
            'info': '#2196F3',
            'pending': '#888888',
            'active': '#4a90d9',
            'completed': '#4CAF50',
        }
        return status_colors.get(status.lower(), '#888888')
    
    @staticmethod
    def get_priority_color(priority: int) -> str:
        """
        根据优先级获取颜色
        
        Args:
            priority: 优先级 (1-5)
            
        Returns:
            颜色代码
        """
        priority_colors = {
            1: '#f44336',  # 最高 - 红色
            2: '#FF9800',  # 高 - 橙色
            3: '#FFC107',  # 中 - 黄色
            4: '#4CAF50',  # 低 - 绿色
            5: '#888888',  # 最低 - 灰色
        }
        return priority_colors.get(priority, '#888888')
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节数
            
        Returns:
            格式化的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


# ============== 数据验证函数 ==============
class Validator:
    """数据验证工具类"""
    
    @staticmethod
    def is_valid_time(time_str: str) -> bool:
        """
        验证时间格式
        
        Args:
            time_str: 时间字符串
            
        Returns:
            是否有效
        """
        match = RegexPatterns.TIME_FORMAT.match(time_str)
        if not match:
            return False
        
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3)) if match.group(3) else 0
        
        return 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59
    
    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """
        验证日期格式
        
        Args:
            date_str: 日期字符串
            
        Returns:
            是否有效
        """
        match = RegexPatterns.DATE_FORMAT.match(date_str)
        if not match:
            return False
        
        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            datetime(year, month, day)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名中的非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # Windows 非法字符
        illegal_chars = r'<>:"/\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
