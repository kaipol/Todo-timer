"""
设置对话框模块 - 自定义应用图标和背景
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QFileDialog, QColorDialog,
                              QRadioButton, QButtonGroup, QWidget, QSlider,
                              QCheckBox, QScrollArea, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QIcon
import os

from core.config import app_config


class SettingsDialog(QDialog):
    """设置对话框"""
    
    settings_changed = pyqtSignal()  # 设置改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(480, 620)
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
        
        self.settings_changed.emit()
        self.accept()