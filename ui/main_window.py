# -*- coding: utf-8 -*-
"""
主窗口：玻璃拟态风格 (Glassmorphism)
渐变背景 + 玻璃导航栏 + 玻璃卡片内容区
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem,
    QMessageBox, QLabel, QGraphicsDropShadowEffect,
    QApplication, QFrame, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush, QLinearGradient
from config import WINDOW_CONFIG
from models.user import User
from ui.ai_assistant_widget import FloatingAssistant
from database.db_manager import db_manager
from ui.styles.theme import COLORS, FONTS, SIZES, get_qss, get_nav_qss


class GradientBackground(QWidget):
    """渐变背景组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(COLORS['gradient_start']))
        gradient.setColorAt(0.5, QColor(COLORS['gradient_mid']))
        gradient.setColorAt(1, QColor(COLORS['gradient_end']))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


class NavButton(QPushButton):
    """导航按钮组件"""

    def __init__(self, icon_text, label, parent=None):
        super().__init__(parent)
        self.icon_text = icon_text
        self.label = label
        self._is_selected = False
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(SIZES['nav_item_height'])
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        if self._is_selected:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    border: none;
                    border-radius: {SIZES['border_radius']}px;
                    color: {COLORS['text_white']};
                    font-size: 14px;
                    font-weight: 600;
                    text-align: left;
                    padding-left: 16px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: {SIZES['border_radius']}px;
                    color: {COLORS['text_secondary']};
                    font-size: 14px;
                    font-weight: 500;
                    text-align: left;
                    padding-left: 16px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_alpha_hover']};
                    color: {COLORS['primary']};
                }}
            """)

    def set_selected(self, selected):
        self._is_selected = selected
        self._update_style()

    def paintEvent(self, event):
        super().paintEvent(event)


class MainWindow(QMainWindow):
    """主窗口类：玻璃拟态风格"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.nav_expanded = False
        self.current_index = 0
        self._setup_ui()

    def _setup_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(WINDOW_CONFIG['title'])
        self.setMinimumSize(WINDOW_CONFIG['min_width'], WINDOW_CONFIG['min_height'])
        self.showMaximized()

        # 设置渐变背景样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['gradient_start']},
                    stop:0.5 {COLORS['gradient_mid']},
                    stop:1 {COLORS['gradient_end']});
            }}
            QWidget {{
                background: transparent;
            }}
        """)

        # 设置应用字体
        app = QApplication.instance()
        if app:
            app.setFont(QFont("SF Pro Display", 13))

        # 创建中心部件
        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)

        # 内容区布局
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # 左侧导航栏
        self.nav_widget = self._create_nav_bar()
        content_layout.addWidget(self.nav_widget)

        # 右侧内容区
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        content_layout.addWidget(self.stack, 1)

        main_layout.addLayout(content_layout, 1)

        # 加载功能模块
        self._init_modules()

        # 绑定导航点击
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)

        # 悬浮 AI 助手
        try:
            self.ai_assistant = FloatingAssistant(self)
            self.ai_assistant.raise_()
        except Exception:
            self.ai_assistant = None

    def _create_nav_bar(self):
        """创建玻璃拟态导航栏"""
        nav_container = QWidget()
        nav_container.setFixedWidth(SIZES['nav_width_collapsed'])
        nav_container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(nav_container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Logo 区域
        logo_frame = QFrame()
        logo_frame.setFixedHeight(64)
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
            }}
        """)
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(12, 0, 12, 0)

        logo_icon = QLabel("🎓")
        logo_icon.setFont(QFont("Segoe UI Emoji", 24))
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setStyleSheet("background: transparent;")
        logo_layout.addWidget(logo_icon)

        self.logo_text = QLabel("PyStudyAssist")
        self.logo_text.setFont(QFont(*FONTS['subheading']))
        self.logo_text.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self.logo_text.setVisible(False)
        logo_layout.addWidget(self.logo_text)

        layout.addWidget(logo_frame)
        layout.addSpacing(8)

        # 导航列表
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
                padding: 8px;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                border-radius: {SIZES['border_radius']}px;
                padding: 12px 16px;
                margin: 2px 0;
                color: {COLORS['text_secondary']};
                font-size: 14px;
                font-weight: 500;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['primary_alpha_hover']};
                color: {COLORS['primary']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_white']};
                font-weight: 600;
            }}
        """)
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 导航项配置
        nav_items = [
            ("📚", "知识学习"),
            ("✍️", "题库练习"),
            ("📝", "模拟考试"),
            ("💻", "代码编辑"),
            ("📊", "学习进度"),
            ("❌", "错题本"),
            ("📈", "成绩统计"),
            ("👤", "个人主页"),
        ]

        for icon, label in nav_items:
            item = QListWidgetItem(f"{icon}  {label}")
            item.setSizeHint(QSize(0, SIZES['nav_item_height']))
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.nav_list.addItem(item)

        layout.addWidget(self.nav_list, 1)

        # 底部设置按钮
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(48, 48)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius']}px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_alpha_hover']};
            }}
        """)
        layout.addWidget(settings_btn, alignment=Qt.AlignCenter)

        # 添加阴影
        shadow = QGraphicsDropShadowEffect(nav_container)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        nav_container.setGraphicsEffect(shadow)

        return nav_container

    def _init_modules(self):
        """初始化各功能模块"""
        from ui.knowledge_widget import KnowledgeWidget
        from ui.practice_widget import PracticeWidget
        from ui.editor_widget import EditorWidget
        from ui.progress_widget import ProgressWidget
        from ui.mistakes_widget import MistakesWidget
        from ui.statistics_widget import StatisticsWidget
        from ui.profile_widget import ProfileWidget
        from ui.exam_widget import ExamWidget

        modules = [
            ("知识学习", KnowledgeWidget),
            ("题库练习", PracticeWidget),
            ("模拟考试", ExamWidget),
            ("代码编辑", EditorWidget),
            ("学习进度", ProgressWidget),
            ("错题本", MistakesWidget),
            ("成绩统计", StatisticsWidget),
            ("个人主页", ProfileWidget),
        ]

        for name, WidgetClass in modules:
            try:
                widget = WidgetClass(self.current_user)
                self.stack.addWidget(widget)
            except Exception as e:
                print(f"加载模块 {name} 失败: {e}")
                # 添加占位符
                placeholder = QLabel(f"{name} 模块加载失败")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet(f"color: {COLORS['text_hint']}; font-size: 16px;")
                self.stack.addWidget(placeholder)

    def _on_nav_changed(self, index):
        """导航切换"""
        if index < 0:
            return

        self.current_index = index
        self.stack.setCurrentIndex(index)

        # 刷新对应模块
        try:
            widget = self.stack.currentWidget()
            if hasattr(widget, 'refresh'):
                widget.refresh()
        except Exception as e:
            print(f"刷新模块失败: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 更新背景大小
        if hasattr(self, 'background'):
            self.background.setGeometry(self.centralWidget().rect())

    def showEvent(self, event):
        super().showEvent(event)
        # 选中第一个导航项
        if hasattr(self, 'nav_list') and self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, '确认退出',
            '确定退出 PyStudyAssist 吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
