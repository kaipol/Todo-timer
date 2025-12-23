"""
日记主组件
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QComboBox, QFrame,
                              QScrollArea, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt

from core.storage.diary_storage import diary_storage
from .diary_entry_item import DiaryEntryItem
from .diary_editor_dialog import DiaryEditorDialog
from .markdown_editor import MarkdownPreview


class DiaryWidget(QWidget):
    """日记主组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_entries()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 左侧：日记列表
        left_panel = QFrame()
        left_panel.setFixedWidth(320)
        left_panel.setStyleSheet("background: #f8f9fa; border-right: 1px solid #e0e0e0;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(12)
        
        # 顶部操作栏
        top_bar = QHBoxLayout()
        title = QLabel("📔 我的日记")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        
        new_btn = QPushButton("✏️ 写日记")
        new_btn.setFixedSize(80, 32)
        new_btn.setStyleSheet("""
            QPushButton {
                background: #007bff; color: white;
                border: none; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background: #0056b3; }
        """)
        new_btn.clicked.connect(self._new_entry)
        top_bar.addWidget(new_btn)
        left_layout.addLayout(top_bar)
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索日记...")
        self.search_edit.setFixedHeight(36)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px; border: 1px solid #e0e0e0;
                border-radius: 18px; background: white;
            }
        """)
        self.search_edit.textChanged.connect(self._on_search)
        left_layout.addWidget(self.search_edit)
        
        # 筛选栏
        filter_bar = QHBoxLayout()
        
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("全部标签")
        self.tag_filter.addItems(diary_storage.tags)
        self.tag_filter.setFixedHeight(30)
        self.tag_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self.tag_filter)
        
        self.mood_filter = QComboBox()
        self.mood_filter.addItem("全部心情")
        self.mood_filter.addItems(["😊 开心", "😢 难过", "🤩 兴奋", "😴 疲惫", "😠 生气", "🥰 幸福"])
        self.mood_filter.setFixedHeight(30)
        self.mood_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self.mood_filter)
        
        left_layout.addLayout(filter_bar)
        
        # 日记列表
        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_scroll.setStyleSheet("border: none; background: transparent;")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        
        self.list_scroll.setWidget(self.list_container)
        left_layout.addWidget(self.list_scroll)
        
        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #888; font-size: 12px;")
        left_layout.addWidget(self.stats_label)
        
        layout.addWidget(left_panel)
        
        # 右侧：日记详情/预览
        right_panel = QFrame()
        right_panel.setStyleSheet("background: white;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        self.detail_stack = QStackedWidget()
        
        # 空状态
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label = QLabel("📝 选择一篇日记查看\n或点击「写日记」开始记录")
        empty_label.setStyleSheet("color: #999; font-size: 16px;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.detail_stack.addWidget(empty_widget)
        
        # 日记详情
        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        
        # 详情头部
        detail_header = QHBoxLayout()
        self.detail_title = QLabel()
        self.detail_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
        self.detail_title.setWordWrap(True)
        detail_header.addWidget(self.detail_title)
        detail_header.addStretch()
        
        edit_btn = QPushButton("✏️ 编辑")
        edit_btn.setFixedSize(70, 32)
        edit_btn.setStyleSheet("background: #f0f0f0; border: none; border-radius: 6px;")
        edit_btn.clicked.connect(self._edit_current)
        detail_header.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setStyleSheet("background: #fff0f0; border: none; border-radius: 6px;")
        delete_btn.clicked.connect(self._delete_current)
        detail_header.addWidget(delete_btn)
        
        detail_layout.addLayout(detail_header)
        
        # 元信息
        self.detail_meta = QLabel()
        self.detail_meta.setStyleSheet("color: #888; font-size: 13px; margin: 8px 0;")
        detail_layout.addWidget(self.detail_meta)
        
        # 内容预览
        self.detail_content = MarkdownPreview()
        detail_layout.addWidget(self.detail_content)
        
        self.detail_stack.addWidget(self.detail_widget)
        right_layout.addWidget(self.detail_stack)
        
        layout.addWidget(right_panel)
        
        self.current_entry_id = None
    
    def _load_entries(self):
        """加载日记列表"""
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        entries = diary_storage.get_all_entries()
        
        for entry in entries:
            item = DiaryEntryItem(entry)
            item.clicked.connect(self._show_entry)
            item.edit_requested.connect(self._edit_entry)
            item.delete_requested.connect(self._delete_entry)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)
        
        stats = diary_storage.get_statistics()
        self.stats_label.setText(f"共 {stats['total']} 篇日记")
    
    def _new_entry(self):
        """新建日记"""
        dialog = DiaryEditorDialog(self)
        dialog.saved.connect(self._on_entry_saved)
        dialog.exec()
    
    def _show_entry(self, entry_id: str):
        """显示日记详情"""
        entry = diary_storage.get_entry(entry_id)
        if not entry:
            return
        
        self.current_entry_id = entry_id
        self.detail_title.setText(entry.title or "无标题")
        
        meta_parts = [entry.created_at.strftime("%Y年%m月%d日 %H:%M")]
        if entry.mood:
            meta_parts.append(entry.mood)
        if entry.weather:
            meta_parts.append(entry.weather)
        if entry.tags:
            meta_parts.append(" ".join([f"#{t}" for t in entry.tags]))
        self.detail_meta.setText(" · ".join(meta_parts))
        
        self.detail_content.set_markdown(entry.content)
        self.detail_stack.setCurrentIndex(1)
    
    def _edit_entry(self, entry_id: str):
        """编辑日记"""
        entry = diary_storage.get_entry(entry_id)
        if entry:
            dialog = DiaryEditorDialog(self, entry)
            dialog.saved.connect(self._on_entry_saved)
            dialog.exec()
    
    def _edit_current(self):
        """编辑当前日记"""
        if self.current_entry_id:
            self._edit_entry(self.current_entry_id)
    
    def _delete_entry(self, entry_id: str):
        """删除日记"""
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这篇日记吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            diary_storage.delete_entry(entry_id)
            if self.current_entry_id == entry_id:
                self.current_entry_id = None
                self.detail_stack.setCurrentIndex(0)
            self._load_entries()
    
    def _delete_current(self):
        """删除当前日记"""
        if self.current_entry_id:
            self._delete_entry(self.current_entry_id)
    
    def _on_entry_saved(self, entry_id: str):
        """日记保存后刷新"""
        self._load_entries()
        self._show_entry(entry_id)
    
    def _on_search(self, text: str):
        """搜索日记"""
        if not text.strip():
            self._load_entries()
            return
        
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        entries = diary_storage.search_entries(text)
        for entry in entries:
            item = DiaryEntryItem(entry)
            item.clicked.connect(self._show_entry)
            item.edit_requested.connect(self._edit_entry)
            item.delete_requested.connect(self._delete_entry)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)
    
    def _on_filter_changed(self):
        """筛选条件变化"""
        tag = self.tag_filter.currentText()
        mood = self.mood_filter.currentText()
        
        if tag == "全部标签":
            tag = None
        if mood == "全部心情":
            mood = None
        
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if tag:
            entries = diary_storage.get_entries_by_tag(tag)
        elif mood:
            entries = diary_storage.get_entries_by_mood(mood)
        else:
            entries = diary_storage.get_all_entries()
        
        for entry in entries:
            item = DiaryEntryItem(entry)
            item.clicked.connect(self._show_entry)
            item.edit_requested.connect(self._edit_entry)
            item.delete_requested.connect(self._delete_entry)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)