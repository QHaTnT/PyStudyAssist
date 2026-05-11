# -*- coding: utf-8 -*-
"""
PyPalPrep 入口文件 - Python学习教辅系统

【文件功能说明】
这个文件是整个程序的入口点，就像一栋大楼的大门。
当你运行这个程序时，Python会首先执行这个文件中的代码。

【程序启动流程】
1. 创建应用程序实例（QApplication）
2. 显示启动/登录界面（LaunchOverlay）
3. 用户登录成功后，启动主窗口（MainWindow）
4. 进入事件循环，等待用户操作

【为什么需要这个文件】
- PyQt5程序必须有一个QApplication实例才能运行
- 这个文件负责初始化应用程序并启动第一个窗口
- 它就像程序的"心脏"，没有它程序无法运行
"""
import sys  # 导入系统模块，用于获取命令行参数和退出程序
from PyQt5.QtWidgets import QApplication  # 导入PyQt5的应用程序类
from PyQt5.QtGui import QFont  # 导入字体类，用于设置全局字体
from ui.main_window import MainWindow  # 导入主窗口类
from ui.launch_overlay_clean_login import LaunchOverlay  # 导入启动/登录界面类
from models.user import User  # 导入用户模型类


def create_app():
    """
    创建并配置 QApplication 实例

    【为什么需要这个函数】
    QApplication是PyQt5应用程序的核心，它管理程序的控制流和主要设置。
    每个PyQt5应用程序只能有一个QApplication实例。

    【函数做了什么】
    1. 创建QApplication实例
    2. 设置全局字体（让所有界面使用统一的字体）
    3. 设置应用程序名称、版本等信息

    【返回值】
    返回配置好的QApplication实例
    """
    # 创建QApplication实例，sys.argv包含命令行参数
    app = QApplication(sys.argv)

    # 创建字体对象
    font = QFont()
    # 设置字体族：按优先级尝试以下字体
    # SF Pro Display - macOS系统字体
    # PingFang SC - macOS中文字体
    # Segoe UI - Windows系统字体
    # Microsoft YaHei - Windows中文字体
    font.setFamily("SF Pro Display, PingFang SC, Segoe UI, Microsoft YaHei")
    font.setPointSize(10)  # 设置字体大小为10pt
    app.setFont(font)  # 将字体设置为应用程序的全局字体

    # 设置应用程序元数据
    app.setApplicationName("Python学习教辅系统")  # 应用程序名称
    app.setApplicationVersion("1.0.0")  # 版本号
    app.setOrganizationName("Python Learning Assistant")  # 组织名称

    return app


def launch_main_window(username: str, password: str):
    """
    登录完成后启动主窗口

    【为什么需要这个函数】
    登录界面和主窗口是分离的，登录成功后需要关闭登录窗口并打开主窗口。
    这个函数负责创建主窗口并显示。

    【参数说明】
    - username: 用户名（登录界面传递过来的）
    - password: 密码（登录界面传递过来的）

    【函数做了什么】
    1. 获取已创建的QApplication实例
    2. 创建User用户对象
    3. 创建主窗口并显示
    4. 将主窗口设置为前台窗口
    """
    # 获取当前的QApplication实例
    app = QApplication.instance()
    if app is None:
        # 如果QApplication不存在，抛出异常
        raise RuntimeError("QApplication 未初始化")

    # 创建用户对象（这里简化处理，实际应该从数据库验证）
    user = User(user_id=1, username=username, nickname=username)

    # 创建主窗口
    main_window = MainWindow(user)

    # 将主窗口保存到app中，防止被垃圾回收
    app._main_window = main_window

    # 显示主窗口
    main_window.show()

    # 将主窗口提升到前台
    main_window.raise_()
    main_window.activateWindow()


def run():
    """
    启动应用的主函数

    【程序启动流程】
    1. 创建QApplication
    2. 创建启动/登录界面
    3. 连接信号：登录成功信号 -> 启动主窗口
    4. 显示登录界面（全屏）
    5. 进入事件循环（app.exec_()）
    6. 用户关闭窗口时，退出程序

    【什么是信号（Signal）】
    信号是PyQt5的一种通信机制。当某个事件发生时（如登录成功），
    对象会发送一个信号，其他对象可以"监听"这个信号并做出响应。
    这里LaunchOverlay发送finished信号，MainWindow接收并启动。
    """
    # 创建应用程序
    app = create_app()

    # 创建启动/登录界面
    overlay = LaunchOverlay()

    # 连接信号：当登录完成时，调用launch_main_window函数
    # overlay.finished是信号，launch_main_window是槽函数
    overlay.finished.connect(launch_main_window)

    # 显示登录界面（全屏）
    overlay.showFullScreen()

    # 进入事件循环
    # exec_()会一直运行，直到程序退出
    # 用户的所有操作（点击、输入等）都由这个循环处理
    sys.exit(app.exec_())


# 当直接运行这个文件时（而不是被其他文件导入），执行run()
if __name__ == '__main__':
    run()
