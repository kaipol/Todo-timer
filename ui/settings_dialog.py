"""
设置对话框模块 - 自定义应用图标和背景
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QFileDialog, QColorDialog,
                              QRadioButton, QButtonGroup, QWidget, QSlider,
                              QCheckBox, QScrollArea, QTabWidget, QLineEdit,
                              QSpinBox, QMessageBox, QListWidget, QListWidgetItem,
                              QProgressDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QPixmap, QColor, QIcon
import os

from core.config import app_config
from core.webdav_sync import webdav_sync


class SettingsDialog(QDialog):
    """设置对话框"""
    
    settings_changed = pyqtSignal()  # 设置改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(520, 720)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("⚙️ 个性化设置")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 5, 0)
        scroll_layout.setSpacing(12)
        
        # === 界面背景设置（主要功能）===
        bg_main_section = self._create_section("🖼️ 界面背景")
        
        # 说明文字
        bg_tip = QLabel("设置整个应用窗口的背景（图片/颜色/渐变）")
        bg_tip.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 5px;")
        bg_main_section.layout().addWidget(bg_tip)
        
        # 启用全局背景复选框
        self.global_bg_enable_check = QCheckBox("启用全局背景")
        self.global_bg_enable_check.setStyleSheet("font-size: 13px; font-weight: bold; color: #495057;")
        self.global_bg_enable_check.stateChanged.connect(self._on_global_bg_enable_changed)
        bg_main_section.layout().addWidget(self.global_bg_enable_check)
        
        # 背景类型选择
        self.global_bg_type_group = QButtonGroup(self)
        
        self.global_image_radio = QRadioButton("图片背景")
        self.global_color_radio = QRadioButton("纯色背景")
        self.global_gradient_radio = QRadioButton("渐变背景")
        
        self.global_bg_type_group.addButton(self.global_image_radio, 0)
        self.global_bg_type_group.addButton(self.global_color_radio, 1)
        self.global_bg_type_group.addButton(self.global_gradient_radio, 2)
        
        radio_layout = QHBoxLayout()
        for radio in [self.global_image_radio, self.global_color_radio, self.global_gradient_radio]:
            radio.setStyleSheet("font-size: 13px;")
            radio_layout.addWidget(radio)
        radio_layout.addStretch()
        bg_main_section.layout().addLayout(radio_layout)
        
        # 背景预览和控制
        global_bg_control = QHBoxLayout()
        
        self.global_bg_preview = QLabel()
        self.global_bg_preview.setFixedSize(160, 100)
        self.global_bg_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f0f0f0;
            }
        """)
        self.global_bg_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.global_bg_preview.setText("点击右侧按钮\n选择背景")
        global_bg_control.addWidget(self.global_bg_preview)
        
        global_btn_layout = QVBoxLayout()
        global_btn_layout.setSpacing(8)
        
        # 图片选择按钮
        self.global_image_btn = QPushButton("📷 选择图片")
        self.global_image_btn.clicked.connect(self._select_global_bg_image)
        
        # 颜色选择按钮
        self.global_color_btn = QPushButton("🎨 选择颜色")
        self.global_color_btn.clicked.connect(self._select_global_bg_color)
        
        # 渐变颜色按钮
        self.global_gradient_btn1 = QPushButton("颜色1")
        self.global_gradient_btn1.clicked.connect(lambda: self._select_global_gradient_color(0))
        self.global_gradient_btn2 = QPushButton("颜色2")
        self.global_gradient_btn2.clicked.connect(lambda: self._select_global_gradient_color(1))
        
        # 清除背景按钮
        self.clear_bg_btn = QPushButton("🗑️ 清除背景")
        self.clear_bg_btn.clicked.connect(self._clear_global_bg)
        
        for btn in [self.global_image_btn, self.global_color_btn,
                    self.global_gradient_btn1, self.global_gradient_btn2, self.clear_bg_btn]:
            btn.setFixedWidth(110)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    background: white;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                    border-color: #007bff;
                }
            """)
        
        self.clear_bg_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                border: 1px solid #dc3545;
                border-radius: 6px;
                background: white;
                font-size: 12px;
                color: #dc3545;
            }
            QPushButton:hover {
                background: #dc3545;
                color: white;
            }
        """)
        
        global_btn_layout.addWidget(self.global_image_btn)
        global_btn_layout.addWidget(self.global_color_btn)
        global_btn_layout.addWidget(self.global_gradient_btn1)
        global_btn_layout.addWidget(self.global_gradient_btn2)
        global_btn_layout.addWidget(self.clear_bg_btn)
        
        global_bg_control.addLayout(global_btn_layout)
        global_bg_control.addStretch()
        bg_main_section.layout().addLayout(global_bg_control)
        
        scroll_layout.addWidget(bg_main_section)
        
        # 连接信号
        self.global_bg_type_group.buttonClicked.connect(self._on_global_bg_type_changed)
        
        # === 背景效果设置 ===
        effect_section = self._create_section("✨ 背景效果")
        
        # 模糊度
        blur_layout = QHBoxLayout()
        blur_label = QLabel("模糊度:")
        blur_label.setStyleSheet("font-size: 13px;")
        blur_label.setFixedWidth(70)
        blur_layout.addWidget(blur_label)
        
        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(0, 50)
        self.blur_slider.setValue(0)
        self.blur_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ddd;
                height: 6px;
                background: #f0f0f0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007bff;
                border: none;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #0056b3;
            }
        """)
        self.blur_slider.valueChanged.connect(self._on_blur_changed)
        blur_layout.addWidget(self.blur_slider)
        
        self.blur_value_label = QLabel("0")
        self.blur_value_label.setFixedWidth(30)
        self.blur_value_label.setStyleSheet("font-size: 13px; color: #007bff; font-weight: bold;")
        blur_layout.addWidget(self.blur_value_label)
        
        effect_section.layout().addLayout(blur_layout)
        
        # 内容透明度
        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("内容透明:")
        opacity_label.setStyleSheet("font-size: 13px;")
        opacity_label.setFixedWidth(70)
        opacity_layout.addWidget(opacity_label)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(85)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ddd;
                height: 6px;
                background: #f0f0f0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #28a745;
                border: none;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #1e7e34;
            }
        """)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        
        self.opacity_value_label = QLabel("85%")
        self.opacity_value_label.setFixedWidth(45)
        self.opacity_value_label.setStyleSheet("font-size: 13px; color: #28a745; font-weight: bold;")
        opacity_layout.addWidget(self.opacity_value_label)
        
        effect_section.layout().addLayout(opacity_layout)
        
        opacity_tip = QLabel("💡 降低透明度可让背景更明显（0%完全透明，100%不透明）")
        opacity_tip.setStyleSheet("font-size: 11px; color: #888;")
        effect_section.layout().addWidget(opacity_tip)
        
        scroll_layout.addWidget(effect_section)
        
        # === 计时器背景设置 ===
        timer_section = self._create_section("🍅 计时器背景")
        
        timer_tip = QLabel("单独设置计时器区域的背景（图片/颜色/渐变）")
        timer_tip.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 5px;")
        timer_section.layout().addWidget(timer_tip)
        
        # 背景类型选择
        self.bg_type_group = QButtonGroup(self)
        
        self.timer_image_radio = QRadioButton("图片背景")
        self.gradient_radio = QRadioButton("渐变色")
        self.color_radio = QRadioButton("纯色")
        
        self.bg_type_group.addButton(self.timer_image_radio, 0)
        self.bg_type_group.addButton(self.gradient_radio, 1)
        self.bg_type_group.addButton(self.color_radio, 2)
        
        timer_radio_layout = QHBoxLayout()
        for radio in [self.timer_image_radio, self.gradient_radio, self.color_radio]:
            radio.setStyleSheet("font-size: 13px;")
            timer_radio_layout.addWidget(radio)
        timer_radio_layout.addStretch()
        timer_section.layout().addLayout(timer_radio_layout)
        
        # 背景预览和控制
        timer_bg_control = QHBoxLayout()
        
        self.bg_preview = QLabel()
        self.bg_preview.setFixedSize(100, 60)
        self.bg_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 8px;
            }
        """)
        self.bg_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_bg_control.addWidget(self.bg_preview)
        
        timer_btn_layout = QVBoxLayout()
        
        # 图片选择按钮
        self.timer_image_btn = QPushButton("📷 选择图片")
        self.timer_image_btn.clicked.connect(self._select_timer_bg_image)
        
        # 渐变色设置
        self.gradient_btn1 = QPushButton("颜色1")
        self.gradient_btn1.clicked.connect(lambda: self._select_gradient_color(0))
        self.gradient_btn2 = QPushButton("颜色2")
        self.gradient_btn2.clicked.connect(lambda: self._select_gradient_color(1))
        
        # 纯色设置
        self.color_btn = QPushButton("选择颜色")
        self.color_btn.clicked.connect(self._select_bg_color)
        
        for btn in [self.timer_image_btn, self.gradient_btn1, self.gradient_btn2, self.color_btn]:
            btn.setFixedWidth(90)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 5px 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: white;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                    border-color: #007bff;
                }
            """)
        
        timer_btn_layout.addWidget(self.timer_image_btn)
        timer_btn_layout.addWidget(self.gradient_btn1)
        timer_btn_layout.addWidget(self.gradient_btn2)
        timer_btn_layout.addWidget(self.color_btn)
        
        timer_bg_control.addLayout(timer_btn_layout)
        timer_bg_control.addStretch()
        timer_section.layout().addLayout(timer_bg_control)
        
        scroll_layout.addWidget(timer_section)
        
        # 连接信号
        self.bg_type_group.buttonClicked.connect(self._on_bg_type_changed)
        
        # === 应用图标设置 ===
        icon_section = self._create_section("📱 应用图标")
        icon_layout = QHBoxLayout()
        
        # 图标预览
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(50, 50)
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_preview.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
        """)
        icon_layout.addWidget(self.icon_preview)
        
        icon_btn_layout = QHBoxLayout()
        self.select_icon_btn = QPushButton("选择图标")
        self.select_icon_btn.clicked.connect(self._select_icon)
        self.clear_icon_btn = QPushButton("恢复默认")
        self.clear_icon_btn.clicked.connect(self._clear_icon)
        
        for btn in [self.select_icon_btn, self.clear_icon_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    background: white;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                    border-color: #007bff;
                }
            """)
        
        icon_btn_layout.addWidget(self.select_icon_btn)
        icon_btn_layout.addWidget(self.clear_icon_btn)
        icon_btn_layout.addStretch()
        icon_layout.addLayout(icon_btn_layout)
        
        icon_section.layout().addLayout(icon_layout)
        scroll_layout.addWidget(icon_section)
        
        # === WebDAV 同步设置 ===
        webdav_section = self._create_section("☁️ WebDAV 同步")
        
        webdav_tip = QLabel("将待办、计时记录等数据同步到WebDAV服务器")
        webdav_tip.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 5px;")
        webdav_section.layout().addWidget(webdav_tip)
        
        # 启用开关
        enable_layout = QHBoxLayout()
        self.webdav_enable_check = QCheckBox("启用WebDAV同步")
        self.webdav_enable_check.setStyleSheet("font-size: 13px;")
        enable_layout.addWidget(self.webdav_enable_check)
        enable_layout.addStretch()
        
        # 同步状态
        self.sync_status_label = QLabel()
        self.sync_status_label.setStyleSheet("font-size: 11px; color: #666;")
        enable_layout.addWidget(self.sync_status_label)
        webdav_section.layout().addLayout(enable_layout)
        
        # 服务器地址
        server_layout = QHBoxLayout()
        server_label = QLabel("服务器:")
        server_label.setFixedWidth(60)
        server_label.setStyleSheet("font-size: 13px;")
        server_layout.addWidget(server_label)
        
        self.webdav_server_input = QLineEdit()
        self.webdav_server_input.setPlaceholderText("https://dav.example.com/webdav")
        self.webdav_server_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        server_layout.addWidget(self.webdav_server_input)
        webdav_section.layout().addLayout(server_layout)
        
        # 用户名
        user_layout = QHBoxLayout()
        user_label = QLabel("用户名:")
        user_label.setFixedWidth(60)
        user_label.setStyleSheet("font-size: 13px;")
        user_layout.addWidget(user_label)
        
        self.webdav_user_input = QLineEdit()
        self.webdav_user_input.setPlaceholderText("用户名")
        self.webdav_user_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        user_layout.addWidget(self.webdav_user_input)
        webdav_section.layout().addLayout(user_layout)
        
        # 密码
        pass_layout = QHBoxLayout()
        pass_label = QLabel("密码:")
        pass_label.setFixedWidth(60)
        pass_label.setStyleSheet("font-size: 13px;")
        pass_layout.addWidget(pass_label)
        
        self.webdav_pass_input = QLineEdit()
        self.webdav_pass_input.setPlaceholderText("密码")
        self.webdav_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.webdav_pass_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        pass_layout.addWidget(self.webdav_pass_input)
        webdav_section.layout().addLayout(pass_layout)
        
        # 远程路径
        path_layout = QHBoxLayout()
        path_label = QLabel("远程路径:")
        path_label.setFixedWidth(60)
        path_label.setStyleSheet("font-size: 13px;")
        path_layout.addWidget(path_label)
        
        self.webdav_path_input = QLineEdit()
        self.webdav_path_input.setPlaceholderText("/TimeTracker/")
        self.webdav_path_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        path_layout.addWidget(self.webdav_path_input)
        webdav_section.layout().addLayout(path_layout)
        
        # 操作按钮
        webdav_btn_layout = QHBoxLayout()
        webdav_btn_layout.setSpacing(8)
        
        self.test_conn_btn = QPushButton("🔗 测试连接")
        self.test_conn_btn.clicked.connect(self._test_webdav_connection)
        
        self.sync_now_btn = QPushButton("☁️ 立即同步")
        self.sync_now_btn.clicked.connect(self._sync_now)
        
        self.view_backups_btn = QPushButton("📋 查看备份")
        self.view_backups_btn.clicked.connect(self._view_remote_backups)
        
        for btn in [self.test_conn_btn, self.sync_now_btn, self.view_backups_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    background: white;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                    border-color: #007bff;
                }
            """)
        
        webdav_btn_layout.addWidget(self.test_conn_btn)
        webdav_btn_layout.addWidget(self.sync_now_btn)
        webdav_btn_layout.addWidget(self.view_backups_btn)
        webdav_btn_layout.addStretch()
        webdav_section.layout().addLayout(webdav_btn_layout)
        
        scroll_layout.addWidget(webdav_section)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # === 底部按钮 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.reset_btn = QPushButton("重置所有")
        self.reset_btn.clicked.connect(self._reset_all)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #dc3545;
                border-radius: 6px;
                background: white;
                color: #dc3545;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #dc3545;
                color: white;
            }
        """)
        
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                background: #007bff;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
        # 临时存储设置
        self.temp_icon = ''
        self.temp_bg_type = 'gradient'
        self.temp_bg_color = '#667eea'
        self.temp_bg_gradient = ['#667eea', '#764ba2']
        self.temp_bg_image = ''
        # 全局背景临时设置
        self.temp_global_bg_enabled = False
        self.temp_global_bg_type = 'image'
        self.temp_global_bg_image = ''
        self.temp_global_bg_color = '#f8f9fa'
        self.temp_global_bg_gradient = ['#e0e5ec', '#f8f9fa']
        self.temp_global_bg_blur = 0
        self.temp_global_bg_opacity = 0.85
    
    def _clear_global_bg(self):
        """清除全局背景"""
        self.temp_global_bg_enabled = False
        self.temp_global_bg_image = ''
        self.global_bg_preview.clear()
        self.global_bg_preview.setText("点击右侧按钮\n选择背景")
        self.global_bg_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f0f0f0;
                color: #999;
                font-size: 11px;
            }
        """)
    
    def _create_section(self, title):
        """创建设置区块"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        
        label = QLabel(title)
        label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        layout.addWidget(label)
        
        return frame
    
    def _load_current_settings(self):
        """加载当前设置"""
        # 加载图标
        self.temp_icon = app_config.get('app_icon', '')
        self._update_icon_preview()
        
        # 加载计时器背景设置
        self.temp_bg_type = app_config.get('background_type', 'gradient')
        self.temp_bg_color = app_config.get('background_color', '#667eea')
        self.temp_bg_gradient = app_config.get('background_gradient', ['#667eea', '#764ba2'])
        self.temp_bg_image = app_config.get('background_image', '')
        
        # 设置单选按钮
        if self.temp_bg_type == 'image':
            self.timer_image_radio.setChecked(True)
        elif self.temp_bg_type == 'gradient':
            self.gradient_radio.setChecked(True)
        elif self.temp_bg_type == 'color':
            self.color_radio.setChecked(True)
        
        self._on_bg_type_changed()
        self._update_bg_preview()
        
        # 加载全局背景设置
        self.temp_global_bg_enabled = app_config.get('global_bg_enabled', False)
        self.temp_global_bg_type = app_config.get('global_bg_type', 'image')
        self.temp_global_bg_image = app_config.get('global_bg_image', '')
        self.temp_global_bg_color = app_config.get('global_bg_color', '#f8f9fa')
        self.temp_global_bg_gradient = app_config.get('global_bg_gradient', ['#e0e5ec', '#f8f9fa'])
        self.temp_global_bg_blur = app_config.get('global_bg_blur', 0)
        self.temp_global_bg_opacity = app_config.get('global_bg_opacity', 0.85)
        
        # 设置启用全局背景复选框状态
        self.global_bg_enable_check.setChecked(self.temp_global_bg_enabled)
        
        # 设置UI状态
        if self.temp_global_bg_type == 'image':
            self.global_image_radio.setChecked(True)
        elif self.temp_global_bg_type == 'color':
            self.global_color_radio.setChecked(True)
        else:
            self.global_gradient_radio.setChecked(True)
        
        self.blur_slider.setValue(self.temp_global_bg_blur)
        self.blur_value_label.setText(str(self.temp_global_bg_blur))
        
        opacity_percent = int(self.temp_global_bg_opacity * 100)
        self.opacity_slider.setValue(opacity_percent)
        self.opacity_value_label.setText(f"{opacity_percent}%")
        
        self._on_global_bg_type_changed()
        self._update_global_bg_preview()
        
        # 加载WebDAV设置
        self._load_webdav_settings()
    
    def _update_icon_preview(self):
        """更新图标预览"""
        if self.temp_icon and os.path.exists(self.temp_icon):
            pixmap = QPixmap(self.temp_icon)
            self.icon_preview.setPixmap(pixmap.scaled(
                60, 60, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.icon_preview.setText("默认")
            self.icon_preview.setStyleSheet("""
                QLabel {
                    background-color: #f0f0f0;
                    border: 2px dashed #ccc;
                    border-radius: 8px;
                    color: #999;
                    font-size: 12px;
                }
            """)
    
    def _update_bg_preview(self):
        """更新背景预览"""
        if self.temp_bg_type == 'image':
            if self.temp_bg_image and os.path.exists(self.temp_bg_image):
                pixmap = QPixmap(self.temp_bg_image)
                self.bg_preview.setPixmap(pixmap.scaled(
                    96, 56,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.bg_preview.setStyleSheet("""
                    QLabel {
                        border: 2px solid #ddd;
                        border-radius: 8px;
                    }
                """)
            else:
                self.bg_preview.clear()
                self.bg_preview.setText("点击选择图片")
                self.bg_preview.setStyleSheet("""
                    QLabel {
                        background-color: #f0f0f0;
                        border: 2px solid #ddd;
                        border-radius: 8px;
                        color: #999;
                        font-size: 10px;
                    }
                """)
        elif self.temp_bg_type == 'gradient':
            self.bg_preview.clear()
            c1, c2 = self.temp_bg_gradient
            self.bg_preview.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {c1}, stop:1 {c2});
                    border: 2px solid #ddd;
                    border-radius: 8px;
                }}
            """)
        elif self.temp_bg_type == 'color':
            self.bg_preview.clear()
            self.bg_preview.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.temp_bg_color};
                    border: 2px solid #ddd;
                    border-radius: 8px;
                }}
            """)
    
    def _on_bg_type_changed(self):
        """计时器背景类型改变"""
        is_image = self.timer_image_radio.isChecked()
        is_gradient = self.gradient_radio.isChecked()
        is_color = self.color_radio.isChecked()
        
        self.timer_image_btn.setVisible(is_image)
        self.gradient_btn1.setVisible(is_gradient)
        self.gradient_btn2.setVisible(is_gradient)
        self.color_btn.setVisible(is_color)
        
        if is_image:
            self.temp_bg_type = 'image'
        elif is_gradient:
            self.temp_bg_type = 'gradient'
        elif is_color:
            self.temp_bg_type = 'color'
        
        self._update_bg_preview()
    
    def _on_global_bg_type_changed(self):
        """全局背景类型改变"""
        is_image = self.global_image_radio.isChecked()
        is_color = self.global_color_radio.isChecked()
        is_gradient = self.global_gradient_radio.isChecked()
        
        self.global_image_btn.setVisible(is_image)
        self.global_color_btn.setVisible(is_color)
        self.global_gradient_btn1.setVisible(is_gradient)
        self.global_gradient_btn2.setVisible(is_gradient)
        
        if is_image:
            self.temp_global_bg_type = 'image'
        elif is_color:
            self.temp_global_bg_type = 'color'
        else:
            self.temp_global_bg_type = 'gradient'
        
        self._update_global_bg_preview()
    
    def _update_global_bg_preview(self):
        """更新全局背景预览"""
        if self.temp_global_bg_type == 'image':
            if self.temp_global_bg_image and os.path.exists(self.temp_global_bg_image):
                pixmap = QPixmap(self.temp_global_bg_image)
                self.global_bg_preview.setPixmap(pixmap.scaled(
                    136, 86,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                self.global_bg_preview.setText("无图片")
                self.global_bg_preview.setStyleSheet("""
                    QLabel {
                        background-color: #f0f0f0;
                        border: 2px solid #ddd;
                        border-radius: 8px;
                        color: #999;
                    }
                """)
        elif self.temp_global_bg_type == 'color':
            self.global_bg_preview.clear()
            self.global_bg_preview.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.temp_global_bg_color};
                    border: 2px solid #ddd;
                    border-radius: 8px;
                }}
            """)
        else:
            c1, c2 = self.temp_global_bg_gradient
            self.global_bg_preview.clear()
            self.global_bg_preview.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {c1}, stop:1 {c2});
                    border: 2px solid #ddd;
                    border-radius: 8px;
                }}
            """)
    
    def _select_global_bg_image(self):
        """选择全局背景图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
        )
        if file_path:
            self.temp_global_bg_image = file_path
            self.temp_global_bg_enabled = True  # 自动启用全局背景
            self.temp_global_bg_type = 'image'
            self.global_image_radio.setChecked(True)
            self._update_global_bg_preview()
    
    def _select_global_bg_color(self):
        """选择全局背景颜色"""
        current_color = QColor(self.temp_global_bg_color)
        color = QColorDialog.getColor(current_color, self, "选择背景颜色")
        if color.isValid():
            self.temp_global_bg_color = color.name()
            self.temp_global_bg_enabled = True  # 自动启用全局背景
            self.temp_global_bg_type = 'color'
            self.global_color_radio.setChecked(True)
            self._update_global_bg_preview()
    
    def _select_global_gradient_color(self, index):
        """选择全局渐变颜色"""
        current_color = QColor(self.temp_global_bg_gradient[index])
        color = QColorDialog.getColor(current_color, self, "选择颜色")
        if color.isValid():
            self.temp_global_bg_gradient[index] = color.name()
            self.temp_global_bg_enabled = True  # 自动启用全局背景
            self.temp_global_bg_type = 'gradient'
            self.global_gradient_radio.setChecked(True)
            self._update_global_bg_preview()
    
    def _on_global_bg_enable_changed(self, state):
        """全局背景启用状态改变"""
        self.temp_global_bg_enabled = (state == Qt.CheckState.Checked.value)
    
    def _on_blur_changed(self, value):
        """模糊度改变"""
        self.temp_global_bg_blur = value
        self.blur_value_label.setText(str(value))
    
    def _on_opacity_changed(self, value):
        """透明度改变"""
        self.temp_global_bg_opacity = value / 100.0
        self.opacity_value_label.setText(f"{value}%")
    
    def _select_icon(self):
        """选择图标"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图标", "",
            "图片文件 (*.png *.jpg *.jpeg *.ico *.svg);;所有文件 (*.*)"
        )
        if file_path:
            self.temp_icon = file_path
            self._update_icon_preview()
    
    def _clear_icon(self):
        """清除自定义图标"""
        self.temp_icon = ''
        self._update_icon_preview()
    
    def _select_gradient_color(self, index):
        """选择渐变颜色"""
        current_color = QColor(self.temp_bg_gradient[index])
        color = QColorDialog.getColor(current_color, self, "选择颜色")
        if color.isValid():
            self.temp_bg_gradient[index] = color.name()
            self._update_bg_preview()
    
    def _select_bg_color(self):
        """选择背景颜色"""
        current_color = QColor(self.temp_bg_color)
        color = QColorDialog.getColor(current_color, self, "选择背景颜色")
        if color.isValid():
            self.temp_bg_color = color.name()
            self._update_bg_preview()
    
    def _select_bg_image(self):
        """选择背景图片（已弃用，保留兼容）"""
        self._select_timer_bg_image()
    
    def _select_timer_bg_image(self):
        """选择计时器背景图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择计时器背景图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
        )
        if file_path:
            self.temp_bg_image = file_path
            self.temp_bg_type = 'image'
            self.timer_image_radio.setChecked(True)
            self._on_bg_type_changed()
            self._update_bg_preview()
    
    def _reset_all(self):
        """重置所有设置"""
        self.temp_icon = ''
        self.temp_bg_type = 'gradient'
        self.temp_bg_color = '#667eea'
        self.temp_bg_gradient = ['#667eea', '#764ba2']
        self.temp_bg_image = ''
        
        # 重置全局背景设置
        self.temp_global_bg_enabled = False
        self.temp_global_bg_type = 'image'
        self.temp_global_bg_image = ''
        self.temp_global_bg_color = '#f8f9fa'
        self.temp_global_bg_gradient = ['#e0e5ec', '#f8f9fa']
        self.temp_global_bg_blur = 0
        self.temp_global_bg_opacity = 0.85
        
        # 重置计时器背景UI
        self.gradient_radio.setChecked(True)
        self._on_bg_type_changed()
        self._update_icon_preview()
        self._update_bg_preview()
        
        # 重置全局背景UI
        self.global_image_radio.setChecked(True)
        self.blur_slider.setValue(0)
        self.blur_value_label.setText("0")
        self.opacity_slider.setValue(85)
        self.opacity_value_label.setText("85%")
        self._clear_global_bg()
        self._on_global_bg_type_changed()
    
    def _save_settings(self):
        """保存设置"""
        app_config.set('app_icon', self.temp_icon)
        app_config.set('background_type', self.temp_bg_type)
        app_config.set('background_color', self.temp_bg_color)
        app_config.set('background_gradient', self.temp_bg_gradient)
        app_config.set('background_image', self.temp_bg_image)
        
        # 保存全局背景设置
        app_config.set('global_bg_enabled', self.temp_global_bg_enabled)
        app_config.set('global_bg_type', self.temp_global_bg_type)
        app_config.set('global_bg_image', self.temp_global_bg_image)
        app_config.set('global_bg_color', self.temp_global_bg_color)
        app_config.set('global_bg_gradient', self.temp_global_bg_gradient)
        app_config.set('global_bg_blur', self.temp_global_bg_blur)
        app_config.set('global_bg_opacity', self.temp_global_bg_opacity)
        
        # 保存WebDAV设置
        self._save_webdav_settings()
        
        self.settings_changed.emit()
        self.accept()
    
    # === WebDAV 相关方法 ===
    
    def _load_webdav_settings(self):
        """加载WebDAV设置"""
        self.webdav_enable_check.setChecked(webdav_sync.get_config('enabled', False))
        self.webdav_server_input.setText(webdav_sync.get_config('server_url', ''))
        self.webdav_user_input.setText(webdav_sync.get_config('username', ''))
        self.webdav_pass_input.setText(webdav_sync.get_config('password', ''))
        self.webdav_path_input.setText(webdav_sync.get_config('remote_path', '/TimeTracker/'))
        
        # 更新同步状态显示
        self._update_sync_status()
    
    def _save_webdav_settings(self):
        """保存WebDAV设置"""
        webdav_sync.update_config(
            enabled=self.webdav_enable_check.isChecked(),
            server_url=self.webdav_server_input.text().strip(),
            username=self.webdav_user_input.text().strip(),
            password=self.webdav_pass_input.text(),
            remote_path=self.webdav_path_input.text().strip() or '/TimeTracker/'
        )
    
    def _update_sync_status(self):
        """更新同步状态显示"""
        sync_info = webdav_sync.get_last_sync_info()
        if sync_info['last_sync']:
            status_text = f"上次同步: {sync_info['last_sync_display']}"
            if sync_info['status'] == 'success':
                self.sync_status_label.setStyleSheet("font-size: 11px; color: #28a745;")
            else:
                self.sync_status_label.setStyleSheet("font-size: 11px; color: #dc3545;")
        else:
            status_text = "从未同步"
            self.sync_status_label.setStyleSheet("font-size: 11px; color: #666;")
        
        self.sync_status_label.setText(status_text)
    
    def _test_webdav_connection(self):
        """测试WebDAV连接"""
        # 先临时保存配置
        webdav_sync.update_config(
            server_url=self.webdav_server_input.text().strip(),
            username=self.webdav_user_input.text().strip(),
            password=self.webdav_pass_input.text(),
            remote_path=self.webdav_path_input.text().strip() or '/TimeTracker/'
        )
        
        # 测试连接
        self.test_conn_btn.setEnabled(False)
        self.test_conn_btn.setText("测试中...")
        
        # 使用QTimer延迟执行，避免UI卡顿
        QTimer.singleShot(100, self._do_test_connection)
    
    def _do_test_connection(self):
        """执行连接测试"""
        try:
            success, msg = webdav_sync.test_connection()
            
            if success:
                QMessageBox.information(self, "连接成功", "✅ WebDAV服务器连接成功！")
            else:
                QMessageBox.warning(self, "连接失败", f"❌ 连接失败:\n{msg}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试连接时发生错误:\n{str(e)}")
        finally:
            self.test_conn_btn.setEnabled(True)
            self.test_conn_btn.setText("🔗 测试连接")
    
    def _sync_now(self):
        """立即同步"""
        # 先保存当前配置
        self._save_webdav_settings()
        
        if not webdav_sync.is_configured():
            QMessageBox.warning(self, "未配置", "请先配置WebDAV服务器信息并启用同步")
            return
        
        # 确认同步
        reply = QMessageBox.question(
            self, "确认同步",
            "将把本地数据打包为ZIP并上传到WebDAV服务器。\n\n继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 执行同步
        self.sync_now_btn.setEnabled(False)
        self.sync_now_btn.setText("同步中...")
        
        QTimer.singleShot(100, self._do_sync)
    
    def _do_sync(self):
        """执行同步"""
        try:
            success, msg = webdav_sync.upload_backup()
            
            if success:
                QMessageBox.information(self, "同步成功", f"✅ {msg}")
            else:
                QMessageBox.warning(self, "同步失败", f"❌ {msg}")
            
            self._update_sync_status()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"同步时发生错误:\n{str(e)}")
        finally:
            self.sync_now_btn.setEnabled(True)
            self.sync_now_btn.setText("☁️ 立即同步")
    
    def _view_remote_backups(self):
        """查看远程备份"""
        # 先保存当前配置
        self._save_webdav_settings()
        
        if not webdav_sync.is_configured():
            QMessageBox.warning(self, "未配置", "请先配置WebDAV服务器信息并启用同步")
            return
        
        # 显示备份列表对话框
        dialog = BackupListDialog(self)
        dialog.exec()


class BackupListDialog(QDialog):
    """备份列表对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("远程备份列表")
        self.setFixedSize(450, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        self._setup_ui()
        self._load_backups()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("📋 远程备份列表")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # 提示
        tip = QLabel("选择一个备份可以下载并恢复数据")
        tip.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(tip)
        
        # 备份列表
        self.backup_list = QListWidget()
        self.backup_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                background-color: white;
                border-radius: 6px;
                margin: 3px 0;
                padding: 10px;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #d0e8ff;
                color: #333;
            }
        """)
        layout.addWidget(self.backup_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self._load_backups)
        
        self.restore_btn = QPushButton("📥 恢复选中")
        self.restore_btn.clicked.connect(self._restore_selected)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        for btn in [self.refresh_btn, self.restore_btn, self.close_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    background: white;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                    border-color: #007bff;
                }
            """)
        
        self.restore_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                background: #007bff;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.restore_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        
        # 存储备份数据
        self.backups = []
    
    def _load_backups(self):
        """加载备份列表"""
        self.backup_list.clear()
        self.backups = []
        
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("加载中...")
        
        QTimer.singleShot(100, self._do_load_backups)
    
    def _do_load_backups(self):
        """执行加载备份"""
        try:
            success, msg, backups = webdav_sync.list_remote_backups()
            
            if success:
                self.backups = backups
                
                if backups:
                    for backup in backups:
                        item = QListWidgetItem(
                            f"📦 {backup['filename']}\n    🕐 {backup['display_time']}"
                        )
                        item.setData(Qt.ItemDataRole.UserRole, backup['filename'])
                        self.backup_list.addItem(item)
                else:
                    self.backup_list.addItem(QListWidgetItem("📭 暂无备份"))
            else:
                self.backup_list.addItem(QListWidgetItem(f"❌ 加载失败: {msg}"))
        except Exception as e:
            self.backup_list.addItem(QListWidgetItem(f"❌ 错误: {str(e)}"))
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 刷新")
    
    def _restore_selected(self):
        """恢复选中的备份"""
        current_item = self.backup_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个备份")
            return
        
        filename = current_item.data(Qt.ItemDataRole.UserRole)
        if not filename:
            return
        
        # 确认恢复
        reply = QMessageBox.warning(
            self, "确认恢复",
            f"确定要从备份恢复数据吗？\n\n备份文件: {filename}\n\n⚠️ 这将覆盖当前的本地数据！\n恢复后需要重启应用才能生效。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 执行恢复
        self.restore_btn.setEnabled(False)
        self.restore_btn.setText("恢复中...")
        
        QTimer.singleShot(100, lambda: self._do_restore(filename))
    
    def _do_restore(self, filename):
        """执行恢复"""
        try:
            # 下载备份
            success, msg, local_path = webdav_sync.download_backup(filename)
            
            if not success:
                QMessageBox.warning(self, "下载失败", f"❌ {msg}")
                return
            
            # 恢复数据
            success, msg = webdav_sync.restore_from_backup(local_path)
            
            if success:
                QMessageBox.information(
                    self, "恢复成功",
                    f"✅ {msg}\n\n请重启应用以加载恢复的数据。"
                )
                self.close()
            else:
                QMessageBox.warning(self, "恢复失败", f"❌ {msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"恢复时发生错误:\n{str(e)}")
        finally:
            self.restore_btn.setEnabled(True)
            self.restore_btn.setText("📥 恢复选中")