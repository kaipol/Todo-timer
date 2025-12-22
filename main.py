"""
Time Tracker - 应用使用时间追踪器
入口文件
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from core.utils import create_app_icon
from core.config import app_config
from ui.main_window import MainWindow

# 应用唯一标识符
APP_UNIQUE_ID = "TimeTracker_SingleInstance_7a8b9c0d"


def is_already_running():
    """检查应用是否已经在运行（使用本地套接字）"""
    socket = QLocalSocket()
    socket.connectToServer(APP_UNIQUE_ID)
    if socket.waitForConnected(500):
        # 已有实例运行
        socket.disconnectFromServer()
        return True
    return False


def main():
    """应用程序入口"""
    app = QApplication(sys.argv)
    
    # 单实例检查
    if is_already_running():
        QMessageBox.warning(None, "Time Tracker", "应用程序已在运行中！")
        sys.exit(0)
    
    # 创建本地服务器，防止其他实例启动
    local_server = QLocalServer()
    # 清理可能存在的旧连接
    QLocalServer.removeServer(APP_UNIQUE_ID)
    if not local_server.listen(APP_UNIQUE_ID):
        print(f"无法创建本地服务器: {local_server.errorString()}")
    
    # 设置应用图标（优先使用自定义图标）
    custom_icon = app_config.get('app_icon', '')
    if custom_icon and os.path.exists(custom_icon):
        app_icon = QIcon(custom_icon)
    else:
        app_icon = create_app_icon()
    app.setWindowIcon(app_icon)
    
    # 设置全局字体
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()