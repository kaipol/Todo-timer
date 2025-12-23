"""
Markdown编辑器和预览器
"""
from PyQt6.QtWidgets import QTextEdit, QFrame, QHBoxLayout, QLabel, QSplitter
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor

from .markdown_highlighter import MarkdownHighlighter


class MarkdownEditor(QTextEdit):
    """Markdown编辑器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.highlighter = MarkdownHighlighter(self.document())
        self.setStyleSheet("""
            QTextEdit {
                background-color: #fefefe;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }
            QTextEdit:focus { border-color: #007bff; }
        """)
    
    def insert_markdown(self, prefix: str, suffix: str = ""):
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            pos = cursor.position()
            cursor.insertText(f"{prefix}{suffix}")
            cursor.setPosition(pos + len(prefix))
            self.setTextCursor(cursor)
    
    def insert_heading(self, level: int):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText('#' * level + ' ')
        self.setTextCursor(cursor)
    
    def insert_link(self, text: str = "", url: str = ""):
        if not text: text = "链接文字"
        if not url: url = "https://"
        self.insert_markdown(f"[{text}](", f"{url})")
    
    def insert_image(self, alt: str = "", url: str = ""):
        if not alt: alt = "图片描述"
        self.insert_markdown(f"![{alt}](", f"{url})")
    
    def insert_code_block(self, language: str = ""):
        cursor = self.textCursor()
        cursor.insertText(f"```{language}\n\n```")
        cursor.movePosition(QTextCursor.MoveOperation.Up)
        self.setTextCursor(cursor)
    
    def insert_math(self, block: bool = False):
        if block:
            self.insert_markdown("$$\n", "\n$$")
        else:
            self.insert_markdown("$", "$")
    
    def insert_list(self, ordered: bool = False):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("1. " if ordered else "- ")
        self.setTextCursor(cursor)
    
    def insert_quote(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("> ")
        self.setTextCursor(cursor)
    
    def insert_hr(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText("\n\n---\n\n")
        self.setTextCursor(cursor)


class MarkdownPreview(QTextEdit):
    """Markdown预览器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
    
    def set_markdown(self, text: str):
        self.setMarkdown(text)