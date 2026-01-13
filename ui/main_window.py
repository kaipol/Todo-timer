"""
主窗口模块 - 应用主界面（方形整合布局）
"""
import os
import winsound
import threading
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QScrollArea, QPushButton,
                             QSpinBox, QMessageBox, QApplication, QProgressBar,
                             QLineEdit, QListWidget, QListWidgetItem, QTabWidget,
                             QGridLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
                             QHeaderView, QGraphicsBlurEffect, QStackedLayout,
                             QComboBox, QDateTimeEdit, QDialog, QInputDialog)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QPalette

from core.monitor import AppMonitor
from core.config import app_config
from core.storage import timer_storage, TimerRecord, app_usage_storage, memo_storage, diary_storage
from core.utils import get_icon_from_exe, format_time
from core.webdav_sync import webdav_sync
from ui.widgets import MiniWindow, AppListItem
from ui.settings_dialog import SettingsDialog
from ui.memo_widget import MemoWidget, ReminderDialog, TodayMemoWidget
from ui.diary import DiaryWidget, TodayDiaryWidget


class MainWindow(QMainWindow):
    """应用程序主窗口 - 方形整合布局"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Tracker")
        self.resize(1100, 750)  # 扩大窗口尺寸以完整显示文字
        
        # 窗口置顶状态
        self.is_always_on_top = False
        
        # 窗口样式：无边框、圆角
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        self._setup_timer()
        self._setup_monitor()
        
        # 拖拽窗口支持
        self.old_pos = None
        
        # 迷你窗口
        self.mini_window = MiniWindow()
        self.mini_window.restore_signal.connect(self.restore_from_mini)
        
        # 当前数据缓存
        self.current_data = None
        
        # 定时保存应用使用数据
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._auto_save_usage)
        self.save_timer.start(60000)  # 每分钟保存一次

    def _setup_ui(self):
        """设置 UI - 左右分栏布局"""
        # 根容器 - 用于承载背景和内容
        self.root_widget = QWidget()
        self.root_widget.setObjectName("RootWidget")
        self.setCentralWidget(self.root_widget)
        
        # 根布局
        root_layout = QVBoxLayout(self.root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # 背景层 - 使用绝对定位
        self.bg_layer = QLabel(self.root_widget)
        self.bg_layer.setObjectName("BackgroundLayer")
        self.bg_layer.setScaledContents(True)
        self.bg_layer.lower()  # 确保在最底层
        
        # 主容器
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainContainer")
        root_layout.addWidget(self.central_widget)
        
        # 应用背景样式
        self._apply_global_background()
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(18, 15, 18, 15)
        main_layout.setSpacing(12)
        
        # 顶部标题栏
        self._setup_title_bar(main_layout)
        
        # 主内容区域（左右分栏）
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # 左侧面板
        left_panel = self._create_left_panel()
        content_layout.addWidget(left_panel, stretch=1)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        separator.setFixedWidth(1)
        content_layout.addWidget(separator)
        
        # 右侧面板
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout)

    def _setup_title_bar(self, parent_layout):
        """设置标题栏"""
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        title = QLabel("⏱ Time Tracker")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        top_bar.addWidget(title)
        
        # 日期显示
        self.date_label = QLabel()
        self._update_date_label()
        self.date_label.setStyleSheet("font-size: 13px; color: #666;")
        top_bar.addWidget(self.date_label)
        
        top_bar.addStretch()
        
        # 设置按钮
        self.settings_btn = self._create_title_btn("⚙", "#28a745", "个性化设置")
        self.settings_btn.mousePressEvent = lambda e: self.open_settings()
        top_bar.addWidget(self.settings_btn)
        
        # 置顶按钮
        self.pin_btn = self._create_title_btn("📌", "#007bff", "固定在最前台")
        self.pin_btn.mousePressEvent = lambda e: self.toggle_always_on_top()
        top_bar.addWidget(self.pin_btn)
        
        # 最小化按钮
        self.minimize_btn = self._create_title_btn("—", "#17a2b8", "最小化为悬浮条")
        self.minimize_btn.mousePressEvent = lambda e: self.minimize_to_mini()
        top_bar.addWidget(self.minimize_btn)
        
        # 关闭按钮
        close_btn = self._create_title_btn("×", "#dc3545", "关闭程序")
        close_btn.mousePressEvent = lambda e: self.close()
        top_bar.addWidget(close_btn)
        
        parent_layout.addLayout(top_bar)
    
    def _create_title_btn(self, text, hover_color, tooltip):
        """创建标题栏按钮"""
        btn = QLabel(text)
        btn.setFixedSize(32, 32)
        btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                color: #999;
                background-color: transparent;
                border: 2px solid #ddd;
                border-radius: 6px;
            }}
            QLabel:hover {{
                color: {hover_color};
                border-color: {hover_color};
            }}
        """)
        btn.setToolTip(tooltip)
        return btn
    
    def _update_date_label(self):
        """更新日期显示"""
        now = datetime.now()
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        self.date_label.setText(f"{now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]}")

    def _create_left_panel(self):
        """创建左侧面板（计时器+当前应用+记录）"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 当前应用区域
        self._setup_current_app_area(layout)
        
        # 计时器区域
        self._setup_timer_area(layout)
        
        # 今日记录
        self._setup_history_area(layout)
        
        layout.addStretch()
        return panel
    
    def _create_right_panel(self):
        """创建右侧面板（日历+统计）"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 使用标签页组织
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #f0f0f0;
                padding: 10px 18px;
                margin-right: 4px;
                border-radius: 8px 8px 0 0;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #e8f4ff;
                font-weight: bold;
                color: #007bff;
            }
            QTabBar::tab:hover {
                background: #e0e0e0;
            }
        """)
        
        # 应用统计标签页
        apps_tab = self._create_apps_tab()
        self.right_tabs.addTab(apps_tab, "📱 应用")

        # 日历标签页
        calendar_tab = self._create_calendar_tab()
        self.right_tabs.addTab(calendar_tab, "📅 日历")

        # 备忘录标签页
        self.memo_widget = MemoWidget()
        self.right_tabs.addTab(self.memo_widget, "📋 备忘录")

        # 日记标签页
        self.diary_widget = DiaryWidget()
        self.right_tabs.addTab(self.diary_widget, "📔 日记")

        # 周统计标签页
        weekly_tab = self._create_weekly_tab()
        self.right_tabs.addTab(weekly_tab, "📊 周统计")
        
        layout.addWidget(self.right_tabs)
        
        # 连接数据变更信号，实现今日待办与备忘录的同步
        self.today_memo_widget.data_changed.connect(self.memo_widget._refresh_list)
        self.memo_widget.data_changed.connect(self.today_memo_widget._refresh_list)
        
        return panel

    def _setup_current_app_area(self, parent_layout):
        """设置当前应用展示区域"""
        self.current_app_frame = QFrame()
        self.current_app_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 12px;
            }
        """)
        curr_layout = QHBoxLayout(self.current_app_frame)
        curr_layout.setContentsMargins(14, 12, 14, 12)
        curr_layout.setSpacing(14)
        
        # 图标 - 增大尺寸
        self.curr_icon = QLabel()
        self.curr_icon.setFixedSize(56, 56)
        self.curr_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.curr_icon.setStyleSheet("background-color: #e9ecef; border-radius: 12px; font-size: 24px;")
        curr_layout.addWidget(self.curr_icon)
        
        # 应用信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        self.curr_name = QLabel("等待中...")
        self.curr_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        info_layout.addWidget(self.curr_name)
        
        self.curr_sub_title = QLabel("")
        self.curr_sub_title.setStyleSheet("font-size: 12px; color: #666;")
        self.curr_sub_title.hide()
        info_layout.addWidget(self.curr_sub_title)
        
        curr_layout.addLayout(info_layout)
        curr_layout.addStretch()
        
        # 计时 - 增大字体
        self.curr_timer = QLabel("00:00:00")
        self.curr_timer.setStyleSheet("font-size: 28px; font-weight: bold; color: #007bff;")
        curr_layout.addWidget(self.curr_timer)
        
        parent_layout.addWidget(self.current_app_frame)

    def _setup_timer_area(self, parent_layout):
        """设置计时器区域"""
        self.timer_frame = QFrame()
        self.timer_frame.setObjectName("TimerFrame")
        self._apply_timer_background()
        timer_layout = QVBoxLayout(self.timer_frame)
        timer_layout.setContentsMargins(16, 12, 16, 12)
        timer_layout.setSpacing(8)
        
        # 计时器模式
        self.timer_mode = 'countdown'
        
        # 模式切换 + 状态
        mode_row = QHBoxLayout()
        mode_row.setSpacing(0)
        
        self.countdown_tab = QPushButton("🍅 番茄钟")
        self.countdown_tab.setFixedHeight(32)
        self.countdown_tab.clicked.connect(lambda: self.switch_timer_mode('countdown'))
        
        self.stopwatch_tab = QPushButton("⏱ 正计时")
        self.stopwatch_tab.setFixedHeight(32)
        self.stopwatch_tab.clicked.connect(lambda: self.switch_timer_mode('stopwatch'))
        
        self._update_tab_styles()
        
        mode_row.addWidget(self.countdown_tab)
        mode_row.addWidget(self.stopwatch_tab)
        mode_row.addStretch()
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.5); font-weight: bold;")
        mode_row.addWidget(self.status_indicator)
        
        self.timer_status_label = QLabel("准备开始")
        self.timer_status_label.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.85); font-weight: bold;")
        mode_row.addWidget(self.timer_status_label)
        timer_layout.addLayout(mode_row)
        
        # 计时器显示
        self.countdown_label = QLabel("25:00")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("""
            font-size: 42px;
            font-weight: bold;
            color: white;
            font-family: 'Microsoft YaHei', 'Arial', sans-serif;
        """)
        timer_layout.addWidget(self.countdown_label)
        
        # 进度条
        self.timer_progress = QProgressBar()
        self.timer_progress.setRange(0, 100)
        self.timer_progress.setValue(100)
        self.timer_progress.setTextVisible(False)
        self.timer_progress.setFixedHeight(4)
        self.timer_progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 2px;
            }
        """)
        timer_layout.addWidget(self.timer_progress)
        
        # 时间设置行
        self.time_setting_row = QWidget()
        time_setting_layout = QHBoxLayout(self.time_setting_row)
        time_setting_layout.setContentsMargins(0, 0, 0, 0)
        time_setting_layout.setSpacing(6)
        time_setting_layout.addStretch()
        
        spinbox_style = """
            QSpinBox {
                font-size: 14px;
                padding: 6px 10px;
                border: none;
                border-radius: 6px;
                background: rgba(255,255,255,0.15);
                color: white;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
            }
        """
        
        self.minutes_spinbox = QSpinBox()
        self.minutes_spinbox.setRange(0, 120)
        self.minutes_spinbox.setValue(25)
        self.minutes_spinbox.setSuffix(" 分")
        self.minutes_spinbox.setFixedWidth(75)
        self.minutes_spinbox.setStyleSheet(spinbox_style)
        self.minutes_spinbox.valueChanged.connect(self._on_time_setting_changed)
        time_setting_layout.addWidget(self.minutes_spinbox)
        
        self.seconds_spinbox = QSpinBox()
        self.seconds_spinbox.setRange(0, 59)
        self.seconds_spinbox.setValue(0)
        self.seconds_spinbox.setSuffix(" 秒")
        self.seconds_spinbox.setFixedWidth(75)
        self.seconds_spinbox.setStyleSheet(spinbox_style)
        self.seconds_spinbox.valueChanged.connect(self._on_time_setting_changed)
        time_setting_layout.addWidget(self.seconds_spinbox)
        
        time_setting_layout.addStretch()
        timer_layout.addWidget(self.time_setting_row)
        
        # 备注输入
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("📝 输入备注...")
        self.note_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 10px 14px;
                border: none;
                border-radius: 8px;
                background: rgba(255,255,255,0.15);
                color: white;
            }
            QLineEdit::placeholder {
                color: rgba(255,255,255,0.5);
            }
        """)
        timer_layout.addWidget(self.note_input)
        
        # 控制按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()
        
        self.start_btn = QPushButton("▶")
        self.start_btn.setFixedSize(50, 50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                border: none;
                border-radius: 25px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #667eea;
                font-weight: bold;
            }
            QPushButton:hover { background-color: white; }
        """)
        self.start_btn.clicked.connect(self.toggle_timer)
        btn_row.addWidget(self.start_btn)
        
        self.reset_btn = QPushButton("↺")
        self.reset_btn.setFixedSize(40, 40)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 20px;
                background-color: transparent;
                color: white;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }
        """)
        self.reset_btn.clicked.connect(self.reset_countdown)
        btn_row.addWidget(self.reset_btn)
        
        btn_row.addStretch()
        timer_layout.addLayout(btn_row)
        
        parent_layout.addWidget(self.timer_frame)
        
        # 初始化计时变量
        self.initial_countdown_seconds = 25 * 60
        self.timer_history = []

    def _setup_history_area(self, parent_layout):
        """设置计时历史区域"""
        history_header = QHBoxLayout()
        history_title = QLabel("📋 今日计时")
        history_title.setStyleSheet("font-size: 16px; color: #6c757d; font-weight: bold;")
        history_header.addWidget(history_title)
        history_header.addStretch()
        parent_layout.addLayout(history_header)
        
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(100)
        self.history_list.setMaximumHeight(150)
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: none;
                border-radius: 10px;
                padding: 8px;
                font-size: 15px;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 8px;
                margin: 3px 0;
                padding: 12px;
                color: #333;
                font-weight: 500;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #d0e8ff;
                color: #333;
            }
        """)
        # 启用平滑滚动
        self.history_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        parent_layout.addWidget(self.history_list)
        
        # 加载今日记录
        self._load_today_history()

    def _create_calendar_tab(self):
        """创建日历标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        # 简化的日历
        self._setup_calendar(layout)
        
        # 选中日期的记录
        self._setup_day_records(layout)
        
        return tab

    def _setup_calendar(self, parent_layout):
        """设置日历组件"""
        self.current_date = datetime.now().date()
        self.selected_date = self.current_date
        self.displayed_month = self.current_date.replace(day=1)
        
        # 月份导航
        nav_layout = QHBoxLayout()
        
        self.prev_month_btn = QPushButton("◀")
        self.prev_month_btn.setFixedSize(32, 32)
        self.prev_month_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #f0f0f0;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        self.prev_month_btn.clicked.connect(self._prev_month)
        nav_layout.addWidget(self.prev_month_btn)
        
        nav_layout.addStretch()
        
        self.month_label = QLabel()
        self.month_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        nav_layout.addWidget(self.month_label)
        
        nav_layout.addStretch()
        
        self.next_month_btn = QPushButton("▶")
        self.next_month_btn.setFixedSize(32, 32)
        self.next_month_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #f0f0f0;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        self.next_month_btn.clicked.connect(self._next_month)
        nav_layout.addWidget(self.next_month_btn)
        
        parent_layout.addLayout(nav_layout)
        
        # 今日使用时间统计行
        today_stats_layout = QHBoxLayout()
        today_stats_layout.setSpacing(8)
        
        today_label = QLabel("📊 今日使用:")
        today_label.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        today_stats_layout.addWidget(today_label)
        
        self.today_usage_label = QLabel("0h 0m")
        self.today_usage_label.setStyleSheet("font-size: 14px; color: #17a2b8; font-weight: bold;")
        today_stats_layout.addWidget(self.today_usage_label)
        
        today_stats_layout.addStretch()
        parent_layout.addLayout(today_stats_layout)
        
        # 星期标题
        week_layout = QHBoxLayout()
        week_layout.setSpacing(4)
        for day in ['一', '二', '三', '四', '五', '六', '日']:
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedHeight(24)
            label.setStyleSheet("color: #666; font-size: 13px; font-weight: bold;")
            week_layout.addWidget(label)
        parent_layout.addLayout(week_layout)
        
        # 日历网格
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(4)
        parent_layout.addLayout(self.calendar_grid)
        
        self.day_buttons = []
        self._day_button_dates = {}  # 按钮到日期的映射
        self._last_calendar_month = None  # 缓存上次显示的月份
        
        # 预缓存日历按钮样式
        self._init_calendar_styles()
        
        self._update_calendar()
    
    def _init_calendar_styles(self):
        """初始化日历按钮样式缓存"""
        base_style = """
            QPushButton {{
                border: none;
                border-radius: 19px;
                font-size: 14px;
                {style}
            }}
            QPushButton:hover {{
                background: #d0e8ff;
                color: #333;
            }}
        """
        self._calendar_styles = {
            'selected': base_style.format(style="background: #d0e8ff; color: #007bff; font-weight: bold; border: 2px solid #007bff;"),
            'today': base_style.format(style="border: 2px solid #007bff; background: white; color: #007bff; font-weight: bold;"),
            'has_record': base_style.format(style="background: #e8f4ff; color: #333;"),
            'current_month': base_style.format(style="background: transparent; color: #333;"),
            'other_month': base_style.format(style="background: transparent; color: #ccc;"),
        }
    
    def _update_calendar(self):
        """更新日历显示 - 优化版本，复用按钮"""
        month_changed = self._last_calendar_month != self.displayed_month
        self._last_calendar_month = self.displayed_month
        
        self.month_label.setText(self.displayed_month.strftime("%Y年%m月"))
        
        # 获取有记录的日期
        dates_with_records = timer_storage.get_dates_with_records()
        dates_with_usage = app_usage_storage.get_dates_with_usage()
        dates_with_records = dates_with_records.union(dates_with_usage)
        
        first_day = self.displayed_month
        first_weekday = first_day.weekday()
        
        if self.displayed_month.month == 12:
            next_month = self.displayed_month.replace(year=self.displayed_month.year + 1, month=1)
        else:
            next_month = self.displayed_month.replace(month=self.displayed_month.month + 1)
        days_in_month = (next_month - self.displayed_month).days
        
        # 计算需要的按钮总数
        total_buttons_needed = first_weekday + days_in_month
        # 补齐到完整的行
        remaining = total_buttons_needed % 7
        if remaining > 0:
            total_buttons_needed += (7 - remaining)
        
        # 如果月份改变或按钮数量不足，需要重建
        if month_changed or len(self.day_buttons) != total_buttons_needed:
            # 清除旧按钮
            for btn in self.day_buttons:
                btn.deleteLater()
            self.day_buttons.clear()
            self._day_button_dates.clear()
            
            # 创建新按钮
            for i in range(total_buttons_needed):
                btn = QPushButton()
                btn.setFixedSize(38, 38)
                row, col = divmod(i, 7)
                self.calendar_grid.addWidget(btn, row, col)
                self.day_buttons.append(btn)
        
        # 更新按钮内容和样式
        btn_index = 0
        
        # 填充上月日期
        if first_weekday > 0:
            prev_month_end = first_day - timedelta(days=1)
            for i in range(first_weekday - 1, -1, -1):
                d = prev_month_end - timedelta(days=i)
                self._update_day_button(btn_index, d, False, d in dates_with_records, False, False)
                btn_index += 1
        
        # 填充当月日期
        for day in range(1, days_in_month + 1):
            d = self.displayed_month.replace(day=day)
            is_today = d == self.current_date
            is_selected = d == self.selected_date
            has_record = d in dates_with_records
            self._update_day_button(btn_index, d, True, has_record, is_today, is_selected)
            btn_index += 1
        
        # 填充下月日期
        next_day = next_month
        while btn_index < len(self.day_buttons):
            self._update_day_button(btn_index, next_day, False, next_day in dates_with_records, False, False)
            btn_index += 1
            next_day += timedelta(days=1)
    
    def _update_day_button(self, index, date, is_current_month=True, has_record=False,
                           is_today=False, is_selected=False):
        """更新日期按钮 - 复用现有按钮"""
        btn = self.day_buttons[index]
        
        # 更新文本（仅在变化时）
        day_text = str(date.day)
        if btn.text() != day_text:
            btn.setText(day_text)
        
        # 更新日期映射
        old_date = self._day_button_dates.get(index)
        if old_date != date:
            self._day_button_dates[index] = date
            # 重新连接点击事件
            try:
                btn.clicked.disconnect()
            except:
                pass
            btn.clicked.connect(lambda checked, d=date: self._on_date_clicked(d))
        
        # 选择合适的样式
        if is_selected:
            style_key = 'selected'
        elif is_today:
            style_key = 'today'
        elif has_record:
            style_key = 'has_record'
        elif is_current_month:
            style_key = 'current_month'
        else:
            style_key = 'other_month'
        
        # 仅在样式变化时更新
        current_style_key = btn.property('style_key')
        if current_style_key != style_key:
            btn.setStyleSheet(self._calendar_styles[style_key])
            btn.setProperty('style_key', style_key)
    
    def _create_day_button(self, date, is_current_month=True, has_record=False,
                           is_today=False, is_selected=False):
        """创建日期按钮 - 保留用于兼容性"""
        btn = QPushButton(str(date.day))
        btn.setFixedSize(38, 38)
        btn.clicked.connect(lambda: self._on_date_clicked(date))
        
        if is_selected:
            style_key = 'selected'
        elif is_today:
            style_key = 'today'
        elif has_record:
            style_key = 'has_record'
        elif is_current_month:
            style_key = 'current_month'
        else:
            style_key = 'other_month'
        
        btn.setStyleSheet(self._calendar_styles[style_key])
        btn.setProperty('style_key', style_key)
        return btn
    
    def _on_date_clicked(self, date):
        """日期点击"""
        self.selected_date = date
        self._update_calendar()
        self._load_day_records(date)
    
    def _prev_month(self):
        """上一月"""
        if self.displayed_month.month == 1:
            self.displayed_month = self.displayed_month.replace(year=self.displayed_month.year - 1, month=12)
        else:
            self.displayed_month = self.displayed_month.replace(month=self.displayed_month.month - 1)
        self._update_calendar()
    
    def _next_month(self):
        """下一月"""
        if self.displayed_month.month == 12:
            self.displayed_month = self.displayed_month.replace(year=self.displayed_month.year + 1, month=1)
        else:
            self.displayed_month = self.displayed_month.replace(month=self.displayed_month.month + 1)
        self._update_calendar()

    def _setup_day_records(self, parent_layout):
        """设置日期记录显示"""
        # 标题行：左侧日期标题 + 右侧清理按钮（保持原布局逻辑）
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.day_records_label = QLabel("📅 今天")
        self.day_records_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        header_layout.addWidget(self.day_records_label)

        header_layout.addStretch()

        # 清理按钮
        self.clear_day_btn = QPushButton("🗑️ 清理")
        self.clear_day_btn.setFixedHeight(28)
        self.clear_day_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #f8d7da;
                color: #721c24;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #f5c6cb;
            }
        """)
        self.clear_day_btn.clicked.connect(self._clear_day_records)
        header_layout.addWidget(self.clear_day_btn)

        parent_layout.addLayout(header_layout)

        # 内容区：用 Tab 在“今日应用/今日待办”之间切换（默认今日应用）
        self.day_detail_tabs = QTabWidget()
        self.day_detail_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #f0f0f0;
                padding: 8px 14px;
                margin-right: 4px;
                border-radius: 8px 8px 0 0;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #f8f9fa;
                font-weight: bold;
                color: #007bff;
            }
            QTabBar::tab:hover {
                background: #e0e0e0;
            }
        """)
        self.day_detail_tabs.currentChanged.connect(lambda idx: self._refresh_today_todo_tab())

        # Tab 1：今日应用（沿用原 day_records_list）
        apps_tab = QWidget()
        apps_layout = QVBoxLayout(apps_tab)
        apps_layout.setContentsMargins(10, 6, 10, 10)
        apps_layout.setSpacing(10)

        self.day_records_list = QListWidget()
        self.day_records_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: none;
                border-radius: 10px;
                padding: 8px;
                font-size: 15px;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 8px;
                margin: 3px 0;
                padding: 12px;
                color: #333;
                font-weight: 500;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #d0e8ff;
                color: #333;
            }
        """)
        self.day_records_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        apps_layout.addWidget(self.day_records_list)

        # Tab 2：今日待办
        todos_tab = QWidget()
        todos_layout = QVBoxLayout(todos_tab)
        todos_layout.setContentsMargins(0, 0, 0, 0)
        todos_layout.setSpacing(8)

        self.today_memo_widget = TodayMemoWidget()
        todos_layout.addWidget(self.today_memo_widget)

        # Tab 3：今日日记
        diary_tab = QWidget()
        diary_layout = QVBoxLayout(diary_tab)
        diary_layout.setContentsMargins(0, 0, 0, 0)
        diary_layout.setSpacing(8)

        self.today_diary_widget = TodayDiaryWidget()
        diary_layout.addWidget(self.today_diary_widget)

        self.day_detail_tabs.addTab(apps_tab, "📱 今日应用")
        self.day_detail_tabs.addTab(todos_tab, "📌 今日待办")
        self.day_detail_tabs.addTab(diary_tab, "📔 今日日记")
        self.day_detail_tabs.setCurrentIndex(0)

        parent_layout.addWidget(self.day_detail_tabs)

        self._load_day_records(self.current_date)

    def _refresh_today_todo_tab(self):
        """切换Tab时刷新数据"""
        if not hasattr(self, 'day_detail_tabs'):
            return
        
        current_index = self.day_detail_tabs.currentIndex()
        
        # 今日待办
        if current_index == 1 and hasattr(self, 'today_memo_widget'):
            self.today_memo_widget.sync_with_date(datetime.now().date())
        
        # 今日日记
        if current_index == 2 and hasattr(self, 'today_diary_widget'):
            self.today_diary_widget.refresh()


    def _load_day_records(self, date):
        """加载日期记录"""
        if date == datetime.now().date():
            date_str = "今天"
        elif date == datetime.now().date() - timedelta(days=1):
            date_str = "昨天"
        else:
            date_str = date.strftime("%m月%d日")
        
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        self.day_records_label.setText(f"📅 {date_str} {weekdays[date.weekday()]}")

        # 同步刷新待办和日记 Tab（无论当前显示哪个 Tab，保持数据最新）
        if hasattr(self, 'today_memo_widget'):
            self.today_memo_widget.sync_with_date(datetime.now().date())
        if hasattr(self, 'today_diary_widget'):
            self.today_diary_widget.refresh()
        
        self.day_records_list.clear()
        
        # 计时记录
        records = timer_storage.get_records_by_date(date)
        if records:
            for r in reversed(records):
                text = f"{r.get_mode_icon()} {r.format_time()} | {r.format_duration()} | {r.note or '无备注'}"
                self.day_records_list.addItem(QListWidgetItem(text))
        
        # 应用使用记录 - 使用详细记录获取exe路径
        summary = app_usage_storage.get_daily_summary(date)
        app_records = summary.get('records', [])
        
        if app_records:
            if records:
                self.day_records_list.addItem(QListWidgetItem("─── 📱 应用使用 ───"))
            for app_record in app_records[:5]:
                name = app_record.app_name
                # 截断过长的应用名称
                if len(name) > 18:
                    name = name[:15] + "..."
                time_str = app_record.format_time()
                exe_path = app_record.exe_path
                
                # 创建带图标的列表项
                item = QListWidgetItem(f"  {name} | {time_str}")
                item.setToolTip(f"{app_record.app_name} | {time_str}")  # 鼠标悬停显示完整名称
                
                # 尝试获取应用图标
                if exe_path:
                    if exe_path not in self.icon_cache:
                        self.icon_cache[exe_path] = get_icon_from_exe(exe_path)
                    
                    icon = self.icon_cache.get(exe_path)
                    if icon:
                        item.setIcon(QIcon(icon))
                
                self.day_records_list.addItem(item)
        
        # 如果没有任何记录
        if not records and not app_records:
            self.day_records_list.addItem(QListWidgetItem("📭 暂无记录"))
    
    def _clear_day_records(self):
        """清理选中日期的所有记录"""
        date = self.selected_date
        
        if date == datetime.now().date():
            date_str = "今天"
        elif date == datetime.now().date() - timedelta(days=1):
            date_str = "昨天"
        else:
            date_str = date.strftime("%Y年%m月%d日")
        
        reply = QMessageBox.question(
            self, "确认清理",
            f"确定要清理 {date_str} 的所有记录吗？\n\n此操作将删除该日期的：\n• 计时记录\n• 应用使用记录\n\n⚠️ 此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除计时记录
            timer_count = timer_storage.delete_records_by_date(date)
            
            # 删除应用使用记录
            app_deleted = app_usage_storage.delete_daily_usage(date)
            
            # 刷新界面
            self._update_calendar()
            self._load_day_records(date)
            
            # 如果删除的是今天的记录，刷新今日历史
            if date == datetime.now().date():
                self.history_list.clear()
                self._load_today_history()
            
            # 刷新周统计
            self._load_weekly_data()
            
            QMessageBox.information(
                self, "清理完成",
                f"已清理 {date_str} 的记录：\n• 计时记录: {timer_count} 条\n• 应用使用记录: {'已删除' if app_deleted else '无'}"
            )

    def _create_weekly_tab(self):
        """创建周统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(8)
        
        # 周导航
        today = datetime.now().date()
        self.week_start = today - timedelta(days=today.weekday())
        
        nav = QHBoxLayout()
        self.prev_week_btn = QPushButton("◀ 上周")
        self.prev_week_btn.setStyleSheet("border: none; background: #f0f0f0; border-radius: 6px; padding: 6px 12px; font-size: 12px;")
        self.prev_week_btn.clicked.connect(self._prev_week)
        nav.addWidget(self.prev_week_btn)
        
        nav.addStretch()
        
        self.week_label = QLabel()
        self.week_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        nav.addWidget(self.week_label)
        
        nav.addStretch()
        
        self.next_week_btn = QPushButton("下周 ▶")
        self.next_week_btn.setStyleSheet("border: none; background: #f0f0f0; border-radius: 6px; padding: 6px 12px; font-size: 12px;")
        self.next_week_btn.clicked.connect(self._next_week)
        nav.addWidget(self.next_week_btn)
        
        layout.addLayout(nav)
        
        # 周总计统计卡片（放在最上面）
        self.weekly_total_frame = QFrame()
        self.weekly_total_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 12px;
            }
        """)
        total_layout = QHBoxLayout(self.weekly_total_frame)
        total_layout.setContentsMargins(16, 12, 16, 12)
        
        # 应用使用统计（左侧）
        app_col = QVBoxLayout()
        app_col.setSpacing(2)
        self.weekly_app_title = QLabel("📱 应用使用")
        self.weekly_app_title.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8); font-weight: bold;")
        app_col.addWidget(self.weekly_app_title)
        self.weekly_app_total_label = QLabel()
        self.weekly_app_total_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #17a2b8;")
        app_col.addWidget(self.weekly_app_total_label)
        self.weekly_app_detail_label = QLabel()
        self.weekly_app_detail_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.7);")
        app_col.addWidget(self.weekly_app_detail_label)
        total_layout.addLayout(app_col)
        
        total_layout.addStretch()
        
        # 计时统计（右侧）
        timer_col = QVBoxLayout()
        timer_col.setSpacing(2)
        self.weekly_timer_label = QLabel("🍅 计时统计")
        self.weekly_timer_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8); font-weight: bold;")
        timer_col.addWidget(self.weekly_timer_label)
        self.weekly_total_label = QLabel()
        self.weekly_total_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #6f42c1;")
        timer_col.addWidget(self.weekly_total_label)
        self.weekly_count_label = QLabel()
        self.weekly_count_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.7);")
        timer_col.addWidget(self.weekly_count_label)
        total_layout.addLayout(timer_col)
        
        layout.addWidget(self.weekly_total_frame)
        
        # 每日详情标题
        daily_title = QLabel("📅 每日详情（点击展开）")
        daily_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-top: 5px;")
        layout.addWidget(daily_title)
        
        # 每日详情（可展开的树形结构）
        self.weekly_tree = QTreeWidget()
        self.weekly_tree.setHeaderHidden(True)
        self.weekly_tree.setIndentation(15)
        self.weekly_tree.setAnimated(True)
        self.weekly_tree.setRootIsDecorated(False)  # 隐藏默认的展开图标，我们用文字图标

        # 交互体验：选中整行，禁用双击展开（我们改为单击展开）
        self.weekly_tree.setExpandsOnDoubleClick(False)
        self.weekly_tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.weekly_tree.setAllColumnsShowFocus(True)

        # 使用点击信号实现单击展开/折叠
        self.weekly_tree.itemClicked.connect(self._on_weekly_item_clicked)
        # 使用展开/折叠信号来跟踪状态（用于更新箭头图标）
        self.weekly_tree.itemExpanded.connect(self._on_weekly_item_expanded)
        self.weekly_tree.itemCollapsed.connect(self._on_weekly_item_collapsed)
        self.weekly_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #f8f9fa;
                border: none;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }
            QTreeWidget::item {
                background-color: white;
                border-radius: 6px;
                margin: 2px 0;
                padding: 10px 8px;
                color: #333;
                font-weight: 500;
            }
            QTreeWidget::item:hover {
                background-color: #e9ecef;
            }
            QTreeWidget::item:selected {
                background-color: #d0e8ff;
                color: #333;
            }
            QTreeWidget::branch {
                background: transparent;
            }
        """)
        layout.addWidget(self.weekly_tree)
        
        # 记录展开状态
        self.weekly_expanded_items = set()
        
        # 防止频繁刷新的标志和时间戳
        self._weekly_last_interaction = 0  # 上次用户交互的时间戳
        self._weekly_interaction_cooldown = 2.0  # 用户交互后的冷却时间（秒）
        
        self._load_weekly_data()
        return tab
    
    def _load_weekly_data(self, force_rebuild=False):
        """加载周数据
        
        Args:
            force_rebuild: 是否强制重建树（切换周时使用）
        """
        week_end = self.week_start + timedelta(days=6)
        today = datetime.now().date()
        current_week = today - timedelta(days=today.weekday())
        
        # 记录当前是否为本周
        self.is_current_week = (self.week_start == current_week)
        
        if self.week_start == current_week:
            self.week_label.setText("📆 本周")
        elif self.week_start == current_week - timedelta(days=7):
            self.week_label.setText("📆 上周")
        else:
            self.week_label.setText(f"📆 {self.week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}")
        
        # 获取应用使用统计
        app_summary = app_usage_storage.get_weekly_summary(self.week_start)
        app_total = app_summary.get('total_time', 0)
        app_hours, app_mins = app_total // 3600, (app_total % 3600) // 60
        self.weekly_app_total_label.setText(f"{app_hours}h{app_mins}m" if app_hours else f"{app_mins}分钟")
        
        app_active_days = app_summary.get('active_days', 0) or 1
        app_daily_avg = app_total // app_active_days
        app_avg_h, app_avg_m = app_daily_avg // 3600, (app_daily_avg % 3600) // 60
        app_avg_str = f"{app_avg_h}h{app_avg_m}m" if app_avg_h else f"{app_avg_m}m"
        self.weekly_app_detail_label.setText(f"日均 {app_avg_str}")
        
        # 获取计时统计
        timer_summary = timer_storage.get_weekly_summary(self.week_start)
        total = timer_summary['total_duration']
        hours, mins = total // 3600, (total % 3600) // 60
        self.weekly_total_label.setText(f"{hours}h{mins}m" if hours else f"{mins}分钟")
        
        # 计算日均
        active_days = timer_summary['active_days'] if timer_summary['active_days'] > 0 else 1
        daily_avg = total // active_days
        avg_h, avg_m = daily_avg // 3600, (daily_avg % 3600) // 60
        avg_str = f"{avg_h}h{avg_m}m" if avg_h else f"{avg_m}m"
        self.weekly_count_label.setText(f"{timer_summary['total_count']}次 · 日均 {avg_str}")
        
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        top_apps = app_summary.get('top_apps', [])
        
        # 检查是否需要重建树（树为空或强制重建）
        need_rebuild = force_rebuild or self.weekly_tree.topLevelItemCount() == 0
        
        if need_rebuild:
            # 完全重建树
            self._rebuild_weekly_tree(app_summary, timer_summary, weekdays, top_apps, today)
        else:
            # 增量更新现有项目
            self._update_weekly_tree(app_summary, timer_summary, weekdays, top_apps, today)
    
    def _rebuild_weekly_tree(self, app_summary, timer_summary, weekdays, top_apps, today):
        """完全重建周统计树"""
        # 阻塞信号以防止在重建树时触发展开/折叠事件
        self.weekly_tree.blockSignals(True)
        
        self.weekly_tree.clear()
        
        for i in range(7):
            day = self.week_start + timedelta(days=i)
            day_key = day.strftime('%Y-%m-%d')
            
            # 应用使用统计
            app_daily = app_summary.get('daily_totals', {}).get(day, {'total_time': 0})
            app_d = app_daily.get('total_time', 0)
            
            # 计时统计
            timer_stats = timer_summary['daily_stats'].get(day, {'duration': 0, 'count': 0})
            timer_d, timer_c = timer_stats['duration'], timer_stats['count']
            
            # 格式化应用时间
            if app_d > 0:
                h, m = app_d // 3600, (app_d % 3600) // 60
                app_str = f"📱{h}h{m}m" if h else f"📱{m}m"
            else:
                app_str = "📱-"
            
            # 格式化计时时间
            if timer_d > 0:
                h, m = timer_d // 3600, (timer_d % 3600) // 60
                timer_str = f"🍅{h}h{m}m" if h else f"🍅{m}m"
            else:
                timer_str = "🍅-"
            
            day_str = f"{weekdays[i]} ({day.strftime('%m/%d')})"
            
            # 检查是否已展开
            is_expanded = day_key in self.weekly_expanded_items
            arrow = "▼" if is_expanded else "▶"
            
            text = f"{arrow} {day_str}  {app_str}  {timer_str}"
            
            if day == today:
                text = f"🔹 {arrow} {day_str}  {app_str}  {timer_str}"
            
            # 创建父节点（日期）
            day_item = QTreeWidgetItem([text])
            day_item.setData(0, Qt.ItemDataRole.UserRole, day_key)  # 存储日期key
            
            # 添加子节点
            self._add_day_children(day_item, day)
            
            self.weekly_tree.addTopLevelItem(day_item)
            
            # 恢复展开状态
            if is_expanded:
                day_item.setExpanded(True)
        
        # 添加本周Top应用
        if top_apps:
            is_top_expanded = "top_apps" in self.weekly_expanded_items
            arrow = "▼" if is_top_expanded else "▶"
            top_item = QTreeWidgetItem([f"{arrow} 📱 本周Top应用"])
            top_item.setData(0, Qt.ItemDataRole.UserRole, "top_apps")
            
            self._add_top_apps_children(top_item, top_apps)
            
            top_item.setExpanded(is_top_expanded)
            self.weekly_tree.addTopLevelItem(top_item)
        
        # 解除信号阻塞
        self.weekly_tree.blockSignals(False)
    
    def _update_weekly_tree(self, app_summary, timer_summary, weekdays, top_apps, today):
        """增量更新周统计树（不重建，只更新文本和子节点）"""
        # 阻塞信号
        self.weekly_tree.blockSignals(True)
        
        for i in range(7):
            day = self.week_start + timedelta(days=i)
            day_key = day.strftime('%Y-%m-%d')
            
            # 查找对应的树项目
            day_item = self.weekly_tree.topLevelItem(i)
            if not day_item:
                continue
            
            # 应用使用统计
            app_daily = app_summary.get('daily_totals', {}).get(day, {'total_time': 0})
            app_d = app_daily.get('total_time', 0)
            
            # 计时统计
            timer_stats = timer_summary['daily_stats'].get(day, {'duration': 0, 'count': 0})
            timer_d, timer_c = timer_stats['duration'], timer_stats['count']
            
            # 格式化应用时间
            if app_d > 0:
                h, m = app_d // 3600, (app_d % 3600) // 60
                app_str = f"📱{h}h{m}m" if h else f"📱{m}m"
            else:
                app_str = "📱-"
            
            # 格式化计时时间
            if timer_d > 0:
                h, m = timer_d // 3600, (timer_d % 3600) // 60
                timer_str = f"🍅{h}h{m}m" if h else f"🍅{m}m"
            else:
                timer_str = "🍅-"
            
            day_str = f"{weekdays[i]} ({day.strftime('%m/%d')})"
            
            # 保持当前展开状态
            is_expanded = day_item.isExpanded()
            arrow = "▼" if is_expanded else "▶"
            
            text = f"{arrow} {day_str}  {app_str}  {timer_str}"
            
            if day == today:
                text = f"🔹 {arrow} {day_str}  {app_str}  {timer_str}"
            
            # 更新父节点文本
            day_item.setText(0, text)
            
            # 更新子节点（清除并重新添加）
            while day_item.childCount() > 0:
                day_item.removeChild(day_item.child(0))
            self._add_day_children(day_item, day)
        
        # 更新本周Top应用（如果存在）
        top_item_index = self.weekly_tree.topLevelItemCount() - 1
        if top_item_index >= 7:
            top_item = self.weekly_tree.topLevelItem(top_item_index)
            if top_item and top_item.data(0, Qt.ItemDataRole.UserRole) == "top_apps":
                is_expanded = top_item.isExpanded()
                arrow = "▼" if is_expanded else "▶"
                top_item.setText(0, f"{arrow} 📱 本周Top应用")
                
                # 更新子节点
                while top_item.childCount() > 0:
                    top_item.removeChild(top_item.child(0))
                self._add_top_apps_children(top_item, top_apps)
        
        # 解除信号阻塞
        self.weekly_tree.blockSignals(False)
    
    def _add_day_children(self, day_item, day):
        """为日期项添加子节点"""
        # 添加子节点 - 应用使用（直接列出，不显示标题）
        daily_summary = app_usage_storage.get_daily_summary(day)
        app_records = daily_summary.get('records', [])
        if app_records:
            for app_record in app_records[:5]:
                name = app_record.app_name
                if len(name) > 15:
                    name = name[:12] + "..."
                time_str = app_record.format_time()
                exe_path = app_record.exe_path
                child = QTreeWidgetItem([f"    📱 {name} | {time_str}"])
                child.setToolTip(0, app_record.app_name)
                
                # 添加应用图标
                if exe_path:
                    if exe_path not in self.icon_cache:
                        self.icon_cache[exe_path] = get_icon_from_exe(exe_path)
                    icon = self.icon_cache.get(exe_path)
                    if icon:
                        child.setIcon(0, QIcon(icon))
                
                day_item.addChild(child)
        
        # 添加子节点 - 计时记录（直接列出，不显示标题）
        timer_records = timer_storage.get_records_by_date(day)
        if timer_records:
            for r in reversed(timer_records[-5:]):
                note = r.note if r.note else "无备注"
                if len(note) > 12:
                    note = note[:10] + "..."
                child = QTreeWidgetItem([f"    {r.get_mode_icon()} {r.format_time()} | {r.format_duration()} | {note}"])
                day_item.addChild(child)
    
    def _add_top_apps_children(self, top_item, top_apps):
        """为本周Top应用项添加子节点"""
        for app in top_apps[:5]:
            name = app['name']
            exe_path = app.get('exe_path', '')
            if len(name) > 15:
                name = name[:12] + "..."
            child = QTreeWidgetItem([f"    {name} | {app['time_str']}"])
            child.setToolTip(0, app['name'])
            
            # 添加应用图标
            if exe_path:
                if exe_path not in self.icon_cache:
                    self.icon_cache[exe_path] = get_icon_from_exe(exe_path)
                icon = self.icon_cache.get(exe_path)
                if icon:
                    child.setIcon(0, QIcon(icon))
            
            top_item.addChild(child)
    
    def _on_weekly_item_clicked(self, item, column):
        """周统计项目点击事件 - 实现单击展开/折叠"""
        import time
        
        # 只处理顶级项目
        if item.parent() is not None:
            return

        # 只切换真正有子节点的项
        if item.childCount() <= 0:
            return

        # 记录用户交互时间，防止 update_ui 立即刷新导致折叠
        self._weekly_last_interaction = time.time()

        # 获取目标展开状态
        target_state = not item.isExpanded()
        day_key = item.data(0, Qt.ItemDataRole.UserRole)
        
        # 立即更新展开状态记录（在设置展开之前），防止 _load_weekly_data 刷新时状态丢失
        if day_key:
            if target_state:
                self.weekly_expanded_items.add(day_key)
            else:
                self.weekly_expanded_items.discard(day_key)
        
        # 更新箭头图标
        text = item.text(0)
        if target_state and "▶" in text:
            item.setText(0, text.replace("▶", "▼"))
        elif not target_state and "▼" in text:
            item.setText(0, text.replace("▼", "▶"))
        
        # 阻塞信号以防止触发 itemExpanded/itemCollapsed 事件（避免重复处理）
        self.weekly_tree.blockSignals(True)
        item.setExpanded(target_state)
        self.weekly_tree.blockSignals(False)
    
    def _on_weekly_item_expanded(self, item):
        """周统计项目展开事件"""
        day_key = item.data(0, Qt.ItemDataRole.UserRole)
        if day_key:
            self.weekly_expanded_items.add(day_key)
            # 更新箭头图标
            text = item.text(0)
            if "▶" in text:
                item.setText(0, text.replace("▶", "▼"))
    
    def _on_weekly_item_collapsed(self, item):
        """周统计项目折叠事件"""
        day_key = item.data(0, Qt.ItemDataRole.UserRole)
        if day_key:
            self.weekly_expanded_items.discard(day_key)
            # 更新箭头图标
            text = item.text(0)
            if "▼" in text:
                item.setText(0, text.replace("▼", "▶"))
    
    def _prev_week(self):
        self.week_start -= timedelta(days=7)
        self.weekly_expanded_items.clear()  # 切换周时清除展开状态
        self._load_weekly_data(force_rebuild=True)
    
    def _next_week(self):
        self.week_start += timedelta(days=7)
        self.weekly_expanded_items.clear()  # 切换周时清除展开状态
        self._load_weekly_data(force_rebuild=True)

    def _create_apps_tab(self):
        """创建应用统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)
        
        title = QLabel("📊 今日应用使用")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # 应用列表
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        # 启用平滑滚动
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        
        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)
        
        self.icon_cache = {}
        self.list_items = {}
        
        return tab

    def _setup_timer(self):
        """设置计时器"""
        self.countdown_running = False
        self.countdown_paused = False
        self.countdown_seconds = 25 * 60
        self.stopwatch_seconds = 0
        
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_timer)
    
    def _on_time_setting_changed(self):
        """时间设置改变"""
        if not self.countdown_running and not self.countdown_paused:
            total = self.minutes_spinbox.value() * 60 + self.seconds_spinbox.value()
            if total == 0:
                total = 1
            self.countdown_seconds = total
            self.initial_countdown_seconds = total
            mins, secs = total // 60, total % 60
            self.countdown_label.setText(f"{mins:02d}:{secs:02d}")
    
    def _update_tab_styles(self):
        """更新Tab样式"""
        active = "color: white; background: rgba(255,255,255,0.3); border: none; border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: bold;"
        inactive = "color: rgba(255,255,255,0.6); background: transparent; border: none; border-radius: 8px; padding: 6px 12px; font-size: 12px;"
        
        if self.timer_mode == 'countdown':
            self.countdown_tab.setStyleSheet(f"QPushButton {{{active}}}")
            self.stopwatch_tab.setStyleSheet(f"QPushButton {{{inactive}}} QPushButton:hover {{color: white; background: rgba(255,255,255,0.1);}}")
        else:
            self.countdown_tab.setStyleSheet(f"QPushButton {{{inactive}}} QPushButton:hover {{color: white; background: rgba(255,255,255,0.1);}}")
            self.stopwatch_tab.setStyleSheet(f"QPushButton {{{active}}}")
    
    def switch_timer_mode(self, mode):
        """切换模式"""
        if self.countdown_running or self.countdown_paused:
            return
        if mode == self.timer_mode:
            return
        
        self.timer_mode = mode
        self._update_tab_styles()
        
        if mode == 'stopwatch':
            self.time_setting_row.hide()
            self.timer_progress.hide()
            self.countdown_label.setText("00:00")
            self.stopwatch_seconds = 0
        else:
            self.time_setting_row.show()
            self.timer_progress.show()
            self._on_time_setting_changed()
        
        self.countdown_label.setStyleSheet("font-size: 42px; font-weight: bold; color: white;")
        self.timer_status_label.setText("准备开始")
    
    def _apply_timer_background(self):
        """应用计时器背景"""
        bg_type = app_config.get('background_type', 'gradient')
        
        if bg_type == 'image':
            bg_image = app_config.get('background_image', '')
            if bg_image and os.path.exists(bg_image):
                # 使用 border-image 来设置背景图片并保持圆角
                # 需要将路径中的反斜杠转换为正斜杠
                bg_image_path = bg_image.replace('\\', '/')
                self.timer_frame.setStyleSheet(f"""
                    QFrame#TimerFrame {{
                        border-image: url("{bg_image_path}") 0 0 0 0 stretch stretch;
                        border-radius: 12px;
                    }}
                """)
            else:
                # 图片不存在时使用默认渐变
                self.timer_frame.setStyleSheet("QFrame#TimerFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2); border-radius: 12px; }")
        elif bg_type == 'gradient':
            colors = app_config.get('background_gradient', ['#667eea', '#764ba2'])
            self.timer_frame.setStyleSheet(f"""
                QFrame#TimerFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {colors[0]}, stop:1 {colors[1]});
                    border-radius: 12px;
                }}
            """)
        elif bg_type == 'color':
            color = app_config.get('background_color', '#667eea')
            self.timer_frame.setStyleSheet(f"QFrame#TimerFrame {{ background-color: {color}; border-radius: 12px; }}")
        else:
            self.timer_frame.setStyleSheet("QFrame#TimerFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2); border-radius: 12px; }")
    
    def _apply_global_background(self):
        """应用全局背景"""
        global_enabled = app_config.get('global_bg_enabled', False)
        
        if global_enabled:
            bg_type = app_config.get('global_bg_type', 'image')
            blur_radius = app_config.get('global_bg_blur', 0)
            opacity = app_config.get('global_bg_opacity', 0.85)
            
            # 设置背景层
            if bg_type == 'image':
                bg_image = app_config.get('global_bg_image', '')
                if bg_image and os.path.exists(bg_image):
                    pixmap = QPixmap(bg_image)
                    self.bg_layer.setPixmap(pixmap)
                    self.bg_layer.setStyleSheet("border-radius: 20px;")
                else:
                    self.bg_layer.clear()
                    self.bg_layer.setStyleSheet("background-color: #f8f9fa; border-radius: 20px;")
            elif bg_type == 'color':
                bg_color = app_config.get('global_bg_color', '#f8f9fa')
                self.bg_layer.clear()
                self.bg_layer.setStyleSheet(f"background-color: {bg_color}; border-radius: 20px;")
            else:  # gradient
                colors = app_config.get('global_bg_gradient', ['#e0e5ec', '#f8f9fa'])
                self.bg_layer.clear()
                self.bg_layer.setStyleSheet(f"""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {colors[0]}, stop:1 {colors[1]});
                    border-radius: 20px;
                """)
            
            # 应用模糊效果
            if blur_radius > 0:
                blur_effect = QGraphicsBlurEffect()
                blur_effect.setBlurRadius(blur_radius)
                self.bg_layer.setGraphicsEffect(blur_effect)
            else:
                self.bg_layer.setGraphicsEffect(None)
            
            self.bg_layer.show()
            self.bg_layer.setGeometry(0, 0, self.width(), self.height())
            
            # 设置根部件背景透明
            self.root_widget.setStyleSheet("""
                QWidget#RootWidget {
                    background-color: transparent;
                    border-radius: 20px;
                }
            """)
            
            # 设置主容器半透明 - 让背景透出来
            self.central_widget.setStyleSheet(f"""
                QWidget#MainContainer {{
                    background-color: rgba(255, 255, 255, {opacity});
                    border-radius: 20px;
                    border: 1px solid rgba(224, 224, 224, {opacity});
                }}
            """)
            
            # 更新所有子组件的样式以支持半透明
            self._apply_transparent_styles(opacity)
        else:
            # 禁用全局背景时的默认样式
            self.bg_layer.hide()
            self.bg_layer.setGraphicsEffect(None)
            
            self.root_widget.setStyleSheet("""
                QWidget#RootWidget {
                    background-color: transparent;
                    border-radius: 20px;
                }
            """)
            
            self.central_widget.setStyleSheet("""
                QWidget#MainContainer {
                    background-color: white;
                    border-radius: 20px;
                    border: 1px solid #e0e0e0;
                }
            """)
            
            # 恢复默认样式
            self._apply_default_styles()
    
    def _apply_transparent_styles(self, opacity):
        """应用半透明样式到所有子组件"""
        # 计算透明度值
        bg_alpha = opacity
        frame_alpha = max(0.3, opacity - 0.2)  # 框架稍微更透明
        
        # 当前应用区域
        if hasattr(self, 'current_app_frame'):
            self.current_app_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(248, 249, 250, {bg_alpha});
                    border-radius: 12px;
                }}
            """)
        
        # 今日计时列表
        if hasattr(self, 'history_list'):
            self.history_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: rgba(248, 249, 250, {frame_alpha});
                    border: none;
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 15px;
                }}
                QListWidget::item {{
                    background-color: rgba(255, 255, 255, {bg_alpha});
                    border-radius: 8px;
                    margin: 3px 0;
                    padding: 12px;
                    color: #333;
                    font-weight: 500;
                }}
                QListWidget::item:hover {{
                    background-color: rgba(233, 236, 239, {bg_alpha});
                }}
                QListWidget::item:selected {{
                    background-color: rgba(208, 232, 255, {bg_alpha});
                    color: #333;
                }}
            """)
        
        # 右侧标签页
        if hasattr(self, 'right_tabs'):
            self.right_tabs.setStyleSheet(f"""
                QTabWidget::pane {{
                    border: none;
                    background: transparent;
                }}
                QTabBar::tab {{
                    background: rgba(240, 240, 240, {frame_alpha});
                    padding: 10px 18px;
                    margin-right: 4px;
                    border-radius: 8px 8px 0 0;
                    font-size: 14px;
                }}
                QTabBar::tab:selected {{
                    background: rgba(232, 244, 255, {bg_alpha});
                    font-weight: bold;
                    color: #007bff;
                }}
                QTabBar::tab:hover {{
                    background: rgba(224, 224, 224, {bg_alpha});
                }}
            """)
        
        # 应用列表滚动区域
        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    border: none;
                    background: transparent;
                }}
                QScrollBar:vertical {{
                    background: rgba(240, 240, 240, {frame_alpha});
                    width: 8px;
                    border-radius: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background: rgba(192, 192, 192, {bg_alpha});
                    border-radius: 4px;
                    min-height: 30px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: rgba(160, 160, 160, {bg_alpha});
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
            """)
        
        # 日期记录列表
        if hasattr(self, 'day_records_list'):
            self.day_records_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: rgba(248, 249, 250, {frame_alpha});
                    border: none;
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 15px;
                }}
                QListWidget::item {{
                    background-color: rgba(255, 255, 255, {bg_alpha});
                    border-radius: 8px;
                    margin: 3px 0;
                    padding: 12px;
                    color: #333;
                    font-weight: 500;
                }}
                QListWidget::item:hover {{
                    background-color: rgba(233, 236, 239, {bg_alpha});
                }}
                QListWidget::item:selected {{
                    background-color: rgba(208, 232, 255, {bg_alpha});
                    color: #333;
                }}
            """)
        
        # 周统计树
        if hasattr(self, 'weekly_tree'):
            self.weekly_tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: rgba(248, 249, 250, {frame_alpha});
                    border: none;
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 14px;
                }}
                QTreeWidget::item {{
                    background-color: rgba(255, 255, 255, {bg_alpha});
                    border-radius: 6px;
                    margin: 2px 0;
                    padding: 10px 8px;
                    color: #333;
                    font-weight: 500;
                }}
                QTreeWidget::item:hover {{
                    background-color: rgba(233, 236, 239, {bg_alpha});
                }}
                QTreeWidget::item:selected {{
                    background-color: rgba(208, 232, 255, {bg_alpha});
                    color: #333;
                }}
                QTreeWidget::branch {{
                    background: transparent;
                }}
            """)
        
        # 周统计总计框
        if hasattr(self, 'weekly_total_frame'):
            self.weekly_total_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(44, 62, 80, {bg_alpha});
                    border-radius: 12px;
                }}
            """)
    
    def _apply_default_styles(self):
        """恢复默认样式"""
        # 当前应用区域
        if hasattr(self, 'current_app_frame'):
            self.current_app_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 12px;
                }
            """)
        
        # 今日计时列表
        if hasattr(self, 'history_list'):
            self.history_list.setStyleSheet("""
                QListWidget {
                    background-color: #f8f9fa;
                    border: none;
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 15px;
                }
                QListWidget::item {
                    background-color: white;
                    border-radius: 8px;
                    margin: 3px 0;
                    padding: 12px;
                    color: #333;
                    font-weight: 500;
                }
                QListWidget::item:hover {
                    background-color: #e9ecef;
                }
                QListWidget::item:selected {
                    background-color: #d0e8ff;
                    color: #333;
                }
            """)
        
        # 右侧标签页
        if hasattr(self, 'right_tabs'):
            self.right_tabs.setStyleSheet("""
                QTabWidget::pane {
                    border: none;
                    background: transparent;
                }
                QTabBar::tab {
                    background: #f0f0f0;
                    padding: 10px 18px;
                    margin-right: 4px;
                    border-radius: 8px 8px 0 0;
                    font-size: 14px;
                }
                QTabBar::tab:selected {
                    background: #e8f4ff;
                    font-weight: bold;
                    color: #007bff;
                }
                QTabBar::tab:hover {
                    background: #e0e0e0;
                }
            """)
        
        # 应用列表滚动区域
        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background: transparent;
                }
                QScrollBar:vertical {
                    background: #f0f0f0;
                    width: 8px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background: #c0c0c0;
                    border-radius: 4px;
                    min-height: 30px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #a0a0a0;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """)
        
        # 日期记录列表
        if hasattr(self, 'day_records_list'):
            self.day_records_list.setStyleSheet("""
                QListWidget {
                    background-color: #f8f9fa;
                    border: none;
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 15px;
                }
                QListWidget::item {
                    background-color: white;
                    border-radius: 8px;
                    margin: 3px 0;
                    padding: 12px;
                    color: #333;
                    font-weight: 500;
                }
                QListWidget::item:hover {
                    background-color: #e9ecef;
                }
                QListWidget::item:selected {
                    background-color: #d0e8ff;
                    color: #333;
                }
            """)
        
        # 周统计树
        if hasattr(self, 'weekly_tree'):
            self.weekly_tree.setStyleSheet("""
                QTreeWidget {
                    background-color: #f8f9fa;
                    border: none;
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 14px;
                }
                QTreeWidget::item {
                    background-color: white;
                    border-radius: 6px;
                    margin: 2px 0;
                    padding: 10px 8px;
                    color: #333;
                    font-weight: 500;
                }
                QTreeWidget::item:hover {
                    background-color: #e9ecef;
                }
                QTreeWidget::item:selected {
                    background-color: #d0e8ff;
                    color: #333;
                }
                QTreeWidget::branch {
                    background: transparent;
                }
            """)
        
        # 周统计总计框
        if hasattr(self, 'weekly_total_frame'):
            self.weekly_total_frame.setStyleSheet("""
                QFrame {
                    background-color: #2c3e50;
                    border-radius: 12px;
                }
            """)
    
    def resizeEvent(self, event):
        """窗口大小改变时调整背景"""
        super().resizeEvent(event)
        # 确保背景层填满窗口
        if hasattr(self, 'bg_layer'):
            self.bg_layer.setGeometry(0, 0, self.width(), self.height())
    
    def showEvent(self, event):
        """窗口显示时调整背景"""
        super().showEvent(event)
        if hasattr(self, 'bg_layer'):
            self.bg_layer.setGeometry(0, 0, self.width(), self.height())

    def open_settings(self):
        """打开设置"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()
    
    def _on_settings_changed(self):
        """设置改变"""
        self._apply_timer_background()
        self._apply_global_background()
    
    def _setup_monitor(self):
        """设置监控"""
        self.monitor = AppMonitor()
        self.monitor.update_signal.connect(self.update_ui)
        self.monitor.start()

    # === 窗口操作 ===
    
    def minimize_to_mini(self):
        """最小化"""
        self.saved_pos = self.pos()
        self.hide()
        screen = QApplication.primaryScreen().geometry()
        self.mini_window.move(screen.width() - 300, 50)
        self.mini_window.show()
        if self.current_data:
            self.mini_window.update_display(self.current_data, self.icon_cache)

    def restore_from_mini(self):
        """恢复"""
        self.mini_window.hide()
        if hasattr(self, 'saved_pos'):
            self.move(self.saved_pos)
        self.show()
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.show()

    def toggle_always_on_top(self):
        """切换置顶"""
        self.is_always_on_top = not self.is_always_on_top
        
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.pin_btn.setText("📍")
            self.pin_btn.setStyleSheet("font-size: 18px; color: white; background-color: #007bff; border: 2px solid #007bff; border-radius: 6px;")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.pin_btn.setText("📌")
            self.pin_btn.setStyleSheet("font-size: 18px; color: #999; background-color: transparent; border: 2px solid #ddd; border-radius: 6px;")
        
        self.show()

    # === 鼠标事件 ===
    
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

    # === 计时器功能 ===
    
    def toggle_timer(self):
        """切换计时"""
        if self.countdown_running:
            self.pause_timer()
        else:
            self.start_timer()
    
    def start_timer(self):
        """开始"""
        if self.timer_mode == 'countdown':
            if not self.countdown_paused:
                total = self.minutes_spinbox.value() * 60 + self.seconds_spinbox.value()
                if total == 0:
                    total = 1
                self.countdown_seconds = total
                self.initial_countdown_seconds = total
                self.current_note = self.note_input.text().strip()
            self.timer_status_label.setText("专注中...")
        else:
            if not self.countdown_paused:
                self.stopwatch_seconds = 0
                self.current_note = self.note_input.text().strip()
            self.timer_status_label.setText("计时中...")
        
        self.countdown_running = True
        self.countdown_paused = False
        self.countdown_timer.start(1000)
        
        self.start_btn.setText("⏸")
        self.start_btn.setStyleSheet("font-size: 20px; border: none; border-radius: 25px; background-color: rgba(255, 200, 100, 0.9); color: #333;")
        
        self.countdown_tab.setEnabled(False)
        self.stopwatch_tab.setEnabled(False)
        self.minutes_spinbox.setEnabled(False)
        self.seconds_spinbox.setEnabled(False)
        self.note_input.setEnabled(False)
        self.status_indicator.setStyleSheet("font-size: 14px; color: #00ff88; font-weight: bold;")

    def pause_timer(self):
        """暂停"""
        self.countdown_running = False
        self.countdown_paused = True
        self.countdown_timer.stop()
        
        self.start_btn.setText("▶")
        self.start_btn.setStyleSheet("font-size: 20px; border: none; border-radius: 25px; background-color: rgba(255, 255, 255, 0.9); color: #667eea;")
        
        self.timer_status_label.setText("已暂停")
        self.status_indicator.setStyleSheet("font-size: 14px; color: #ffd700; font-weight: bold;")

    def reset_countdown(self):
        """重置"""
        if self.countdown_running or self.countdown_paused:
            self._save_timer_record()
        
        self.countdown_running = False
        self.countdown_paused = False
        self.countdown_timer.stop()
        
        if self.timer_mode == 'countdown':
            total = self.minutes_spinbox.value() * 60 + self.seconds_spinbox.value()
            if total == 0:
                total = 1
            self.countdown_seconds = total
            self.initial_countdown_seconds = total
            self.timer_progress.setValue(100)
        else:
            self.stopwatch_seconds = 0
        
        self.update_timer_display()
        self.countdown_label.setStyleSheet("font-size: 42px; font-weight: bold; color: white;")
        
        self.start_btn.setText("▶")
        self.start_btn.setStyleSheet("font-size: 20px; border: none; border-radius: 25px; background-color: rgba(255, 255, 255, 0.9); color: #667eea;")
        
        self.countdown_tab.setEnabled(True)
        self.stopwatch_tab.setEnabled(True)
        self.minutes_spinbox.setEnabled(True)
        self.seconds_spinbox.setEnabled(True)
        self.note_input.setEnabled(True)
        self.timer_status_label.setText("准备开始")
        self.status_indicator.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.5); font-weight: bold;")
    
    def _save_timer_record(self):
        """保存记录"""
        if self.timer_mode == 'countdown':
            elapsed = self.initial_countdown_seconds - self.countdown_seconds
            completed = self.countdown_seconds == 0
        else:
            elapsed = self.stopwatch_seconds
            completed = True
        
        if elapsed <= 0:
            return
        
        note = getattr(self, 'current_note', '') or ""
        record = TimerRecord(mode=self.timer_mode, duration=elapsed, note=note, timestamp=datetime.now(), completed=completed)
        timer_storage.add_record(record)
        
        self._add_record_to_list(record)
        
        while self.history_list.count() > 10:
            self.history_list.takeItem(self.history_list.count() - 1)
    
    def _add_record_to_list(self, record):
        """添加记录到列表"""
        text = f"{record.get_mode_icon()} {record.format_time()} | {record.format_duration()} | {record.note or '无备注'}"
        self.history_list.insertItem(0, QListWidgetItem(text))
    
    def _load_today_history(self):
        """加载今日记录"""
        records = timer_storage.get_today_records()
        records.sort(key=lambda r: r.timestamp, reverse=True)
        for r in records[:10]:
            self._add_record_to_list(r)

    def update_timer(self):
        """更新计时"""
        if self.timer_mode == 'countdown':
            if self.countdown_seconds > 0:
                self.countdown_seconds -= 1
                self.update_timer_display()
            else:
                self.countdown_timer.stop()
                self.countdown_running = False
                self.on_countdown_finished()
        else:
            self.stopwatch_seconds += 1
            self.update_timer_display()

    def update_timer_display(self):
        """更新显示"""
        if self.timer_mode == 'countdown':
            mins, secs = self.countdown_seconds // 60, self.countdown_seconds % 60
            self.countdown_label.setText(f"{mins:02d}:{secs:02d}")
            
            if self.initial_countdown_seconds > 0:
                progress = int((self.countdown_seconds / self.initial_countdown_seconds) * 100)
                self.timer_progress.setValue(progress)
            
            if self.countdown_seconds <= 10:
                self.countdown_label.setStyleSheet("font-size: 42px; font-weight: bold; color: #ff6b6b;")
                self.timer_status_label.setText("即将结束！")
            elif self.countdown_seconds <= 60:
                self.countdown_label.setStyleSheet("font-size: 42px; font-weight: bold; color: #ffd93d;")
            else:
                self.countdown_label.setStyleSheet("font-size: 42px; font-weight: bold; color: white;")
        else:
            hours = self.stopwatch_seconds // 3600
            mins = (self.stopwatch_seconds % 3600) // 60
            secs = self.stopwatch_seconds % 60
            
            if hours > 0:
                self.countdown_label.setText(f"{hours}:{mins:02d}:{secs:02d}")
            else:
                self.countdown_label.setText(f"{mins:02d}:{secs:02d}")
            
            self.countdown_label.setStyleSheet("font-size: 42px; font-weight: bold; color: #00ff88;")

    def play_notification_sound(self):
        """播放提示音"""
        def play():
            try:
                for _ in range(3):
                    winsound.Beep(800, 200)
                    winsound.Beep(1000, 200)
                    winsound.Beep(1200, 300)
            except:
                pass
        threading.Thread(target=play, daemon=True).start()

    def on_countdown_finished(self):
        """倒计时完成"""
        self._save_timer_record()
        self.play_notification_sound()
        
        note = getattr(self, 'current_note', '') or "专注时段"
        QMessageBox.information(self, "🍅 番茄完成！", f"🎉 完成！\n📝 事项: {note}\n建议休息5分钟~")
        
        self.reset_countdown()
        self.note_input.clear()

    # === UI 更新 ===
    
    def update_ui(self, data):
        """更新界面 - 优化版本，减少不必要的更新"""
        import time
        
        current = data['current_app']
        stats = data['all_stats']
        
        # 缓存当前数据
        self.current_data = data
        
        # 更新迷你窗口（仅在可见时）
        if self.mini_window.isVisible():
            self.mini_window.update_display(data, self.icon_cache)
        
        # 更新当前应用显示
        self._update_current_app_display(current)
        
        # 更新今日总使用时间
        self._update_today_usage(stats)
        
        # 节流：日历记录和周统计的更新频率限制
        current_time = time.time()
        
        # 日历记录更新（每5秒最多一次）
        if not hasattr(self, '_last_day_records_update'):
            self._last_day_records_update = 0
        
        if hasattr(self, 'selected_date') and self.selected_date == datetime.now().date():
            if current_time - self._last_day_records_update >= 5:
                self._load_day_records(self.selected_date)
                self._last_day_records_update = current_time
        
        # 周统计更新（每10秒最多一次，且需要检查用户交互冷却）
        if not hasattr(self, '_last_weekly_update'):
            self._last_weekly_update = 0
        
        if hasattr(self, 'is_current_week') and self.is_current_week:
            # 检查用户交互冷却时间
            interaction_cooldown = getattr(self, '_weekly_interaction_cooldown', 2.0)
            last_interaction = getattr(self, '_weekly_last_interaction', 0)
            
            if (current_time - self._last_weekly_update >= 10 and
                current_time - last_interaction >= interaction_cooldown):
                self._load_weekly_data()
                self._last_weekly_update = current_time

        # 更新应用列表（优化版本）
        self._update_app_list(stats)
    
    def _update_current_app_display(self, current):
        """更新当前应用显示 - 分离出来便于维护"""
        if current:
            # 截断过长的应用名称
            name = current['name']
            display_name = name if len(name) <= 18 else name[:15] + "..."
            
            # 只在内容变化时更新
            if self.curr_name.text() != display_name:
                self.curr_name.setText(display_name)
                self.curr_name.setToolTip(name)
            
            sub = current.get('current_sub_title')
            if sub:
                display = sub if len(sub) <= 25 else sub[:22] + "..."
                if self.curr_sub_title.text() != display:
                    self.curr_sub_title.setText(display)
                    self.curr_sub_title.setToolTip(sub)
                if not self.curr_sub_title.isVisible():
                    self.curr_sub_title.show()
            else:
                if self.curr_sub_title.isVisible():
                    self.curr_sub_title.hide()
            
            # 更新计时器显示
            time_str = format_time(current['session_time'])
            if self.curr_timer.text() != time_str:
                self.curr_timer.setText(time_str)
            
            # 更新图标（使用缓存）
            path = current['path']
            if path not in self.icon_cache:
                self.icon_cache[path] = get_icon_from_exe(path)
            
            icon = self.icon_cache.get(path)
            if icon:
                # 缓存缩放后的图标，避免重复缩放
                cache_key = f"{path}_scaled_56"
                if cache_key not in self.icon_cache:
                    self.icon_cache[cache_key] = icon.scaled(
                        56, 56,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                self.curr_icon.setPixmap(self.icon_cache[cache_key])
            else:
                self.curr_icon.setText(current['name'][0] if current['name'] else "?")
        else:
            if self.curr_name.text() != "闲置":
                self.curr_name.setText("闲置")
            if self.curr_sub_title.isVisible():
                self.curr_sub_title.hide()
            if self.curr_timer.text() != "00:00:00":
                self.curr_timer.setText("00:00:00")
            self.curr_icon.setText("-")
    
    def _update_app_list(self, stats):
        """更新应用列表 - 优化版本"""
        # 按使用时间排序
        sorted_apps = sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True)
        
        # 检查是否需要重建列表
        current_paths = set(self.list_items.keys())
        new_paths = set(path for path, _ in sorted_apps)
        
        need_rebuild = current_paths != new_paths
        
        if need_rebuild:
            # 完全重建列表
            while self.list_layout.count():
                child = self.list_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.list_items.clear()
            
            for path, info in sorted_apps:
                # 获取或创建图标缓存
                if path not in self.icon_cache:
                    self.icon_cache[path] = get_icon_from_exe(path)
                
                item = AppListItem(
                    info['name'],
                    format_time(info['total_time']),
                    self.icon_cache.get(path),
                    info.get('app_type', 'normal'),
                    info.get('children', {})
                )
                self.list_layout.addWidget(item)
                self.list_items[path] = item
            
            self.list_layout.addStretch()
        else:
            # 增量更新：只更新时间和子项
            for path, info in sorted_apps:
                if path in self.list_items:
                    item = self.list_items[path]
                    new_time = format_time(info['total_time'])
                    if item.time_label.text() != new_time:
                        item.time_label.setText(new_time)
                    if hasattr(item, 'update_children'):
                        item.update_children(info.get('children', {}))
    
    def _update_today_usage(self, stats):
        """更新今日总使用时间显示"""
        if not hasattr(self, 'today_usage_label'):
            return
        
        # 计算今日总使用时间
        total_seconds = sum(info.get('total_time', 0) for info in stats.values())
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        if hours > 0:
            time_str = f"{hours}h {minutes}m"
        else:
            time_str = f"{minutes}m"
        
        self.today_usage_label.setText(time_str)
    
    def _auto_save_usage(self):
        """自动保存"""
        if self.current_data and self.current_data.get('all_stats'):
            app_usage_storage.save_daily_usage(datetime.now().date(), self.current_data['all_stats'])
    
    def closeEvent(self, event):
        """关闭"""
        self._auto_save_usage()
        
        if hasattr(self, 'monitor'):
            self.monitor.stop()
        if hasattr(self, 'save_timer'):
            self.save_timer.stop()
        if hasattr(self, 'mini_window'):
            self.mini_window.close()
        
        event.accept()