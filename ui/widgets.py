"""
UI 组件模块 - 迷你窗口和列表项组件

性能优化:
- 缓存缩放后的图标避免重复缩放
- 复用子项 widget 而非每次重建
- 减少不必要的样式更新
"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                              QApplication, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap


class MiniWindow(QWidget):
    """迷你悬浮窗口，显示当前应用和时间"""
    restore_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Tracker Mini")
        self.setFixedSize(280, 45)
        
        # 窗口样式：无边框、置顶、工具窗口
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 主布局
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 280, 45)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(44, 62, 80, 0.95);
                border-radius: 10px;
            }
        """)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # 应用图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("background-color: #34495e; border-radius: 5px; color: white;")
        layout.addWidget(self.icon_label)
        
        # 应用名称
        self.name_label = QLabel("等待中...")
        self.name_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        self.name_label.setMaximumWidth(120)
        layout.addWidget(self.name_label)
        
        # 时间显示
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.time_label)
        
        layout.addStretch()
        
        # 展开按钮
        expand_btn = QLabel("⬜")
        expand_btn.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 14px;
                padding: 2px;
            }
            QLabel:hover { color: white; }
        """)
        expand_btn.mousePressEvent = lambda e: self.restore_signal.emit()
        expand_btn.setToolTip("展开主窗口")
        layout.addWidget(expand_btn)
        
        # 关闭按钮
        close_btn = QLabel("×")
        close_btn.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 18px;
                padding: 2px;
            }
            QLabel:hover { color: #e74c3c; }
        """)
        close_btn.mousePressEvent = lambda e: QApplication.quit()
        close_btn.setToolTip("关闭程序")
        layout.addWidget(close_btn)
        
        # 拖拽支持
        self.old_pos = None
        
        # 图标缓存引用
        self.icon_cache = {}
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event):
        self.old_pos = None
    
    def mouseDoubleClickEvent(self, event):
        """双击恢复主窗口"""
        self.restore_signal.emit()
    
    def update_display(self, data, icon_cache):
        """更新显示内容 - 优化版本，缓存缩放后的图标"""
        self.icon_cache = icon_cache
        current = data.get('current_app')
        
        if current:
            # 截断过长的名称
            name = current['name']
            display_name = name[:14] + "..." if len(name) > 15 else name
            
            # 只在内容变化时更新（减少不必要的重绘）
            if self.name_label.text() != display_name:
                self.name_label.setText(display_name)
            
            # 格式化时间
            seconds = current['session_time']
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            if self.time_label.text() != time_str:
                self.time_label.setText(time_str)
            
            # 图标 - 使用缓存的缩放版本
            path = current['path']
            if path in self.icon_cache and self.icon_cache[path]:
                # 使用缓存的缩放图标，避免每次都重新缩放
                cache_key = f"{path}_scaled_24"
                if cache_key not in self.icon_cache:
                    self.icon_cache[cache_key] = self.icon_cache[path].scaled(
                        24, 24,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                self.icon_label.setPixmap(self.icon_cache[cache_key])
            else:
                self.icon_label.clear()
                first_char = name[0] if name else "-"
                if self.icon_label.text() != first_char:
                    self.icon_label.setText(first_char)
        else:
            if self.name_label.text() != "闲置":
                self.name_label.setText("闲置")
            if self.time_label.text() != "00:00:00":
                self.time_label.setText("00:00:00")
            self.icon_label.clear()
            if self.icon_label.text() != "-":
                self.icon_label.setText("-")


class AppListItem(QWidget):
    """应用列表项组件 - 支持展开子项"""
    
    def __init__(self, name, time_str, icon=None, app_type='normal', children=None):
        super().__init__()
        self.app_type = app_type
        self.children_data = children or {}
        self.is_expanded = False
        self.child_widgets = []
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 主行容器
        self.header_widget = QWidget()
        self.header_widget.setMinimumHeight(50)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(10, 8, 10, 8)
        header_layout.setSpacing(12)
        
        # 展开按钮 (仅当有子项时显示)
        self.expand_btn = QLabel()
        self.expand_btn.setFixedSize(20, 20)
        self.expand_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.children_data:
            self.expand_btn.setText("▶")
            self.expand_btn.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 10px;
                    background: transparent;
                }
                QLabel:hover {
                    color: #007bff;
                }
            """)
            self.expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.expand_btn.mousePressEvent = lambda e: self.toggle_expand()
        else:
            self.expand_btn.setText("")
            self.expand_btn.setStyleSheet("background: transparent;")
        header_layout.addWidget(self.expand_btn)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(36, 36)
        if icon:
            self.icon_label.setPixmap(icon.scaled(
                36, 36,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.icon_label.setStyleSheet("background-color: #ddd; border-radius: 6px; font-size: 16px;")
            self.icon_label.setText(name[0] if name else "-")
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.icon_label)
        
        # 名称和类型标签
        name_container = QWidget()
        name_layout = QVBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(2)
        
        # Name - 截断过长的名称
        display_name = name if len(name) <= 20 else name[:17] + "..."
        self.name_label = QLabel(display_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #333;")
        self.name_label.setToolTip(name)  # 完整名称作为提示
        name_layout.addWidget(self.name_label)
        
        # 类型标签和子项数量
        if self.children_data:
            type_labels = {
                'browser': '🌐 浏览器',
                'chat': '💬 聊天',
                'editor': '📝 编辑器'
            }
            type_text = type_labels.get(app_type, '')
            if type_text:
                child_count = len(self.children_data)
                self.type_label = QLabel(f"{type_text} · {child_count}个标签")
                self.type_label.setStyleSheet("font-size: 11px; color: #888;")
                name_layout.addWidget(self.type_label)
        
        header_layout.addWidget(name_container)
        header_layout.addStretch()
        
        # Time
        self.time_label = QLabel(time_str)
        self.time_label.setStyleSheet("color: #007bff; font-size: 15px; font-weight: 500;")
        header_layout.addWidget(self.time_label)
        
        self.main_layout.addWidget(self.header_widget)
        
        # 子项容器 (初始隐藏)
        self.children_container = QWidget()
        self.children_layout = QVBoxLayout(self.children_container)
        self.children_layout.setContentsMargins(48, 0, 10, 8)  # 左侧缩进
        self.children_layout.setSpacing(4)
        self.children_container.hide()
        self.main_layout.addWidget(self.children_container)
        
        # 如果有子项，可以点击展开
        if self.children_data:
            self.header_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            self.header_widget.mousePressEvent = lambda e: self.toggle_expand()
    
    def toggle_expand(self):
        """切换展开/折叠状态"""
        if not self.children_data:
            return
        
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.expand_btn.setText("▼")
            self._populate_children()
            self.children_container.show()
        else:
            self.expand_btn.setText("▶")
            self.children_container.hide()
    
    def _populate_children(self):
        """填充子项 - 优化版本，复用现有 widget"""
        # 按时间排序子项
        sorted_children = sorted(
            self.children_data.items(),
            key=lambda x: x[1].get('total_time', 0),
            reverse=True
        )[:15]  # 最多显示15个子项
        
        # 计算需要的 widget 数量
        needed_count = len(sorted_children)
        current_count = len([w for w in self.child_widgets if isinstance(w, ChildListItem)])
        
        # 复用或创建 ChildListItem
        child_index = 0
        for key, data in sorted_children:
            if child_index < current_count:
                # 复用现有 widget
                child_widget = self.child_widgets[child_index]
                if isinstance(child_widget, ChildListItem):
                    child_widget.update_data(
                        title=data.get('title', key),
                        time_seconds=data.get('total_time', 0),
                        domain=data.get('domain')
                    )
            else:
                # 创建新 widget
                child_widget = ChildListItem(
                    title=data.get('title', key),
                    time_seconds=data.get('total_time', 0),
                    domain=data.get('domain'),
                    app_type=self.app_type
                )
                self.children_layout.addWidget(child_widget)
                self.child_widgets.append(child_widget)
            child_index += 1
        
        # 隐藏多余的 widget（而不是删除，以便复用）
        for i in range(needed_count, len(self.child_widgets)):
            widget = self.child_widgets[i]
            if isinstance(widget, ChildListItem):
                widget.hide()
            else:
                # 删除 "更多" 标签
                widget.deleteLater()
        
        # 清理已删除的 widget 引用
        self.child_widgets = self.child_widgets[:needed_count]
        
        # 确保所有需要的 widget 都可见
        for i in range(needed_count):
            self.child_widgets[i].show()
        
        # 如果有更多项，显示提示
        total_children = len(self.children_data)
        if total_children > 15:
            more_label = QLabel(f"... 还有 {total_children - 15} 项")
            more_label.setStyleSheet("color: #999; font-size: 12px; padding: 4px;")
            more_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.children_layout.addWidget(more_label)
            self.child_widgets.append(more_label)
    
    def update_children(self, children_data):
        """更新子项数据"""
        self.children_data = children_data or {}
        
        # 更新展开按钮显示
        if self.children_data:
            self.expand_btn.setText("▼" if self.is_expanded else "▶")
            self.expand_btn.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 10px;
                    background: transparent;
                }
                QLabel:hover {
                    color: #007bff;
                }
            """)
        else:
            self.expand_btn.setText("")
        
        # 如果已展开，重新填充子项
        if self.is_expanded and self.children_data:
            self._populate_children()


