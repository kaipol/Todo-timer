"""
日历视图模块 - 显示日历和计时记录
"""
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QGridLayout, QFrame, QScrollArea,
                              QListWidget, QListWidgetItem, QDialog, QSizePolicy,
                              QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.storage import timer_storage, TimerRecord, app_usage_storage


class CalendarWidget(QWidget):
    """日历组件"""
    date_selected = pyqtSignal(object)  # 发送选中的日期
    
    def __init__(self):
        super().__init__()
        self.current_date = datetime.now().date()
        self.selected_date = self.current_date
        self.displayed_month = self.current_date.replace(day=1)
        
        self._setup_ui()
        self._update_calendar()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 月份导航
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #f0f0f0;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.prev_btn.clicked.connect(self._prev_month)
        nav_layout.addWidget(self.prev_btn)
        
        nav_layout.addStretch()
        
        self.month_label = QLabel()
        self.month_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        nav_layout.addWidget(self.month_label)
        
        nav_layout.addStretch()
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #f0f0f0;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.next_btn.clicked.connect(self._next_month)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # 星期标题
        week_layout = QHBoxLayout()
        week_layout.setSpacing(2)
        week_days = ['一', '二', '三', '四', '五', '六', '日']
        for day in week_days:
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedHeight(24)
            label.setStyleSheet("color: #666; font-size: 12px; font-weight: bold;")
            week_layout.addWidget(label)
        layout.addLayout(week_layout)
        
        # 日历网格
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(2)
        layout.addLayout(self.calendar_grid)
        
        # 日期按钮容器
        self.day_buttons = []
    
    def _update_calendar(self):
        """更新日历显示"""
        # 清除现有按钮
        for btn in self.day_buttons:
            btn.deleteLater()
        self.day_buttons.clear()
        
        # 更新月份标签
        self.month_label.setText(self.displayed_month.strftime("%Y年%m月"))
        
        # 获取有记录的日期（合并计时记录和应用使用记录）
        dates_with_records = timer_storage.get_dates_with_records()
        dates_with_usage = app_usage_storage.get_dates_with_usage()
        dates_with_records = dates_with_records.union(dates_with_usage)
        
        # 计算月份第一天是周几 (0=周一)
        first_day = self.displayed_month
        first_weekday = first_day.weekday()
        
        # 获取上个月的最后几天
        if first_weekday > 0:
            prev_month_end = first_day - timedelta(days=1)
            prev_month_start = prev_month_end - timedelta(days=first_weekday - 1)
        else:
            prev_month_start = first_day
        
        # 计算这个月有多少天
        if self.displayed_month.month == 12:
            next_month = self.displayed_month.replace(year=self.displayed_month.year + 1, month=1)
        else:
            next_month = self.displayed_month.replace(month=self.displayed_month.month + 1)
        days_in_month = (next_month - self.displayed_month).days
        
        # 生成日历
        current_date = prev_month_start
        row = 0
        col = 0
        
        # 填充上个月的日期
        while current_date < first_day:
            btn = self._create_day_button(current_date, is_current_month=False, 
                                          has_record=current_date in dates_with_records)
            self.calendar_grid.addWidget(btn, row, col)
            self.day_buttons.append(btn)
            col += 1
            if col > 6:
                col = 0
                row += 1
            current_date += timedelta(days=1)
        
        # 填充当前月的日期
        for day in range(1, days_in_month + 1):
            current_date = self.displayed_month.replace(day=day)
            is_today = current_date == self.current_date
            is_selected = current_date == self.selected_date
            has_record = current_date in dates_with_records
            
            btn = self._create_day_button(current_date, is_current_month=True,
                                          is_today=is_today, is_selected=is_selected,
                                          has_record=has_record)
            self.calendar_grid.addWidget(btn, row, col)
            self.day_buttons.append(btn)
            col += 1
            if col > 6:
                col = 0
                row += 1
        
        # 填充下个月的日期
        current_date = next_month
        while col != 0:
            btn = self._create_day_button(current_date, is_current_month=False,
                                          has_record=current_date in dates_with_records)
            self.calendar_grid.addWidget(btn, row, col)
            self.day_buttons.append(btn)
            col += 1
            if col > 6:
                col = 0
                row += 1
            current_date += timedelta(days=1)
    
    def _create_day_button(self, date, is_current_month=True, is_today=False, 
                           is_selected=False, has_record=False):
        """创建日期按钮"""
        btn = QPushButton(str(date.day))
        btn.setFixedSize(36, 36)
        btn.setProperty('date', date)
        btn.clicked.connect(lambda checked, d=date: self._on_date_clicked(d))
        
        # 样式
        if is_selected:
            style = """
                QPushButton {
                    border: none;
                    border-radius: 18px;
                    background: #007bff;
                    color: white;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
        elif is_today:
            style = """
                QPushButton {
                    border: 2px solid #007bff;
                    border-radius: 18px;
                    background: white;
                    color: #007bff;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #e8f4ff;
                }
            """
        elif has_record:
            style = """
                QPushButton {
                    border: none;
                    border-radius: 18px;
                    background: #e8f4ff;
                    color: #333;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #d0e8ff;
                }
            """
        elif is_current_month:
            style = """
                QPushButton {
                    border: none;
                    border-radius: 18px;
                    background: transparent;
                    color: #333;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #f0f0f0;
                }
            """
        else:
            style = """
                QPushButton {
                    border: none;
                    border-radius: 18px;
                    background: transparent;
                    color: #ccc;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #f0f0f0;
                }
            """
        
        btn.setStyleSheet(style)
        return btn
    
    def _on_date_clicked(self, date):
        """日期点击处理"""
        self.selected_date = date
        self._update_calendar()
        self.date_selected.emit(date)
    
    def _prev_month(self):
        """上一个月"""
        if self.displayed_month.month == 1:
            self.displayed_month = self.displayed_month.replace(
                year=self.displayed_month.year - 1, month=12)
        else:
            self.displayed_month = self.displayed_month.replace(
                month=self.displayed_month.month - 1)
        self._update_calendar()
    
    def _next_month(self):
        """下一个月"""
        if self.displayed_month.month == 12:
            self.displayed_month = self.displayed_month.replace(
                year=self.displayed_month.year + 1, month=1)
        else:
            self.displayed_month = self.displayed_month.replace(
                month=self.displayed_month.month + 1)
        self._update_calendar()
    
    def refresh(self):
        """刷新日历"""
        self._update_calendar()


class DayRecordsWidget(QWidget):
    """单日记录显示组件 - 带标签页"""
    
    def __init__(self):
        super().__init__()
        self.current_date = datetime.now().date()
        self._setup_ui()
        self.load_date(self.current_date)
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 日期标题和统计
        self.date_label = QLabel()
        self.date_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        layout.addWidget(self.date_label)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #f8f9fa;
                border-radius: 10px;
            }
            QTabBar::tab {
                background: #e9ecef;
                padding: 8px 16px;
                margin-right: 4px;
                border-radius: 6px 6px 0 0;
            }
            QTabBar::tab:selected {
                background: #f8f9fa;
                font-weight: bold;
            }
        """)
        
        # 计时记录标签页
        timer_tab = QWidget()
        timer_layout = QVBoxLayout(timer_tab)
        timer_layout.setContentsMargins(8, 8, 8, 8)
        
        self.timer_stats_label = QLabel()
        self.timer_stats_label.setStyleSheet("font-size: 13px; color: #666;")
        timer_layout.addWidget(self.timer_stats_label)
        
        self.records_list = QListWidget()
        self.records_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 8px;
                margin: 3px 0;
                padding: 10px;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
        """)
        timer_layout.addWidget(self.records_list)
        self.tab_widget.addTab(timer_tab, "⏱ 计时记录")
        
        # 应用使用标签页
        usage_tab = QWidget()
        usage_layout = QVBoxLayout(usage_tab)
        usage_layout.setContentsMargins(8, 8, 8, 8)
        
        self.usage_stats_label = QLabel()
        self.usage_stats_label.setStyleSheet("font-size: 13px; color: #666;")
        usage_layout.addWidget(self.usage_stats_label)
        
        self.usage_list = QListWidget()
        self.usage_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 8px;
                margin: 3px 0;
                padding: 10px;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
        """)
        usage_layout.addWidget(self.usage_list)
        self.tab_widget.addTab(usage_tab, "📊 应用统计")
        
        layout.addWidget(self.tab_widget)
    
    def load_date(self, date):
        """加载指定日期的记录"""
        self.current_date = date
        
        # 更新标题
        if date == datetime.now().date():
            date_str = "今天"
        elif date == datetime.now().date() - timedelta(days=1):
            date_str = "昨天"
        else:
            date_str = date.strftime("%m月%d日")
        
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday = weekday_names[date.weekday()]
        self.date_label.setText(f"📅 {date_str} {weekday}")
        
        # 加载计时记录
        self._load_timer_records(date)
        
        # 加载应用使用数据
        self._load_usage_records(date)
    
    def _load_timer_records(self, date):
        """加载计时记录"""
        records = timer_storage.get_records_by_date(date)
        
        # 更新统计
        if records:
            total_duration = sum(r.duration for r in records)
            hours = total_duration // 3600
            minutes = (total_duration % 3600) // 60
            if hours > 0:
                time_str = f"{hours}小时{minutes}分钟"
            else:
                time_str = f"{minutes}分钟"
            self.timer_stats_label.setText(f"共 {len(records)} 条记录，总计 {time_str}")
        else:
            self.timer_stats_label.setText("暂无计时记录")
        
        # 更新列表
        self.records_list.clear()
        for record in reversed(records):  # 最新的在上面
            mode_icon = record.get_mode_icon()
            time_str = record.format_time()
            duration_str = record.format_duration()
            note = record.note or "无备注"
            
            text = f"{mode_icon} {time_str} | {duration_str} | {note}"
            item = QListWidgetItem(text)
            self.records_list.addItem(item)
    
    def _load_usage_records(self, date):
        """加载应用使用数据"""
        summary = app_usage_storage.get_daily_summary(date)
        
        # 更新统计
        total_time = summary['total_time']
        if total_time > 0:
            hours = total_time // 3600
            minutes = (total_time % 3600) // 60
            if hours > 0:
                time_str = f"{hours}小时{minutes}分钟"
            else:
                time_str = f"{minutes}分钟"
            self.usage_stats_label.setText(f"共 {summary['app_count']} 个应用，总计 {time_str}")
        else:
            self.usage_stats_label.setText("暂无应用使用数据")
        
        # 更新列表
        self.usage_list.clear()
        for app in summary.get('top_apps', []):
            app_type_icons = {
                'browser': '🌐',
                'chat': '💬',
                'editor': '📝',
                'normal': '📱'
            }
            icon = app_type_icons.get(app['app_type'], '📱')
            text = f"{icon} {app['name']}   |   {app['time_str']}"
            item = QListWidgetItem(text)
            self.usage_list.addItem(item)
        
        # 显示更多应用
        records = summary.get('records', [])
        if len(records) > 5:
            remaining = len(records) - 5
            item = QListWidgetItem(f"... 还有 {remaining} 个应用")
            item.setForeground(Qt.GlobalColor.gray)
            self.usage_list.addItem(item)
    
    def refresh(self):
        """刷新当前日期"""
        self.load_date(self.current_date)


