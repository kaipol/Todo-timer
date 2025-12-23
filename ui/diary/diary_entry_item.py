"""
日记条目项组件
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, pyqtSignal

from core.storage.diary_storage import DiaryEntry


class DiaryEntryItem(QFrame):
    """日记条目项"""
    clicked = pyqtSignal(str)
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    
    def __init__(self, entry: DiaryEntry, parent=None):
        super().__init__(parent)
        self.entry = entry
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 12px;
            }
            QFrame:hover {
                border-color: #007bff;
                background: #f8f9ff;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # 顶部：日期和心情
        top = QHBoxLayout()
        date_str = self.entry.created_at.strftime("%m月%d日")
        date_label = QLabel(f"📅 {date_str}")
        date_label.setStyleSheet("color: #666; font-size: 12px;")
        top.addWidget(date_label)
        
        if self.entry.mood:
            mood_label = QLabel(self.entry.mood)
            mood_label.setStyleSheet("font-size: 14px;")
            top.addWidget(mood_label)
        
        if self.entry.weather:
            weather_label = QLabel(self.entry.weather)
            weather_label.setStyleSheet("color: #888; font-size: 12px;")
            top.addWidget(weather_label)
        
        top.addStretch()
        layout.addLayout(top)
        
        # 标题
        title = QLabel(self.entry.title or "无标题")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # 内容预览
        preview = self.entry.content[:100].replace('\n', ' ')
        if len(self.entry.content) > 100:
            preview += "..."
        preview_label = QLabel(preview)
        preview_label.setStyleSheet("color: #666; font-size: 13px;")
        preview_label.setWordWrap(True)
        layout.addWidget(preview_label)
        
        # 标签
        if self.entry.tags:
            tags_layout = QHBoxLayout()
            for tag in self.entry.tags[:3]:
                tag_label = QLabel(f"#{tag}")
                tag_label.setStyleSheet("""
                    background: #e7f3ff;
                    color: #0066cc;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 11px;
                """)
                tags_layout.addWidget(tag_label)
            tags_layout.addStretch()
            layout.addLayout(tags_layout)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.entry.id)
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ 编辑")
        delete_action = menu.addAction("🗑️ 删除")
        
        action = menu.exec(event.globalPos())
        if action == edit_action:
            self.edit_requested.emit(self.entry.id)
        elif action == delete_action:
            self.delete_requested.emit(self.entry.id)