class ChildListItem(QWidget):
    """子项列表组件（标签页/聊天对象等）"""
    
    def __init__(self, title, time_seconds, domain=None, app_type='browser'):
        super().__init__()
        self.setMinimumHeight(36)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 6px;
            }
            QWidget:hover {
                background-color: #e8e8e8;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        
        # 类型图标
        type_icons = {
            'browser': '🔗',
            'chat': '👤',
            'editor': '📄'
        }
        icon_label = QLabel(type_icons.get(app_type, '•'))
        icon_label.setFixedWidth(20)
        icon_label.setStyleSheet("background: transparent; font-size: 12px;")
        layout.addWidget(icon_label)
        
        # 标题
        title_text = title if len(title) <= 40 else title[:37] + "..."
        title_label = QLabel(title_text)
        title_label.setStyleSheet("background: transparent; font-size: 13px; color: #444;")
        title_label.setToolTip(title)  # 完整标题作为提示
        layout.addWidget(title_label)
        
        # 域名标签（浏览器专用）
        if domain:
            domain_label = QLabel(domain)
            domain_label.setStyleSheet("""
                background-color: #e0e7ff;
                color: #4f46e5;
                font-size: 10px;
                padding: 2px 6px;
                border-radius: 3px;
            """)
            layout.addWidget(domain_label)
        
        layout.addStretch()
        
        # 时间
        time_str = self._format_time(time_seconds)
        time_label = QLabel(time_str)
        time_label.setStyleSheet("background: transparent; color: #666; font-size: 12px;")
        layout.addWidget(time_label)
    
    def _format_time(self, seconds):
        """格式化时间"""
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            m, s = divmod(seconds, 60)
            return f"{m}分{s}秒"
        else:
            h, remainder = divmod(seconds, 3600)
            m, s = divmod(remainder, 60)
            return f"{h}时{m}分"