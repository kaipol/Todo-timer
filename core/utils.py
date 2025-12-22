"""
工具函数模块 - 图标提取和创建
"""
import math
import win32gui
import win32ui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QImage, QPen


def create_app_icon():
    """创建应用程序图标（时钟样式）"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 绘制圆形背景
    painter.setBrush(QColor("#007bff"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 60, 60)
    
    # 绘制内圈
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(8, 8, 48, 48)
    
    # 绘制时钟刻度
    painter.setPen(QColor("#007bff"))
    center_x, center_y = 32, 32
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = center_x + 20 * math.cos(angle)
        y1 = center_y + 20 * math.sin(angle)
        x2 = center_x + 18 * math.cos(angle)
        y2 = center_y + 18 * math.sin(angle)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    # 绘制时针（指向10点）
    pen = QPen(QColor("#2c3e50"))
    pen.setWidth(3)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(32, 32, 24, 20)
    
    # 绘制分针（指向2点）
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawLine(32, 32, 42, 18)
    
    # 绘制中心点
    painter.setBrush(QColor("#007bff"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(29, 29, 6, 6)
    
    painter.end()
    
    return QIcon(pixmap)


def get_icon_from_exe(path):
    """从 exe 文件提取图标"""
    try:
        large, small = win32gui.ExtractIconEx(path, 0)
        if large:
            hIcon = large[0]
        elif small:
            hIcon = small[0]
        else:
            return None

        # 将 HICON 转换为 QPixmap
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        
        # DrawIconEx
        win32gui.DrawIconEx(hdc.GetHandleOutput(), 0, 0, hIcon, 32, 32, 0, None, 3)
        
        # Convert to PIL
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        from PIL import Image
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        
        # Convert PIL to QPixmap
        data = img.tobytes("raw", "RGBA")
        qim = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qim)
        
        win32gui.DestroyIcon(hIcon)
        return pixmap

    except Exception:
        return None


def format_time(seconds):
    """格式化时间为 HH:MM:SS"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"