"""
Markdown语法高亮器
"""
import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtGui import QFont


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown语法高亮器"""
    
    def __init__(self, document):
        super().__init__(document)
        self._init_formats()
    
    def _init_formats(self):
        """初始化格式"""
        self.h1_format = QTextCharFormat()
        self.h1_format.setFontWeight(QFont.Weight.Bold)
        self.h1_format.setFontPointSize(20)
        self.h1_format.setForeground(QColor("#1a73e8"))
        
        self.h2_format = QTextCharFormat()
        self.h2_format.setFontWeight(QFont.Weight.Bold)
        self.h2_format.setFontPointSize(18)
        self.h2_format.setForeground(QColor("#1a73e8"))
        
        self.h3_format = QTextCharFormat()
        self.h3_format.setFontWeight(QFont.Weight.Bold)
        self.h3_format.setFontPointSize(16)
        self.h3_format.setForeground(QColor("#1a73e8"))
        
        self.h4_format = QTextCharFormat()
        self.h4_format.setFontWeight(QFont.Weight.Bold)
        self.h4_format.setFontPointSize(14)
        self.h4_format.setForeground(QColor("#1a73e8"))
        
        self.bold_format = QTextCharFormat()
        self.bold_format.setFontWeight(QFont.Weight.Bold)
        self.bold_format.setForeground(QColor("#333"))
        
        self.italic_format = QTextCharFormat()
        self.italic_format.setFontItalic(True)
        self.italic_format.setForeground(QColor("#555"))
        
        self.code_format = QTextCharFormat()
        self.code_format.setFontFamily("Consolas")
        self.code_format.setBackground(QColor("#f5f5f5"))
        self.code_format.setForeground(QColor("#d63384"))
        
        self.code_block_format = QTextCharFormat()
        self.code_block_format.setFontFamily("Consolas")
        self.code_block_format.setBackground(QColor("#f8f9fa"))
        self.code_block_format.setForeground(QColor("#212529"))
        
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#0d6efd"))
        self.link_format.setFontUnderline(True)
        
        self.image_format = QTextCharFormat()
        self.image_format.setForeground(QColor("#198754"))
        
        self.quote_format = QTextCharFormat()
        self.quote_format.setForeground(QColor("#6c757d"))
        self.quote_format.setFontItalic(True)
        
        self.list_format = QTextCharFormat()
        self.list_format.setForeground(QColor("#fd7e14"))
        
        self.math_format = QTextCharFormat()
        self.math_format.setForeground(QColor("#6f42c1"))
        self.math_format.setBackground(QColor("#f8f0ff"))
        
        self.hr_format = QTextCharFormat()
        self.hr_format.setForeground(QColor("#adb5bd"))
    
    def highlightBlock(self, text):
        """高亮文本块"""
        if text.startswith('# '):
            self.setFormat(0, len(text), self.h1_format)
            return
        elif text.startswith('## '):
            self.setFormat(0, len(text), self.h2_format)
            return
        elif text.startswith('### '):
            self.setFormat(0, len(text), self.h3_format)
            return
        elif text.startswith('#### '):
            self.setFormat(0, len(text), self.h4_format)
            return
        
        if text.startswith('>'):
            self.setFormat(0, len(text), self.quote_format)
            return
        
        if re.match(r'^[-*_]{3,}\s*$', text):
            self.setFormat(0, len(text), self.hr_format)
            return
        
        if re.match(r'^[\s]*[-*+]\s', text) or re.match(r'^[\s]*\d+\.\s', text):
            match = re.match(r'^([\s]*[-*+\d.]+\s)', text)
            if match:
                self.setFormat(0, len(match.group(1)), self.list_format)
        
        if text.startswith('```'):
            self.setFormat(0, len(text), self.code_block_format)
            return
        
        for match in re.finditer(r'\*\*([^*]+)\*\*|__([^_]+)__', text):
            self.setFormat(match.start(), match.end() - match.start(), self.bold_format)
        
        for match in re.finditer(r'(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)', text):
            self.setFormat(match.start(), match.end() - match.start(), self.italic_format)
        
        for match in re.finditer(r'`([^`]+)`', text):
            self.setFormat(match.start(), match.end() - match.start(), self.code_format)
        
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', text):
            self.setFormat(match.start(), match.end() - match.start(), self.link_format)
        
        for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', text):
            self.setFormat(match.start(), match.end() - match.start(), self.image_format)
        
        for match in re.finditer(r'\$([^$]+)\$', text):
            self.setFormat(match.start(), match.end() - match.start(), self.math_format)