class WeeklySummaryWidget(QWidget):
    """周总结组件 - 包含计时和应用使用统计"""
    
    def __init__(self):
        super().__init__()
        today = datetime.now().date()
        self.week_start = today - timedelta(days=today.weekday())
        self._setup_ui()
        self.load_week(self.week_start)
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 周导航
        nav_layout = QHBoxLayout()
        
        self.prev_week_btn = QPushButton("◀ 上周")
        self.prev_week_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #f0f0f0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.prev_week_btn.clicked.connect(self._prev_week)
        nav_layout.addWidget(self.prev_week_btn)
        
        nav_layout.addStretch()
        
        self.week_label = QLabel()
        self.week_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        nav_layout.addWidget(self.week_label)
        
        nav_layout.addStretch()
        
        self.next_week_btn = QPushButton("下周 ▶")
        self.next_week_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #f0f0f0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.next_week_btn.clicked.connect(self._next_week)
        nav_layout.addWidget(self.next_week_btn)
        
        layout.addLayout(nav_layout)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        
        # ===== 计时统计部分 =====
        timer_section_label = QLabel("⏱ 计时统计")
        timer_section_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        scroll_layout.addWidget(timer_section_label)
        
        # 计时总体统计卡片
        self.timer_summary_frame = QFrame()
        self.timer_summary_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        timer_summary_layout = QVBoxLayout(self.timer_summary_frame)
        timer_summary_layout.setSpacing(8)
        
        self.total_time_label = QLabel()
        self.total_time_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.total_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_summary_layout.addWidget(self.total_time_label)
        
        self.total_count_label = QLabel()
        self.total_count_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8);")
        self.total_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_summary_layout.addWidget(self.total_count_label)
        
        scroll_layout.addWidget(self.timer_summary_frame)
        
        # 计时详细统计
        timer_stats_grid = QGridLayout()
        timer_stats_grid.setSpacing(8)
        
        self.avg_daily_card = self._create_stat_card("📊 日均时长", "0")
        timer_stats_grid.addWidget(self.avg_daily_card, 0, 0)
        
        self.active_days_card = self._create_stat_card("📅 活跃天数", "0")
        timer_stats_grid.addWidget(self.active_days_card, 0, 1)
        
        self.pomodoro_card = self._create_stat_card("🍅 番茄钟", "0")
        timer_stats_grid.addWidget(self.pomodoro_card, 1, 0)
        
        self.stopwatch_card = self._create_stat_card("⏱ 正计时", "0")
        timer_stats_grid.addWidget(self.stopwatch_card, 1, 1)
        
        scroll_layout.addLayout(timer_stats_grid)
        
        # ===== 应用使用统计部分 =====
        usage_section_label = QLabel("📊 应用使用统计")
        usage_section_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-top: 10px;")
        scroll_layout.addWidget(usage_section_label)
        
        # 应用使用总体统计卡片
        self.usage_summary_frame = QFrame()
        self.usage_summary_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #11998e, stop:1 #38ef7d);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        usage_summary_layout = QVBoxLayout(self.usage_summary_frame)
        usage_summary_layout.setSpacing(8)
        
        self.usage_total_time_label = QLabel()
        self.usage_total_time_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.usage_total_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        usage_summary_layout.addWidget(self.usage_total_time_label)
        
        self.usage_avg_label = QLabel()
        self.usage_avg_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8);")
        self.usage_avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        usage_summary_layout.addWidget(self.usage_avg_label)
        
        scroll_layout.addWidget(self.usage_summary_frame)
        
        # Top应用列表
        top_apps_label = QLabel("🏆 最常使用的应用")
        top_apps_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #666;")
        scroll_layout.addWidget(top_apps_label)
        
        self.top_apps_list = QListWidget()
        self.top_apps_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: none;
                border-radius: 10px;
                padding: 6px;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 8px;
                margin: 2px 0;
                padding: 8px 12px;
            }
        """)
        self.top_apps_list.setMaximumHeight(150)
        scroll_layout.addWidget(self.top_apps_list)
        
        # 每日详情
        daily_title = QLabel("📈 每日详情")
        daily_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-top: 8px;")
        scroll_layout.addWidget(daily_title)
        
        self.daily_list = QListWidget()
        self.daily_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: none;
                border-radius: 10px;
                padding: 6px;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 8px;
                margin: 2px 0;
                padding: 8px 12px;
            }
        """)
        self.daily_list.setMinimumHeight(150)
        scroll_layout.addWidget(self.daily_list)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def _create_stat_card(self, title, value):
        """创建统计卡片"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        value_label.setObjectName("value_label")
        layout.addWidget(value_label)
        
        return frame
    
    def _update_stat_card(self, card, value):
        """更新统计卡片的值"""
        value_label = card.findChild(QLabel, "value_label")
        if value_label:
            value_label.setText(value)
    
    def load_week(self, week_start):
        """加载周数据"""
        self.week_start = week_start
        week_end = week_start + timedelta(days=6)
        
        # 更新标题
        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        
        if week_start == current_week_start:
            week_str = "本周"
        elif week_start == current_week_start - timedelta(days=7):
            week_str = "上周"
        else:
            week_str = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"
        
        self.week_label.setText(f"📆 {week_str}")
        
        # ===== 加载计时统计 =====
        timer_summary = timer_storage.get_weekly_summary(week_start)
        
        # 更新计时总体统计
        total_duration = timer_summary['total_duration']
        hours = total_duration // 3600
        minutes = (total_duration % 3600) // 60
        if hours > 0:
            self.total_time_label.setText(f"{hours}小时{minutes}分钟")
        else:
            self.total_time_label.setText(f"{minutes}分钟")
        
        self.total_count_label.setText(f"共完成 {timer_summary['total_count']} 次计时")
        
        # 更新计时详细统计
        avg_daily = timer_summary['avg_daily_duration']
        avg_hours = avg_daily // 3600
        avg_minutes = (avg_daily % 3600) // 60
        if avg_hours > 0:
            self._update_stat_card(self.avg_daily_card, f"{avg_hours}h{avg_minutes}m")
        else:
            self._update_stat_card(self.avg_daily_card, f"{avg_minutes}分钟")
        
        self._update_stat_card(self.active_days_card, f"{timer_summary['active_days']}天")
        self._update_stat_card(self.pomodoro_card, f"{timer_summary['pomodoro_count']}次")
        self._update_stat_card(self.stopwatch_card, f"{timer_summary['stopwatch_count']}次")
        
        # ===== 加载应用使用统计 =====
        usage_summary = app_usage_storage.get_weekly_summary(week_start)
        
        # 更新应用使用总体统计
        usage_total = usage_summary['total_time']
        u_hours = usage_total // 3600
        u_minutes = (usage_total % 3600) // 60
        if u_hours > 0:
            self.usage_total_time_label.setText(f"{u_hours}小时{u_minutes}分钟")
        else:
            self.usage_total_time_label.setText(f"{u_minutes}分钟")
        
        avg_usage = usage_summary['avg_daily_time']
        avg_u_hours = avg_usage // 3600
        avg_u_minutes = (avg_usage % 3600) // 60
        if avg_u_hours > 0:
            self.usage_avg_label.setText(f"日均使用 {avg_u_hours}h{avg_u_minutes}m · {usage_summary['active_days']}天有数据")
        else:
            self.usage_avg_label.setText(f"日均使用 {avg_u_minutes}分钟 · {usage_summary['active_days']}天有数据")
        
        # 更新Top应用列表
        self.top_apps_list.clear()
        for i, app in enumerate(usage_summary.get('top_apps', [])[:5]):
            app_type_icons = {
                'browser': '🌐',
                'chat': '💬',
                'editor': '📝',
                'normal': '📱'
            }
            icon = app_type_icons.get(app['app_type'], '📱')
            text = f"{i+1}. {icon} {app['name']}   |   {app['time_str']}"
            item = QListWidgetItem(text)
            self.top_apps_list.addItem(item)
        
        if not usage_summary.get('top_apps'):
            item = QListWidgetItem("暂无应用使用数据")
            item.setForeground(Qt.GlobalColor.gray)
            self.top_apps_list.addItem(item)
        
        # 更新每日详情（合并计时和应用使用）
        self.daily_list.clear()
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            weekday = weekday_names[i]
            
            # 计时数据
            timer_data = timer_summary['daily_stats'].get(day, {'duration': 0, 'count': 0})
            timer_duration = timer_data['duration']
            timer_count = timer_data['count']
            
            # 应用使用数据
            usage_data = usage_summary.get('daily_totals', {}).get(day, {'total_time': 0})
            usage_time = usage_data.get('total_time', 0)
            
            # 格式化
            parts = []
            
            if timer_duration > 0:
                t_hours = timer_duration // 3600
                t_minutes = (timer_duration % 3600) // 60
                if t_hours > 0:
                    parts.append(f"⏱{t_hours}h{t_minutes}m({timer_count}次)")
                else:
                    parts.append(f"⏱{t_minutes}m({timer_count}次)")
            
            if usage_time > 0:
                uh = usage_time // 3600
                um = (usage_time % 3600) // 60
                if uh > 0:
                    parts.append(f"📊{uh}h{um}m")
                else:
                    parts.append(f"📊{um}m")
            
            if parts:
                text = f"{weekday} ({day.strftime('%m/%d')})   |   " + "   ".join(parts)
            else:
                text = f"{weekday} ({day.strftime('%m/%d')})   |   -"
            
            # 高亮今天
            if day == today:
                text = f"🔹 {text}"
            
            item = QListWidgetItem(text)
            self.daily_list.addItem(item)
    
    def _prev_week(self):
        """上一周"""
        self.week_start = self.week_start - timedelta(days=7)
        self.load_week(self.week_start)
    
    def _next_week(self):
        """下一周"""
        self.week_start = self.week_start + timedelta(days=7)
        self.load_week(self.week_start)
    
    def refresh(self):
        """刷新当前周"""
        self.load_week(self.week_start)


class CalendarDialog(QDialog):
    """日历对话框 - 独立窗口显示日历和统计"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📅 计时记录与统计")
        self.resize(650, 700)
        self.setStyleSheet("background-color: white;")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 左侧：日历和日记录
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # 日历
        self.calendar = CalendarWidget()
        self.calendar.date_selected.connect(self._on_date_selected)
        left_layout.addWidget(self.calendar)
        
        # 日记录
        self.day_records = DayRecordsWidget()
        left_layout.addWidget(self.day_records)
        
        layout.addWidget(left_panel)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        separator.setFixedWidth(1)
        layout.addWidget(separator)
        
        # 右侧：周总结
        self.weekly_summary = WeeklySummaryWidget()
        layout.addWidget(self.weekly_summary)
        
        # 设置比例
        layout.setStretch(0, 1)
        layout.setStretch(2, 1)
    
    def _on_date_selected(self, date):
        """日期选中处理"""
        self.day_records.load_date(date)
    
    def refresh(self):
        """刷新所有数据"""
        self.calendar.refresh()
        self.day_records.refresh()
        self.weekly_summary.refresh()