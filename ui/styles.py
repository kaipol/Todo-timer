"""
共享样式模块 - 提取UI组件中重复使用的样式常量
"""

# ============== 颜色常量 ==============
class Colors:
    """应用程序颜色常量"""
    # 主题色
    PRIMARY = "#4a90d9"
    PRIMARY_HOVER = "#5ba0e9"
    PRIMARY_DARK = "#3a80c9"
    
    # 背景色
    BG_DARK = "#1e1e1e"
    BG_MEDIUM = "#252526"
    BG_LIGHT = "#2d2d30"
    BG_LIGHTER = "#333337"
    BG_HOVER = "#3e3e42"
    BG_SELECTED = "#094771"
    
    # 文本色
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#cccccc"
    TEXT_MUTED = "#888888"
    TEXT_DARK = "#666666"
    
    # 边框色
    BORDER_DARK = "#3c3c3c"
    BORDER_LIGHT = "#555555"
    
    # 状态色
    SUCCESS = "#4CAF50"
    WARNING = "#FFC107"
    ERROR = "#f44336"
    INFO = "#2196F3"
    
    # 特殊色
    COMPLETED = "#888888"
    CHECKBOX_BG = "#3c3c3c"


# ============== 字体常量 ==============
class Fonts:
    """字体常量"""
    FAMILY_DEFAULT = "Microsoft YaHei, Segoe UI"
    FAMILY_MONO = "Consolas, Monaco, monospace"
    
    SIZE_SMALL = "11px"
    SIZE_NORMAL = "12px"
    SIZE_MEDIUM = "13px"
    SIZE_LARGE = "14px"
    SIZE_XLARGE = "16px"
    SIZE_TITLE = "18px"


# ============== 尺寸常量 ==============
class Sizes:
    """尺寸常量"""
    BORDER_RADIUS_SMALL = "3px"
    BORDER_RADIUS_NORMAL = "4px"
    BORDER_RADIUS_MEDIUM = "6px"
    BORDER_RADIUS_LARGE = "8px"
    
    PADDING_SMALL = "4px"
    PADDING_NORMAL = "8px"
    PADDING_MEDIUM = "10px"
    PADDING_LARGE = "12px"
    
    MARGIN_SMALL = "4px"
    MARGIN_NORMAL = "8px"
    MARGIN_MEDIUM = "10px"
    MARGIN_LARGE = "12px"


