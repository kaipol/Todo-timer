"""
日记编辑对话框
"""
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QComboBox, QTextEdit,
                              QFrame, QSplitter, QFileDialog, QInputDialog,
                              QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut

from core.storage.diary_storage import diary_storage, DiaryEntry
from .markdown_editor import MarkdownEditor, MarkdownPreview


class DiaryEditorDialog(QDialog):
    """日记编辑对话框"""
    saved = pyqtSignal(str)
    
    def __init__(self, parent=None, entry: DiaryEntry = None):
        super().__init__(parent)
        self.entry = entry
        self.is_new = entry is None
        self.setWindowTitle("写日记" if self.is_new else "编辑日记")
        self.setMinimumSize(900, 700)
        self._setup_ui()
        if entry:
            self._load_entry(entry)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 顶部信息栏
        top_bar = QHBoxLayout()
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("📝 输入日记标题...")
        self.title_edit.setFixedHeight(40)
        self.title_edit.setStyleSheet("""
            QLineEdit {
                font-size: 16px; font-weight: bold;
                padding: 8px 12px; border: 1px solid #e0e0e0;
                border-radius: 8px; background: white;
            }
        """)
        top_bar.addWidget(self.title_edit, stretch=2)
        
        self.mood_combo = QComboBox()
        self.mood_combo.addItems(["😐 一般", "😊 开心", "😢 难过", "🤩 兴奋", "😴 疲惫", "😠 生气", "🥰 幸福"])
        self.mood_combo.setFixedSize(100, 36)
        top_bar.addWidget(QLabel("心情:"))
        top_bar.addWidget(self.mood_combo)
        
        self.weather_edit = QLineEdit()
        self.weather_edit.setPlaceholderText("☀️")
        self.weather_edit.setFixedSize(60, 36)
        top_bar.addWidget(QLabel("天气:"))
        top_bar.addWidget(self.weather_edit)
        
        layout.addLayout(top_bar)
        
        # 标签栏
        tags_bar = QHBoxLayout()
        tags_bar.addWidget(QLabel("标签:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("用逗号分隔...")
        self.tags_edit.setFixedHeight(32)
        tags_bar.addWidget(self.tags_edit)
        layout.addLayout(tags_bar)
        
        # 先创建编辑器（工具栏需要引用它）
        self.editor = MarkdownEditor()
        self.preview = MarkdownPreview()
        
        # 工具栏（现在可以安全引用 self.editor）
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 编辑区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        editor_frame = QFrame()
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(QLabel("✏️ 编辑"))
        self.editor.textChanged.connect(self._on_text_changed)
        editor_layout.addWidget(self.editor)
        splitter.addWidget(editor_frame)
        
        preview_frame = QFrame()
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.addWidget(QLabel("👁️ 预览"))
        preview_layout.addWidget(self.preview)
        splitter.addWidget(preview_frame)
        
        splitter.setSizes([500, 400])
        layout.addWidget(splitter)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QLabel(f"📅 {datetime.now().strftime('%Y年%m月%d日')}"))
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 36)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 保存")
        save_btn.setFixedSize(100, 36)
        save_btn.setStyleSheet("background: #007bff; color: white; border: none; border-radius: 6px;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # 快捷键
        QShortcut(QKeySequence("Ctrl+S"), self, self._save)
        QShortcut(QKeySequence("Ctrl+B"), self, lambda: self.editor.insert_markdown("**", "**"))
        QShortcut(QKeySequence("Ctrl+I"), self, lambda: self.editor.insert_markdown("*", "*"))
    
    def _create_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setStyleSheet("background: #f8f9fa; border-radius: 8px;")
        toolbar.setFixedHeight(40)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        def add_btn(text, tooltip, callback):
            btn = QPushButton(text)
            btn.setFixedSize(32, 28)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("border: none; border-radius: 4px; background: transparent;")
            btn.clicked.connect(callback)
            layout.addWidget(btn)
            return btn
        
        add_btn("H1", "一级标题", lambda: self.editor.insert_heading(1))
        add_btn("H2", "二级标题", lambda: self.editor.insert_heading(2))
        add_btn("H3", "三级标题", lambda: self.editor.insert_heading(3))
        add_btn("B", "粗体", lambda: self.editor.insert_markdown("**", "**"))
        add_btn("I", "斜体", lambda: self.editor.insert_markdown("*", "*"))
        add_btn("`", "代码", lambda: self.editor.insert_markdown("`", "`"))
        add_btn("🔗", "链接", self._insert_link)
        add_btn("🖼", "图片", self._insert_image)
        add_btn("•", "列表", lambda: self.editor.insert_list(False))
        add_btn("1.", "有序列表", lambda: self.editor.insert_list(True))
        add_btn(">", "引用", self.editor.insert_quote)
        add_btn("```", "代码块", lambda: self.editor.insert_code_block())
        add_btn("∑", "公式", lambda: self.editor.insert_math(False))
        add_btn("—", "分隔线", self.editor.insert_hr)
        
        layout.addStretch()
        return toolbar
    
    def _on_text_changed(self):
        self.preview.set_markdown(self.editor.toPlainText())
    
    def _insert_link(self):
        text, ok1 = QInputDialog.getText(self, "插入链接", "链接文字:")
        if ok1 and text:
            url, ok2 = QInputDialog.getText(self, "插入链接", "链接地址:", text="https://")
            if ok2 and url:
                self.editor.insert_link(text, url)
    
    def _insert_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片 (*.png *.jpg *.jpeg *.gif *.webp)")
        if file_path:
            saved_path = diary_storage.save_image(file_path)
            alt, ok = QInputDialog.getText(self, "图片描述", "输入描述:")
            if ok:
                self.editor.insert_image(alt or "图片", saved_path or file_path)
    
    def _load_entry(self, entry: DiaryEntry):
        self.title_edit.setText(entry.title)
        self.editor.setPlainText(entry.content)
        self.tags_edit.setText(", ".join(entry.tags))
        if entry.mood:
            index = self.mood_combo.findText(entry.mood, Qt.MatchFlag.MatchContains)
            if index >= 0:
                self.mood_combo.setCurrentIndex(index)
        if entry.weather:
            self.weather_edit.setText(entry.weather)
    
    def _save(self):
        title = self.title_edit.text().strip()
        content = self.editor.toPlainText()
        
        if not content.strip():
            QMessageBox.warning(self, "提示", "日记内容不能为空")
            return
        
        tags = [t.strip() for t in self.tags_edit.text().split(',') if t.strip()]
        mood = self.mood_combo.currentText()
        weather = self.weather_edit.text().strip()
        
        if self.is_new:
            entry = diary_storage.add_entry(
                title=title or f"{datetime.now().strftime('%Y年%m月%d日')}的日记",
                content=content,
                tags=tags,
                mood=mood,
                weather=weather
            )
            entry_id = entry.id
        else:
            diary_storage.update_entry(
                self.entry.id,
                title=title,
                content=content,
                tags=tags,
                mood=mood,
                weather=weather
            )
            entry_id = self.entry.id
        
        self.saved.emit(entry_id)
        self.accept()