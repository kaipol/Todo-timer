"""
今日日记概况组件 - 用于日历视图中显示今日日记
"""
import re
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QListWidget)
from PyQt6.QtCore import Qt, pyqtSignal

from core.storage.diary_storage import diary_storage
from .diary_editor_dialog import DiaryEditorDialog


class TodayDiaryWidget(QWidget):
    """今日日记概况组件 - 用于日历视图中显示今日日记"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 标题栏
        header = QHBoxLayout()
        header.setSpacing(8)
        
        title = QLabel("📔 今日日记")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        header.addWidget(title)
        
        header.addStretch()
        
        # 写日记按钮
        self.write_btn = QPushButton("✏️ 写日记")
        self.write_btn.setFixedHeight(28)
        self.write_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #e8f4ff;
                color: #007bff;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #d0e8ff;
            }
        """)
        self.write_btn.clicked.connect(self._write_diary)
        header.addWidget(self.write_btn)
        
        layout.addLayout(header)
        
        # 日记列表区域
        self.diary_list = QListWidget()
        self.diary_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: none;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 6px;
                margin: 2px 0;
                padding: 8px;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #d0e8ff;
                color: #333;
            }
        """)
        self.diary_list.setMinimumHeight(100)
        self.diary_list.setMaximumHeight(200)
        self.diary_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.diary_list)
        
        # 空状态提示
        self.empty_label = QLabel("📝 今天还没有写日记，点击上方按钮开始记录吧~")
        self.empty_label.setStyleSheet("color: #999; font-size: 12px; padding: 20px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
        
        layout.addStretch()
    
    def refresh(self):
        """刷新今日日记列表"""
        self.diary_list.clear()
        
        today = datetime.now().date()
        entries = diary_storage.get_entries_by_date(today)
        
        if not entries:
            self.diary_list.hide()
            self.empty_label.show()
            return
        
        self.empty_label.hide()
        self.diary_list.show()
        
        for entry in entries:
            # 创建列表项
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem()
            
            # 格式化显示内容
            time_str = entry.created_at.strftime("%H:%M")
            mood = entry.mood or ""
            title = entry.title or "无标题"
            
            # 截断过长的标题
            if len(title) > 20:
                title = title[:17] + "..."
            
            # 获取内容预览
            content_preview = self._get_content_preview(entry.content)
            
            # 组合显示文本
            display_text = f"{mood} {time_str} | {title}"
            if content_preview:
                display_text += f"\n    {content_preview}"
            
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            item.setToolTip(f"标题: {entry.title}\n时间: {entry.created_at.strftime('%Y-%m-%d %H:%M')}\n标签: {', '.join(entry.tags) if entry.tags else '无'}")
            
            self.diary_list.addItem(item)
    
    def _get_content_preview(self, content: str, max_length: int = 50) -> str:
        """获取内容预览"""
        if not content:
            return ""
        
        # 移除Markdown标记
        preview = content
        # 移除标题标记
        preview = re.sub(r'^#+\s+', '', preview, flags=re.MULTILINE)
        # 移除粗体/斜体
        preview = re.sub(r'\*+([^*]+)\*+', r'\1', preview)
        # 移除链接
        preview = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', preview)
        # 移除图片
        preview = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[图片]', preview)
        # 移除代码块
        preview = re.sub(r'```[\s\S]*?```', '[代码]', preview)
        # 移除行内代码
        preview = re.sub(r'`([^`]+)`', r'\1', preview)
        # 移除换行
        preview = preview.replace('\n', ' ').strip()
        
        if len(preview) > max_length:
            preview = preview[:max_length - 3] + "..."
        
        return preview
    
    def _write_diary(self):
        """写新日记"""
        dialog = DiaryEditorDialog(self)
        dialog.saved.connect(self._on_diary_saved)
        dialog.exec()
    
    def _on_diary_saved(self, entry_id: str):
        """日记保存后刷新"""
        self.refresh()
        self.data_changed.emit()
    
    def _on_item_double_clicked(self, item):
        """双击查看/编辑日记"""
        entry_id = item.data(Qt.ItemDataRole.UserRole)
        if entry_id:
            entry = diary_storage.get_entry(entry_id)
            if entry:
                dialog = DiaryEditorDialog(self, entry)
                dialog.saved.connect(self._on_diary_saved)
                dialog.exec()