# ============== 通用样式模板 ==============
class StyleTemplates:
    """样式模板"""
    
    @staticmethod
    def button_primary() -> str:
        """主要按钮样式"""
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                padding: 8px 16px;
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                font-size: {Fonts.SIZE_MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_DARK};
            }}
        """
    
    @staticmethod
    def button_secondary() -> str:
        """次要按钮样式"""
        return f"""
            QPushButton {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER_DARK};
                padding: 8px 16px;
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                font-size: {Fonts.SIZE_MEDIUM};
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
                border-color: {Colors.BORDER_LIGHT};
            }}
        """
    
    @staticmethod
    def button_icon(size: int = 28) -> str:
        """图标按钮样式"""
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {size // 2}px;
                padding: 4px;
                min-width: {size}px;
                max-width: {size}px;
                min-height: {size}px;
                max-height: {size}px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """
    
    @staticmethod
    def input_field() -> str:
        """输入框样式"""
        return f"""
            QLineEdit {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                padding: 8px;
                font-size: {Fonts.SIZE_MEDIUM};
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """
    
    @staticmethod
    def text_edit() -> str:
        """文本编辑框样式"""
        return f"""
            QTextEdit {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                padding: 8px;
                font-size: {Fonts.SIZE_MEDIUM};
                font-family: {Fonts.FAMILY_DEFAULT};
            }}
            QTextEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """
    
    @staticmethod
    def plain_text_edit() -> str:
        """纯文本编辑框样式"""
        return f"""
            QPlainTextEdit {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                padding: 8px;
                font-size: {Fonts.SIZE_MEDIUM};
                font-family: {Fonts.FAMILY_DEFAULT};
            }}
            QPlainTextEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """
    
    @staticmethod
    def list_widget() -> str:
        """列表组件样式"""
        return f"""
            QListWidget {{
                background-color: {Colors.BG_MEDIUM};
                border: none;
                border-radius: {Sizes.BORDER_RADIUS_MEDIUM};
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                padding: 2px;
                margin: 2px 0;
            }}
            QListWidget::item:selected {{
                background-color: {Colors.BG_SELECTED};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
            }}
            QListWidget::item:hover {{
                background-color: {Colors.BG_HOVER};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
            }}
        """
    
    @staticmethod
    def scroll_area() -> str:
        """滚动区域样式"""
        return f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {Colors.BG_MEDIUM};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {Colors.BG_HOVER};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {Colors.BORDER_LIGHT};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background-color: {Colors.BG_MEDIUM};
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {Colors.BG_HOVER};
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {Colors.BORDER_LIGHT};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """
    
    @staticmethod
    def combo_box() -> str:
        """下拉框样式"""
        return f"""
            QComboBox {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                padding: 6px 10px;
                font-size: {Fonts.SIZE_MEDIUM};
                min-width: 100px;
            }}
            QComboBox:hover {{
                border-color: {Colors.BORDER_LIGHT};
            }}
            QComboBox:focus {{
                border-color: {Colors.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {Colors.TEXT_SECONDARY};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                selection-background-color: {Colors.PRIMARY};
                outline: none;
            }}
        """
    
    @staticmethod
    def spin_box() -> str:
        """数字输入框样式"""
        return f"""
            QSpinBox {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                padding: 6px;
                font-size: {Fonts.SIZE_MEDIUM};
            }}
            QSpinBox:focus {{
                border-color: {Colors.PRIMARY};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {Colors.BG_HOVER};
                border: none;
                width: 16px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {Colors.BORDER_LIGHT};
            }}
        """
    
    @staticmethod
    def checkbox() -> str:
        """复选框样式"""
        return f"""
            QCheckBox {{
                color: {Colors.TEXT_PRIMARY};
                spacing: 8px;
                font-size: {Fonts.SIZE_MEDIUM};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: {Sizes.BORDER_RADIUS_SMALL};
                border: 2px solid {Colors.BORDER_LIGHT};
                background-color: {Colors.CHECKBOX_BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Colors.PRIMARY};
            }}
        """
    
    @staticmethod
    def label_title() -> str:
        """标题标签样式"""
        return f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.SIZE_TITLE};
                font-weight: bold;
                font-family: {Fonts.FAMILY_DEFAULT};
            }}
        """
    
    @staticmethod
    def label_subtitle() -> str:
        """副标题标签样式"""
        return f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Fonts.SIZE_LARGE};
                font-family: {Fonts.FAMILY_DEFAULT};
            }}
        """
    
    @staticmethod
    def label_normal() -> str:
        """普通标签样式"""
        return f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.SIZE_MEDIUM};
                font-family: {Fonts.FAMILY_DEFAULT};
            }}
        """
    
    @staticmethod
    def label_muted() -> str:
        """弱化标签样式"""
        return f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: {Fonts.SIZE_NORMAL};
                font-family: {Fonts.FAMILY_DEFAULT};
            }}
        """
    
    @staticmethod
    def dialog() -> str:
        """对话框样式"""
        return f"""
            QDialog {{
                background-color: {Colors.BG_DARK};
            }}
        """
    
    @staticmethod
    def frame_card() -> str:
        """卡片框架样式"""
        return f"""
            QFrame {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_MEDIUM};
                padding: {Sizes.PADDING_MEDIUM};
            }}
        """
    
    @staticmethod
    def group_box() -> str:
        """分组框样式"""
        return f"""
            QGroupBox {{
                background-color: {Colors.BG_MEDIUM};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_MEDIUM};
                margin-top: 12px;
                padding-top: 8px;
                font-size: {Fonts.SIZE_MEDIUM};
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                color: {Colors.TEXT_SECONDARY};
            }}
        """
    
    @staticmethod
    def tab_widget() -> str:
        """标签页组件样式"""
        return f"""
            QTabWidget::pane {{
                background-color: {Colors.BG_MEDIUM};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_MEDIUM};
            }}
            QTabBar::tab {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER_DARK};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: {Sizes.BORDER_RADIUS_NORMAL};
                border-top-right-radius: {Sizes.BORDER_RADIUS_NORMAL};
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.BG_MEDIUM};
                color: {Colors.TEXT_PRIMARY};
                border-bottom-color: {Colors.BG_MEDIUM};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Colors.BG_HOVER};
            }}
        """


# ============== 特定组件样式 ==============
class MemoStyles:
    """备忘录组件专用样式"""
    
    @staticmethod
    def item_widget(completed: bool = False) -> str:
        """备忘录项样式"""
        text_color = Colors.COMPLETED if completed else Colors.TEXT_PRIMARY
        return f"""
            QWidget {{
                background-color: {Colors.BG_LIGHT};
                border-radius: {Sizes.BORDER_RADIUS_MEDIUM};
            }}
            QLabel {{
                color: {text_color};
                font-size: {Fonts.SIZE_MEDIUM};
            }}
        """
    
    @staticmethod
    def checkbox_custom() -> str:
        """自定义复选框样式"""
        return f"""
            QCheckBox {{
                spacing: 0px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {Colors.BORDER_LIGHT};
                background-color: {Colors.CHECKBOX_BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Colors.PRIMARY};
            }}
        """


class DiaryStyles:
    """日记组件专用样式"""
    
    @staticmethod
    def entry_item() -> str:
        """日记条目样式"""
        return f"""
            QFrame {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_MEDIUM};
            }}
            QFrame:hover {{
                border-color: {Colors.PRIMARY};
                background-color: {Colors.BG_LIGHTER};
            }}
        """
    
    @staticmethod
    def markdown_editor() -> str:
        """Markdown编辑器样式"""
        return f"""
            QPlainTextEdit {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                padding: 12px;
                font-family: {Fonts.FAMILY_MONO};
                font-size: {Fonts.SIZE_LARGE};
                line-height: 1.6;
            }}
            QPlainTextEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """
    
    @staticmethod
    def preview_area() -> str:
        """预览区域样式"""
        return f"""
            QTextEdit {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                padding: 12px;
                font-family: {Fonts.FAMILY_DEFAULT};
                font-size: {Fonts.SIZE_LARGE};
            }}
        """


class CalendarStyles:
    """日历组件专用样式"""
    
    @staticmethod
    def day_cell(is_today: bool = False, has_records: bool = False) -> str:
        """日期单元格样式"""
        if is_today:
            bg_color = Colors.PRIMARY
            text_color = Colors.TEXT_PRIMARY
        elif has_records:
            bg_color = Colors.BG_LIGHTER
            text_color = Colors.TEXT_PRIMARY
        else:
            bg_color = Colors.BG_LIGHT
            text_color = Colors.TEXT_SECONDARY
        
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: {Sizes.BORDER_RADIUS_NORMAL};
                font-size: {Fonts.SIZE_MEDIUM};
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """
    
    @staticmethod
    def summary_card() -> str:
        """摘要卡片样式"""
        return f"""
            QFrame {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: {Sizes.BORDER_RADIUS_LARGE};
                padding: {Sizes.PADDING_LARGE};
            }}
        """
    
    @staticmethod
    def stat_value() -> str:
        """统计数值样式"""
        return f"""
            QLabel {{
                color: {Colors.PRIMARY};
                font-size: 24px;
                font-weight: bold;
            }}
        """
