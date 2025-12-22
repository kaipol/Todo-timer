"""
备忘录组件模块 - 待办事项管理界面
"""
import winsound
import threading
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QListWidget, QListWidgetItem,
                             QFrame, QComboBox, QDateTimeEdit, QMessageBox,
                             QDialog, QFormLayout, QDialogButtonBox, QCheckBox,
                             QTimeEdit, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from core.storage import memo_storage, MemoItem


class ReminderDialog(QDialog):
    """提醒设置对话框"""
    
    def __init__(self, parent=None, item: MemoItem = None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("设置提醒")
        self.setFixedSize(640, 460)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 16px;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(56, 40, 56, 40)
        layout.setSpacing(32)
        
        header = QHBoxLayout()
        header.setSpacing(18)
        hero = QLabel("🔔")
        hero.setFixedSize(54, 54)
        hero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero.setStyleSheet("background:#f0f4ff;border-radius:14px;font-size:26px;")
        header.addWidget(hero)
        
        title_box = QVBoxLayout()
        title = QLabel("设置提醒")
        title.setStyleSheet("font-size: 22px; font-weight: 600; color: #1f2d3d;")
        subtitle = QLabel("为该备忘事项配置提醒时间与重复周期")
        subtitle.setStyleSheet("font-size: 13px; color: #6c757d;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)
        
        self.enable_check = QCheckBox("启用提醒")
        self.enable_check.setChecked(self.item.reminder_enabled if self.item else True)
        self.enable_check.setStyleSheet("font-size: 16px; padding: 6px 0; color:#2f3b52;")
        self.enable_check.stateChanged.connect(self._on_enable_changed)
        layout.addWidget(self.enable_check)
        
        fields_frame = QFrame()
        fields_frame.setStyleSheet("QFrame { background:#f7f9fc; border-radius: 18px; border:1px solid #e2e8f0; }")
        grid = QGridLayout(fields_frame)
        grid.setContentsMargins(28, 24, 28, 24)
        grid.setHorizontalSpacing(36)
        grid.setVerticalSpacing(20)
        layout.addWidget(fields_frame)
        
        date_label = QLabel("日期")
        date_label.setStyleSheet("font-size: 14px; color: #5f6b7c; font-weight: 500;")
        grid.addWidget(date_label, 0, 0)
        
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy/MM/dd")
        self.date_edit.setFixedHeight(56)
        self.date_edit.setMinimumWidth(220)
        self.date_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_edit.setStyleSheet("""
            QDateTimeEdit {
                border: 1px solid #d0d7e2; border-radius: 12px;
                padding: 0 18px; font-size: 16px; background: white;
            }
            QDateTimeEdit::drop-down { border: none; width: 26px; }
        """)
        grid.addWidget(self.date_edit, 1, 0)
        
        time_label = QLabel("时间")
        time_label.setStyleSheet("font-size: 14px; color: #5f6b7c; font-weight: 500;")
        grid.addWidget(time_label, 0, 1)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setFixedHeight(56)
        self.time_edit.setMinimumWidth(180)
        self.time_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_edit.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)
        self.time_edit.setStyleSheet("""
            QTimeEdit {
                border: 1px solid #d0d7e2; border-radius: 12px;
                padding: 0 18px; font-size: 16px; background: white;
            }
        """)
        grid.addWidget(self.time_edit, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        
        repeat_label = QLabel("重复周期")
        repeat_label.setStyleSheet("font-size: 14px; color: #5f6b7c; font-weight: 500;")
        grid.addWidget(repeat_label, 2, 0, 1, 2)
        
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["不重复", "每天", "每周", "每月"])
        if self.item:
            repeat_map = {"none": 0, "daily": 1, "weekly": 2, "monthly": 3}
            self.repeat_combo.setCurrentIndex(repeat_map.get(self.item.reminder_repeat, 0))
        self.repeat_combo.setFixedHeight(54)
        self.repeat_combo.setMinimumWidth(300)
        self.repeat_combo.setStyleSheet("""
            QComboBox {
                font-size: 16px; padding: 0 18px;
                border: 1px solid #d0d7e2; border-radius: 12px;
                background: white;
            }
            QComboBox::drop-down { border: none; width: 28px; }
            QComboBox QAbstractItemView {
                padding: 10px;
                font-size: 14px;
            }
        """)
        grid.addWidget(self.repeat_combo, 3, 0, 1, 2)
        
        info_label = QLabel("提示：保存后会在待办列表中显示相同的提醒配置")
        info_label.setStyleSheet("font-size: 12px; color:#8a97ab;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(22)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(120, 44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px; border: 1px solid #d0d7e2;
                border-radius: 12px; background: white;
                padding: 10px 14px;
            }
            QPushButton:hover { background: #f5f7fb; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setFixedSize(120, 44)
        save_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px; border: none;
                border-radius: 12px; background: #007bff; color: white;
                padding: 10px 14px;
            }
            QPushButton:hover { background: #0064d4; }
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        if self.item and self.item.reminder_datetime:
            init_dt = self.item.reminder_datetime
        else:
            init_dt = datetime.now() + timedelta(hours=1)
        self.date_edit.setDateTime(init_dt)
        self.time_edit.setTime(init_dt.time())
        
        self._on_enable_changed()

    def _get_datetime_value(self) -> datetime:
        """从日期选择 + 手动输入时间合并 datetime"""
        base = self.date_edit.dateTime().toPyDateTime()
        t = self.time_edit.time()
        return base.replace(hour=t.hour(), minute=t.minute(), second=0, microsecond=0)
    
    def _on_enable_changed(self):
        enabled = self.enable_check.isChecked()
        self.date_edit.setEnabled(enabled)
        self.time_edit.setEnabled(enabled)
        self.repeat_combo.setEnabled(enabled)
    
    def get_values(self):
        """获取设置值"""
        enabled = self.enable_check.isChecked()
        dt = self._get_datetime_value() if enabled else None
        repeat_map = {0: "none", 1: "daily", 2: "weekly", 3: "monthly"}
        repeat = repeat_map.get(self.repeat_combo.currentIndex(), "none")
        return enabled, dt, repeat


class MemoWidget(QWidget):
    """备忘录组件"""
    
    reminder_triggered = pyqtSignal(str, str)  # item_id, content
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        # 提醒检查定时器
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start(30000)  # 每30秒检查
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)
        
        # 顶部统计和操作栏
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)
        
        self.stats_label = QLabel("📋 待办事项")
        self.stats_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        top_bar.addWidget(self.stats_label)
        
        top_bar.addStretch()
        
        # 筛选
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "未完成", "已完成", "有提醒"])
        self.filter_combo.setFixedWidth(85)
        self.filter_combo.setFixedHeight(28)
        self.filter_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd; border-radius: 4px;
                padding: 2px 6px; font-size: 11px; background: white;
            }
            QComboBox:hover { border-color: #007bff; }
            QComboBox::drop-down { border: none; width: 16px; }
        """)
        self.filter_combo.currentIndexChanged.connect(self._refresh_list)
        top_bar.addWidget(self.filter_combo)
        
        # 清理按钮
        clear_btn = QPushButton("🗑️")
        clear_btn.setFixedSize(26, 26)
        clear_btn.setToolTip("清理已完成")
        clear_btn.setStyleSheet("""
            QPushButton { border: none; background: #f8d7da; border-radius: 4px; }
            QPushButton:hover { background: #f5c6cb; }
        """)
        clear_btn.clicked.connect(self._clear_completed)
        top_bar.addWidget(clear_btn)
        
        layout.addLayout(top_bar)
        
        # 输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; }")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 8, 10, 8)
        input_layout.setSpacing(6)
        
        # 输入行
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("✏️ 添加待办事项...")
        self.input_edit.setFixedHeight(40)
        self.input_edit.setStyleSheet("""
            QLineEdit {
                font-size: 15px; padding: 8px 12px;
                border: 1px solid #e0e0e0; border-radius: 8px; background: white;
            }
            QLineEdit:focus { border-color: #007bff; }
        """)
        self.input_edit.returnPressed.connect(self._add_item)
        input_row.addWidget(self.input_edit)

        # 未启用提醒时，默认靠左但保持垂直居中
        self.input_edit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # 优先级（显示文字，避免只有图标导致“看不见文字”）
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["普通 📝", "重要 ⭐", "紧急 🔥"])
        self.priority_combo.setFixedSize(92, 40)
        self.priority_combo.setToolTip("优先级")
        self.priority_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0; border-radius: 6px;
                padding: 4px; font-size: 14px; background: white;
            }
            QComboBox:hover { border-color: #007bff; }
            QComboBox::drop-down { border: none; width: 16px; }
        """)
        input_row.addWidget(self.priority_combo)
        
        # 提醒按钮
        self.reminder_btn = QPushButton("⏰")
        self.reminder_btn.setFixedSize(40, 40)
        self.reminder_btn.setToolTip("设置提醒")
        self.reminder_btn.setCheckable(True)
        self.reminder_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; border: 1px solid #e0e0e0;
                border-radius: 6px; background: white;
            }
            QPushButton:hover { border-color: #007bff; background: #f0f7ff; }
            QPushButton:checked { border-color: #28a745; background: #d4edda; }
        """)
        self.reminder_btn.clicked.connect(self._toggle_reminder)
        input_row.addWidget(self.reminder_btn)
        
        # 添加按钮
        add_btn = QPushButton("➕")
        add_btn.setFixedSize(40, 40)
        add_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; border: none; border-radius: 6px;
                background-color: #007bff; color: white;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        add_btn.clicked.connect(self._add_item)
        input_row.addWidget(add_btn)
        
        input_layout.addLayout(input_row)
        
        # 提醒设置行（保持布局占位，避免显示/隐藏导致输入区域高度变化）
        self.reminder_row = QWidget()
        self.reminder_row.setVisible(False)
        self.reminder_row.setFixedHeight(36)
        reminder_layout = QHBoxLayout(self.reminder_row)
        reminder_layout.setContentsMargins(0, 0, 0, 0)
        reminder_layout.setSpacing(6)
        
        # 日期/时间分开设置
        self.reminder_date_edit = QDateTimeEdit()
        self.reminder_date_edit.setDateTime(datetime.now() + timedelta(hours=1))
        self.reminder_date_edit.setCalendarPopup(True)
        self.reminder_date_edit.setDisplayFormat("MM/dd")
        self.reminder_date_edit.setFixedSize(110, 36)
        self.reminder_date_edit.setStyleSheet("""
            QDateTimeEdit {
                border: 1px solid #e0e0e0; border-radius: 6px;
                padding: 4px 8px; font-size: 13px; background: white;
            }
            QDateTimeEdit::drop-down { border: none; width: 18px; }
        """)
        reminder_layout.addWidget(self.reminder_date_edit)

        self.reminder_time_edit = QTimeEdit()
        self.reminder_time_edit.setDisplayFormat("HH:mm")
        self.reminder_time_edit.setFixedHeight(36)
        self.reminder_time_edit.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)
        self.reminder_time_edit.setStyleSheet("""
            QTimeEdit {
                border: 1px solid #e0e0e0; border-radius: 6px;
                padding: 4px 8px; font-size: 13px; background: white;
            }
        """)
        reminder_layout.addWidget(self.reminder_time_edit)
        
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["不重复", "每天", "每周", "每月"])
        self.repeat_combo.setFixedSize(90, 36)
        self.repeat_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0; border-radius: 6px;
                padding: 4px 8px; font-size: 13px; background: white;
            }
            QComboBox::drop-down { border: none; width: 18px; }
        """)
        reminder_layout.addWidget(self.repeat_combo)

        # 多个提醒铃声（可选），默认第一个
        self.sound_combo = QComboBox()
        self.sound_combo.addItems([
            "默认铃声",
            "清脆铃声",
            "急促铃声",
            "静音",
        ])
        self.sound_combo.setFixedSize(110, 36)
        self.sound_combo.setToolTip("提醒铃声")
        self.sound_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0; border-radius: 6px;
                padding: 4px 8px; font-size: 13px; background: white;
            }
            QComboBox::drop-down { border: none; width: 18px; }
        """)
        reminder_layout.addWidget(self.sound_combo)
        reminder_layout.addStretch()
        
        input_layout.addWidget(self.reminder_row)
        layout.addWidget(input_frame)
        
        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa; border: none;
                border-radius: 8px; padding: 4px;
            }
            QListWidget::item {
                background-color: white; border-radius: 6px;
                margin: 2px 0; padding: 0px;
            }
            QListWidget::item:hover { background-color: #f0f7ff; }
            QListWidget::item:selected { background-color: #e3f2fd; }
        """)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setSpacing(1)
        layout.addWidget(self.list_widget)
        
        self._refresh_list()
    
    def _toggle_reminder(self):
        is_checked = self.reminder_btn.isChecked()
        self.reminder_row.setVisible(is_checked)
        # 关键：不让输入框区域高度变化
        self.reminder_row.setMaximumHeight(36 if is_checked else 0)
        if is_checked:
            init_dt = datetime.now() + timedelta(hours=1)
            self.reminder_date_edit.setDateTime(init_dt)
            self.reminder_time_edit.setTime(init_dt.time())
            self.repeat_combo.setCurrentIndex(0)
            self.sound_combo.setCurrentIndex(0)
    
    def _add_item(self):
        content = self.input_edit.text().strip()
        if not content:
            return
        
        priority = self.priority_combo.currentIndex()
        reminder_enabled = self.reminder_btn.isChecked()
        reminder_datetime = None
        reminder_repeat = "none"
        
        if reminder_enabled:
            base = self.reminder_date_edit.dateTime().toPyDateTime()
            t = self.reminder_time_edit.time()
            reminder_datetime = base.replace(hour=t.hour(), minute=t.minute(), second=0, microsecond=0)
            repeat_map = {0: "none", 1: "daily", 2: "weekly", 3: "monthly"}
            reminder_repeat = repeat_map.get(self.repeat_combo.currentIndex(), "none")
            self._last_sound_mode = self.sound_combo.currentIndex()
        
        memo_storage.add_item(
            content=content, priority=priority,
            reminder_enabled=reminder_enabled,
            reminder_datetime=reminder_datetime,
            reminder_repeat=reminder_repeat,
        )
        
        self.input_edit.clear()
        self.priority_combo.setCurrentIndex(0)
        self.reminder_btn.setChecked(False)
        self.reminder_row.setVisible(False)
        self.reminder_row.setMaximumHeight(0)
        self._refresh_list()
    
    def _refresh_list(self):
        self.list_widget.clear()
        
        filter_idx = self.filter_combo.currentIndex()
        if filter_idx == 0:
            items = memo_storage.get_all_items()
        elif filter_idx == 1:
            items = memo_storage.get_pending_items()
        elif filter_idx == 2:
            items = memo_storage.get_completed_items()
        else:
            items = [i for i in memo_storage.get_all_items() if i.reminder_enabled]
        
        def sort_key(x):
            rt = x.reminder_datetime.timestamp() if x.reminder_datetime else float('inf')
            return (x.completed, -x.priority, rt, x.created_at)
        
        items = sorted(items, key=sort_key)
        
        for item in items:
            self._add_list_item(item)
        
        stats = memo_storage.get_statistics()
        reminder_str = f" | ⏰{stats['with_reminder']}" if stats['with_reminder'] > 0 else ""
        self.stats_label.setText(f"📋 待办 {stats['pending']} | 完成 {stats['completed']}{reminder_str}")
    
    def _add_list_item(self, item: MemoItem):
        widget = QWidget()
        has_reminder = item.reminder_enabled and item.reminder_datetime
        # 每个待办项保持一致高度，不因提醒信息变高
        # 高度按截图（主行 + 提醒行）固定
        widget.setFixedHeight(64)
        
        main_layout = QVBoxLayout(widget)
        # 预留第二行区域（提醒时间），无提醒时占位为空白
        main_layout.setContentsMargins(12, 6, 12, 6)
        main_layout.setSpacing(2)
        
        # 主行
        row = QHBoxLayout()
        row.setSpacing(8)
        
        # 完成按钮
        check_btn = QPushButton("✓" if item.completed else "○")
        check_btn.setFixedSize(28, 28)
        if item.completed:
            check_btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px; border: none; border-radius: 14px;
                    background-color: #28a745; color: white;
                }
                QPushButton:hover { background-color: #218838; }
            """)
        else:
            check_btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px; border: 2px solid #ddd; border-radius: 14px;
                    background-color: white; color: #ddd;
                }
                QPushButton:hover { border-color: #28a745; color: #28a745; }
            """)
        check_btn.clicked.connect(lambda: self._toggle_complete(item.id))
        row.addWidget(check_btn)
        
        # 优先级
        priority_label = QLabel(item.get_priority_icon())
        priority_label.setFixedWidth(22)
        priority_label.setStyleSheet("font-size: 16px;")
        row.addWidget(priority_label)
        
        # 内容
        content = item.content
        if len(content) > 28:
            content = content[:26] + "..."
        content_label = QLabel(content)
        content_label.setWordWrap(False)
        # 让文字无论文本框高度如何都会垂直居中
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if item.completed:
            content_label.setStyleSheet("""
                font-size: 14px; color: #999; text-decoration: line-through;
                padding: 0px; margin: 0px; line-height: 28px;
            """)
        else:
            content_label.setStyleSheet("""
                font-size: 14px; color: #333;
                padding: 0px; margin: 0px; line-height: 28px;
            """)
        content_label.setToolTip(item.content)
        content_label.setFixedHeight(28)  # 固定高度确保垂直居中
        row.addWidget(content_label)
        
        row.addStretch()
        
        # 提醒按钮
        reminder_btn = QPushButton("⏰" if has_reminder else "🔔")
        reminder_btn.setFixedSize(28, 28)
        reminder_btn.setToolTip(item.format_reminder_time() if has_reminder else "添加提醒")
        reminder_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; border: none; border-radius: 14px;
                background-color: transparent; color: #999;
            }
            QPushButton:hover { background-color: #e3f2fd; color: #007bff; }
        """)
        reminder_btn.clicked.connect(lambda: self._edit_reminder(item.id))
        row.addWidget(reminder_btn)
        
        # 删除按钮
        del_btn = QPushButton("×")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; border: none; border-radius: 14px;
                background-color: transparent; color: #ccc;
            }
            QPushButton:hover { background-color: #ffebee; color: #dc3545; }
        """)
        del_btn.clicked.connect(lambda: self._delete_item(item.id))
        row.addWidget(del_btn)
        
        main_layout.addLayout(row)

        # 提醒信息行：始终占位，避免有无提醒导致高度变化
        reminder_text = item.format_reminder_time() if has_reminder else ""
        reminder_info = QLabel(reminder_text)
        reminder_info.setFixedHeight(16)
        reminder_info.setStyleSheet("font-size: 11px; color: #17a2b8; margin-left: 48px;")
        main_layout.addWidget(reminder_info)
        
        list_item = QListWidgetItem()
        list_item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, widget)
    
    def _toggle_complete(self, item_id: str):
        memo_storage.toggle_complete(item_id)
        self._refresh_list()
    
    def _delete_item(self, item_id: str):
        memo_storage.delete_item(item_id)
        self._refresh_list()
    
    def _edit_reminder(self, item_id: str):
        item = None
        for i in memo_storage.items:
            if i.id == item_id:
                item = i
                break
        
        if not item:
            return
        
        dialog = ReminderDialog(self, item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            enabled, dt, repeat = dialog.get_values()
            memo_storage.update_item(
                item_id,
                reminder_enabled=enabled,
                reminder_datetime=dt,
                reminder_repeat=repeat
            )
            self._refresh_list()
    
    def _clear_completed(self):
        count = len(memo_storage.get_completed_items())
        if count == 0:
            QMessageBox.information(self, "提示", "没有已完成的待办事项")
            return
        
        reply = QMessageBox.question(
            self, "确认清理",
            f"确定要清理 {count} 个已完成的待办事项吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            memo_storage.clear_completed()
            self._refresh_list()
    
    def _check_reminders(self):
        """检查到期提醒"""
        due_items = memo_storage.get_due_reminders()
        for item in due_items:
            self._show_reminder(item)
            memo_storage.mark_reminder_notified(item.id)
        
        if due_items:
            self._refresh_list()
    
    def _show_reminder(self, item: MemoItem):
        """显示提醒"""
        # 播放提示音
        def play_sound():
            # 多种铃声模式：根据 sound_combo 的选择决定频率/节奏
            try:
                duration_ms = 3000
                end_time = datetime.now() + timedelta(milliseconds=duration_ms)

                # 0: 默认铃声 1: 清脆铃声 2: 急促铃声 3: 静音
                sound_mode = getattr(self, "_last_sound_mode", 0)
                if sound_mode == 3:
                    return

                while datetime.now() < end_time:
                    if sound_mode == 2:
                        winsound.Beep(1400, 120)
                        winsound.Beep(1600, 120)
                    elif sound_mode == 1:
                        winsound.Beep(1200, 220)
                        winsound.Beep(1500, 220)
                    else:
                        winsound.Beep(1000, 250)
                        winsound.Beep(1200, 250)
            except Exception:
                pass
        threading.Thread(target=play_sound, daemon=True).start()
        
        # 显示消息
        QMessageBox.information(
            self, "⏰ 待办提醒",
            f"📋 {item.content}\n\n{item.get_priority_icon()} {item.get_priority_name()}"
        )
        
        self.reminder_triggered.emit(item.id, item.content)