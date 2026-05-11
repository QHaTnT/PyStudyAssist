# -*- coding: utf-8 -*-
"""
主窗口 - PyPalPrep Python学习教辅系统

【文件功能说明】
这个文件定义了主窗口类（MainWindow），是程序的主要界面。

【主窗口的作用】
1. 提供导航菜单，让用户切换不同功能模块
2. 显示各个功能模块的界面
3. 提供全局样式和主题设置
4. 处理窗口事件（关闭、调整大小等）

【界面布局】
主窗口采用左右分栏布局：
- 左侧：导航菜单（可展开/收起）
- 右侧：内容区域（显示各个功能模块）

【功能模块】
1. 知识学习 - 学习Python知识点
2. 题库练习 - 做练习题
3. 模拟考试 - 模拟考试环境
4. 编辑器 - 在线编写Python代码
5. 学习进度 - 查看学习统计
6. 错题本 - 复习错题
7. 成绩统计 - 查看成绩分析图表
8. 个人主页 - 用户信息和设置
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QListWidget, QListWidgetItem,
                             QMenuBar, QMenu, QAction, QToolBar,
                             QStatusBar, QMessageBox, QLabel, QToolTip,
                             QGraphicsDropShadowEffect, QApplication)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize  # 核心模块
from PyQt5.QtGui import QColor, QFont, QIcon  # GUI模块
from config import WINDOW_CONFIG, THEME_COLORS  # 配置
from models.user import User  # 用户模型
from ui.ai_assistant_widget import FloatingAssistant  # AI助手
from database.db_manager import db_manager  # 数据库管理器


class MainWindow(QMainWindow):
    """
    主窗口类

    【类的作用】
    作为程序的主界面，提供导航和内容展示功能。

    【继承关系】
    继承自QMainWindow，这是PyQt5的主窗口类。
    QMainWindow提供了菜单栏、工具栏、状态栏等标准窗口组件。

    【属性说明】
    - current_user: 当前登录用户
    - nav_list: 左侧导航列表
    - stack: 右侧内容堆栈（用于切换不同模块）
    - 各个功能模块的widget实例
    """

    def __init__(self, user):
        """
        初始化主窗口

        【参数说明】
        - user: 当前登录用户（User对象）

        【初始化流程】
        1. 调用父类初始化方法
        2. 保存用户信息
        3. 调用init_ui()初始化界面
        """
        super().__init__()  # 调用QMainWindow的初始化方法
        self.current_user = user  # 保存当前用户
        self.init_ui()  # 初始化界面

    def init_ui(self):
        """
        初始化用户界面

        【界面构建流程】
        1. 设置窗口标题和大小
        2. 应用全局样式
        3. 创建中心部件和布局
        4. 创建左侧导航菜单
        5. 创建右侧内容堆栈
        6. 加载各个功能模块
        7. 创建AI助手
        """
        # 设置窗口标题
        self.setWindowTitle(WINDOW_CONFIG['title'])

        # 设置窗口位置和大小
        # setGeometry(x, y, width, height)
        self.setGeometry(100, 100, WINDOW_CONFIG['width'], WINDOW_CONFIG['height'])

        # 设置最小尺寸（用户不能缩小到这个尺寸以下）
        self.setMinimumSize(WINDOW_CONFIG['min_width'], WINDOW_CONFIG['min_height'])

        # 最大化显示
        self.showMaximized()

        # 加载用户背景偏好并应用全局半透明样式
        self.bg_pref = None
        self.apply_background_theme(None)

        # 全局字体放大35%
        try:
            app = QApplication.instance()
            if app is not None:
                base_font = app.font()
                ps = base_font.pointSizeF()
                if ps > 0:
                    base_font.setPointSizeF(ps * 1.35)
                else:
                    base_font.setPointSize(14)
                app.setFont(base_font)
        except Exception:
            pass

        # 创建中心部件
        # QMainWindow需要一个中心部件来容纳所有内容
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 设置边距为0
        main_layout.setSpacing(0)  # 设置间距为0

        # 创建左右分栏布局
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(12, 12, 12, 12)  # 设置边距
        content_layout.setSpacing(12)  # 设置间距

        # ==================== 左侧导航菜单 ====================
        # QListWidget是一个列表控件，用于显示导航菜单
        self.nav_list = QListWidget()
        self.nav_list.setObjectName('navList')  # 设置对象名，用于样式选择
        self.nav_list.setFixedWidth(88)  # 设置固定宽度（收起状态）
        self.nav_list.setSpacing(8)  # 设置项目间距
        self.nav_list.setContentsMargins(8, 16, 8, 16)  # 设置内边距
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 按需显示滚动条
        self.nav_list.setStyleSheet('QListWidget { background: transparent; }')  # 透明背景
        self.nav_list.installEventFilter(self)  # 安装事件过滤器（用于悬停展开）
        content_layout.addWidget(self.nav_list)

        # ==================== 右侧内容区域 ====================
        # QStackedWidget是一个堆栈控件，一次只显示一个子控件
        # 用于在不同功能模块之间切换
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        main_layout.addLayout(content_layout)

        # 加载各个功能模块
        self.init_modules()

        # 绑定导航切换事件
        # 当用户点击导航菜单项时，调用on_page_changed方法
        self.nav_list.currentRowChanged.connect(self.on_page_changed)

        # 创建悬浮式AI助手
        try:
            self.ai_assistant = FloatingAssistant(self)
            self.ai_assistant.raise_()  # 提升到顶层
        except Exception:
            self.ai_assistant = None

    def showEvent(self, event):
        """
        窗口显示事件

        【什么时候触发】
        当窗口首次显示或从隐藏状态恢复时触发。

        【做了什么】
        1. 调用父类的showEvent
        2. 将窗口提升到前台
        3. 重新定位AI助手
        """
        super().showEvent(event)
        try:
            self.raise_()
            self.activateWindow()
            if hasattr(self, 'ai_assistant') and self.ai_assistant:
                # 延迟重新定位浮标，确保窗口大小已更新
                QTimer.singleShot(200, lambda: self.ai_assistant.reposition_on_parent_resize())
        except Exception as e:
            print(f"ShowEvent error: {e}")

    def resizeEvent(self, event):
        """
        窗口大小改变事件

        【什么时候触发】
        当用户调整窗口大小时触发。

        【做了什么】
        重新定位AI助手，确保它始终在正确的位置。
        """
        super().resizeEvent(event)
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant:
                self.ai_assistant.reposition_on_parent_resize()
        except Exception:
            pass

    def init_modules(self):
        """
        初始化各功能模块

        【为什么在这里导入】
        使用延迟导入（在函数内部导入）可以避免循环导入问题。
        如果在文件顶部导入，可能会导致模块之间的循环依赖。

        【加载的模块】
        1. KnowledgeWidget - 知识学习
        2. PracticeWidget - 题库练习
        3. ExamWidget - 模拟考试
        4. EditorWidget - 编辑器
        5. ProgressWidget - 学习进度
        6. MistakesWidget - 错题本
        7. StatisticsWidget - 成绩统计
        8. ProfileWidget - 个人主页
        """
        from ui.knowledge_widget import KnowledgeWidget
        from ui.practice_widget import PracticeWidget
        from ui.editor_widget import EditorWidget
        from ui.progress_widget import ProgressWidget
        from ui.mistakes_widget import MistakesWidget
        from ui.statistics_widget import StatisticsWidget
        from ui.profile_widget import ProfileWidget
        from ui.exam_widget import ExamWidget

        # 添加知识点学习模块
        self.knowledge_widget = KnowledgeWidget(self.current_user)
        self.stack.addWidget(self.knowledge_widget)  # 添加到堆栈
        self.nav_list.addItem(QListWidgetItem('知识学习'))  # 添加导航项

        # 添加题库练习模块
        self.practice_widget = PracticeWidget(self.current_user)
        self.stack.addWidget(self.practice_widget)
        self.nav_list.addItem(QListWidgetItem('题库练习'))

        # 添加模拟考试模块
        self.exam_widget = ExamWidget(self.current_user)
        self.stack.addWidget(self.exam_widget)
        self.nav_list.addItem(QListWidgetItem('模拟考试'))

        # 添加代码编辑器模块
        self.editor_widget = EditorWidget(self.current_user)
        self.stack.addWidget(self.editor_widget)
        self.nav_list.addItem(QListWidgetItem('编辑器'))

        # 添加学习进度模块
        self.progress_widget = ProgressWidget(self.current_user)
        self.stack.addWidget(self.progress_widget)
        self.nav_list.addItem(QListWidgetItem('学习进度'))

        # 添加错题本模块
        self.mistakes_widget = MistakesWidget(self.current_user)
        self.stack.addWidget(self.mistakes_widget)
        self.nav_list.addItem(QListWidgetItem('错题本'))

        # 添加成绩统计模块
        self.statistics_widget = StatisticsWidget(self.current_user)
        self.stack.addWidget(self.statistics_widget)
        self.nav_list.addItem(QListWidgetItem('成绩统计'))

        # 添加个人主页模块
        self.profile_widget = ProfileWidget(self.current_user)
        self.stack.addWidget(self.profile_widget)
        self.nav_list.addItem(QListWidgetItem('个人主页'))

        # 统一设置导航项的样式
        cur_font = self.nav_list.font()
        ps = cur_font.pointSizeF()
        if ps > 0:
            cur_font.setPointSizeF(ps * 1.05)
        else:
            cur_font.setPointSize(12)
        self.nav_list.setFont(cur_font)

        # 设置每个导航项的样式
        for i in range(self.nav_list.count()):
            item = self.nav_list.item(i)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 居中对齐
            item.setSizeHint(QSize(340, 240))  # 设置大小提示
            item.setToolTip(item.text())  # 设置工具提示

    def on_page_changed(self, index):
        """
        页面切换时刷新数据

        【参数说明】
        - index: 新页面的索引

        【索引对应关系】
        0=知识学习, 1=题库练习, 2=模拟考试, 3=编辑器,
        4=学习进度, 5=错题本, 6=成绩统计, 7=个人主页

        【做了什么】
        1. 切换到对应的页面
        2. 刷新该页面的数据
        """
        # 切换到对应页面
        self.stack.setCurrentIndex(index)

        # 根据索引刷新对应页面的数据
        try:
            if index == 0 and hasattr(self, 'knowledge_widget'):
                self.knowledge_widget.refresh()
            elif index == 1 and hasattr(self, 'practice_widget'):
                self.practice_widget.refresh()
            elif index == 2 and hasattr(self, 'exam_widget'):
                self.exam_widget.refresh()
            elif index == 4 and hasattr(self, 'progress_widget'):
                self.progress_widget.refresh()
            elif index == 5 and hasattr(self, 'mistakes_widget'):
                self.mistakes_widget.refresh()
            elif index == 6 and hasattr(self, 'statistics_widget'):
                self.statistics_widget.refresh()
            elif index == 7 and hasattr(self, 'profile_widget'):
                self.profile_widget.refresh()
        except Exception as e:
            print(f'页面刷新出错: {e}')

    def load_background_pref(self):
        """
        从数据库读取用户的背景偏好

        【返回值】
        - 背景偏好字符串（图片路径或纯色颜色值）
        - None（如果没有设置背景）
        """
        try:
            db_manager.connect()
            result = db_manager.execute_query(
                'SELECT bg_path FROM users WHERE id = ?',
                (self.current_user.id,)
            )
            if result:
                return dict(result[0]).get('bg_path')
        except Exception:
            return None
        finally:
            db_manager.disconnect()
        return None

    def apply_background_theme(self, bg_pref=None):
        """
        应用背景主题

        【参数说明】
        - bg_pref: 背景偏好字符串
          - None: 使用默认背景
          - "color:#xxxxxx": 使用纯色背景
          - 图片路径: 使用图片背景

        【做了什么】
        根据背景偏好生成QSS样式表，并应用到整个窗口。
        """
        if bg_pref is not None:
            self.bg_pref = bg_pref

        base_bg = THEME_COLORS.get('background', '#F6F7F9')
        background_rule = f"background-color: {base_bg};"

        pref = getattr(self, 'bg_pref', None)
        if pref:
            if isinstance(pref, str) and pref.startswith('color:'):
                # 纯色背景
                color_value = pref.split(':', 1)[1] or base_bg
                background_rule = f"background-color: {color_value};"
            else:
                # 图片背景
                path_norm = pref.replace('\\', '/')
                background_rule = (
                    f"background-color: {base_bg};"
                    f"background-image: url('{path_norm}');"
                    "background-position: center center;"
                    "background-repeat: no-repeat;"
                    "background-attachment: fixed;"
                    "background-size: cover;"
                )

        # 生成QSS样式表
        nav_item_bg = "rgba(255,255,255,0.82)"
        card_bg = "rgba(255,255,255,0.82)"

        style = f"""
            QMainWindow {{
                {background_rule}
                font-family: 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', 'Segoe UI';
            }}
            QMainWindow > QWidget {{
                {background_rule}
            }}
            .leftNav {{
                background-color: transparent;
            }}
            QListWidget#navList {{
                background-color: transparent;
                border: none;
            }}
            QListWidget#navList::item {{
                padding: 16px 30px;
                border-radius: 16px;
                color: {THEME_COLORS['dark']};
                margin: 8px 10px;
                background-color: {nav_item_bg};
                border: 1px solid rgba(0,0,0,0.06);
            }}
            QListWidget#navList::item:selected {{
                background-color: rgba(255,255,255,0.95);
                color: {THEME_COLORS['primary']};
                font-weight: 600;
                border: none;
            }}
            QListWidget#navList::item:hover {{
                background-color: rgba(0,0,0,0.06);
            }}
            QGroupBox {{
                background-color: {card_bg};
                border-radius: 12px;
                border: none;
            }}
            QLabel#pageTitle {{
                background-color: {card_bg};
                border: none;
                border-radius: 12px;
                padding: 14px 16px;
            }}
            QTableWidget, QListWidget, QTextEdit, QLineEdit, QComboBox, QSpinBox {{
                background-color: rgba(255,255,255,0.85);
                border-radius: 10px;
                border: none;
            }}
            QScrollBar:vertical {{
                width: 12px;
                background-color: transparent;
            }}
            QScrollBar::handle:vertical {{
                background-color: rgba(0,0,0,0.2);
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: rgba(0,0,0,0.3);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                height: 12px;
                background-color: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background-color: rgba(0,0,0,0.2);
                border-radius: 6px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: rgba(0,0,0,0.3);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            QPushButton {{
                border-radius: 10px;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(0,0,0,0.03);
            }}
            QPushButton:pressed {{
                background-color: rgba(0,0,0,0.05);
            }}
        """
        self.setStyleSheet(style)

    def refresh_data(self):
        """刷新所有数据"""
        try:
            if hasattr(self, 'knowledge_widget'):
                self.knowledge_widget.refresh()
            if hasattr(self, 'practice_widget'):
                self.practice_widget.refresh()
            if hasattr(self, 'progress_widget'):
                self.progress_widget.refresh()
            if hasattr(self, 'mistakes_widget'):
                self.mistakes_widget.refresh()
            if hasattr(self, 'statistics_widget'):
                self.statistics_widget.refresh()

            QMessageBox.information(self, '提示', '数据刷新成功！')
        except Exception as e:
            QMessageBox.warning(self, '警告', f'数据刷新失败: {str(e)}')

    def eventFilter(self, source, event):
        """
        事件过滤器

        【什么是事件过滤器】
        事件过滤器可以拦截和处理其他对象的事件。
        这里用于处理左侧导航菜单的悬停展开/收起行为。

        【做了什么】
        - 鼠标进入导航菜单时：展开菜单，显示阴影
        - 鼠标离开导航菜单时：收起菜单，移除阴影
        """
        from PyQt5.QtCore import QEvent, QPropertyAnimation, QEasingCurve
        if source == self.nav_list:
            if event.type() == QEvent.Enter:
                # 鼠标进入：展开导航
                anim = QPropertyAnimation(self.nav_list, b"minimumWidth")
                anim.setDuration(180)
                anim.setStartValue(self.nav_list.width())
                anim.setEndValue(600)  # 展开宽度
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start()
                self._nav_anim = anim  # 保存引用，防止被垃圾回收

                # 添加阴影效果
                try:
                    shadow = QGraphicsDropShadowEffect(self.nav_list)
                    shadow.setOffset(0, 4)
                    shadow.setBlurRadius(24)
                    shadow.setColor(QColor(0, 0, 0, int(255 * 0.12)))
                    self.nav_list.setGraphicsEffect(shadow)
                    self._nav_shadow = shadow
                except Exception:
                    pass

            elif event.type() == QEvent.Leave:
                # 鼠标离开：收起导航
                anim = QPropertyAnimation(self.nav_list, b"minimumWidth")
                anim.setDuration(160)
                anim.setStartValue(self.nav_list.width())
                anim.setEndValue(88)  # 收起宽度
                anim.setEasingCurve(QEasingCurve.InCubic)
                anim.start()
                self._nav_anim = anim

                # 显示提示气泡
                try:
                    global_pos = self.nav_list.mapToGlobal(self.nav_list.rect().center())
                    QToolTip.showText(global_pos, '悬停展开', self.nav_list)
                except Exception:
                    pass

                # 移除阴影
                try:
                    self.nav_list.setGraphicsEffect(None)
                    self._nav_shadow = None
                except Exception:
                    pass
        return super().eventFilter(source, event)

    def show_about(self):
        """显示关于对话框"""
        about_text = '''
        <h2>Python学习教辅系统</h2>
        <p><b>版本:</b> 1.0.0</p>
        <p><b>基于:</b> Python计算机二级考试大纲</p>
        <p><b>功能特点:</b></p>
        <ul>
            <li>📚 系统的Python知识点学习</li>
            <li>✍️ 丰富的题库练习（选择、判断、填空、编程）</li>
            <li>💻 内置代码编辑器和执行环境</li>
            <li>📊 学习进度可视化跟踪</li>
            <li>📝 智能错题本管理</li>
            <li>📈 详细的成绩统计分析</li>
        </ul>
        <p><b>技术栈:</b> Python 3.x + PyQt5 + SQLite</p>
        <p><b>© 2025 版权所有</b></p>
        '''
        QMessageBox.about(self, '关于', about_text)

    def closeEvent(self, event):
        """
        窗口关闭事件

        【什么时候触发】
        当用户点击窗口关闭按钮时触发。

        【做了什么】
        显示确认对话框，询问用户是否确定退出。
        """
        reply = QMessageBox.question(
            self, '确认退出',
            '确定退出PyPalPrep吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()  # 接受关闭事件，窗口关闭
        else:
            event.ignore()  # 忽略关闭事件，窗口不关闭
