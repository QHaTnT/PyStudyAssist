# -*- coding: utf-8 -*-
"""
主窗口：简洁现代风格
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame, QGridLayout
)
from ui.styles.message_box import ask_question
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QLinearGradient
from config import config
from core.services.auth_service import auth_service
from core.services.data_service import data_service
from ui.styles.theme import COLORS


class GradientWidget(QWidget):
    """渐变背景"""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor('#F8FAFC'))
        gradient.setColorAt(1, QColor('#F1F5F9'))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


class ModuleCard(QFrame):
    """模块卡片 - 无边框设计"""
    clicked = pyqtSignal()

    def __init__(self, icon, title, desc, color, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 120)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
            }}
            QFrame:hover {{
                background: rgba(0, 0, 0, 0.03);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 32))
        icon_label.setFixedSize(56, 56)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"background: {color}12; border-radius: 14px;")
        layout.addWidget(icon_label)

        # 文字
        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 19, QFont.Bold))
        title_label.setStyleSheet("color: #1E293B; background: transparent;")
        text_layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Microsoft YaHei", 15))
        desc_label.setStyleSheet("color: #64748B; background: transparent;")
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout, 1)

        # 箭头
        arrow = QLabel("→")
        arrow.setFont(QFont("Microsoft YaHei", 18))
        arrow.setStyleSheet("color: #CBD5E1; background: transparent;")
        layout.addWidget(arrow)

    def mousePressEvent(self, event):
        self.clicked.emit()


class HomePage(QWidget):
    """首页"""
    module_selected = pyqtSignal(int)

    def __init__(self, user):
        super().__init__()
        self.user = user
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 48, 60, 48)
        layout.setSpacing(0)

        # 欢迎语
        welcome = QLabel(f"👋 你好，{self.user.nickname or self.user.username}")
        welcome.setFont(QFont("Microsoft YaHei", 36, QFont.Bold))
        welcome.setStyleSheet("color: #1E293B; background: transparent;")
        layout.addWidget(welcome)

        subtitle = QLabel("选择一个功能开始学习")
        subtitle.setFont(QFont("Microsoft YaHei", 18))
        subtitle.setStyleSheet("color: #94A3B8; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(40)

        # 统计数据（保存为实例属性以便刷新）
        self._stat_labels = {}
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(48)

        for key, unit, title in [
            ("total_study_time", "分钟", "学习时长"),
            ("completed_knowledge", "个", "完成知识点"),
            ("total_questions", "道", "练习题目"),
            ("wrong_questions_count", "道", "错题数"),
        ]:
            stat_widget = QWidget()
            stat_widget.setStyleSheet("background: transparent;")
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0, 0, 0, 0)
            stat_layout.setSpacing(6)

            value_label = QLabel("0")
            value_label.setFont(QFont("Microsoft YaHei", 32, QFont.Bold))
            value_label.setStyleSheet("color: #1E293B; background: transparent;")
            stat_layout.addWidget(value_label)

            title_label = QLabel(title)
            title_label.setFont(QFont("Microsoft YaHei", 17))
            title_label.setStyleSheet("color: #94A3B8; background: transparent;")
            stat_layout.addWidget(title_label)

            self._stat_labels[key] = (value_label, unit)
            stats_layout.addWidget(stat_widget)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # 初始加载数据
        self.refresh()

        layout.addSpacing(48)

        # 功能模块（无边框列表）
        modules_label = QLabel("功能模块")
        modules_label.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        modules_label.setStyleSheet("color: #1E293B; background: transparent;")
        layout.addWidget(modules_label)

        layout.addSpacing(16)

        modules = [
            ("📚", "知识学习", "系统学习Python知识点", COLORS['primary']),
            ("✍️", "题库练习", "练习选择题、判断题、编程题", COLORS['success']),
            ("📝", "模拟考试", "模拟计算机二级考试环境", COLORS['warning']),
            ("💻", "代码编辑", "在线编写和运行Python代码", COLORS['info']),
            ("📊", "学习进度", "查看学习时长和完成情况", '#8B5CF6'),
            ("❌", "错题本", "复习错题，巩固薄弱知识点", COLORS['danger']),
            ("📈", "成绩统计", "查看各分类准确率分析", '#EC4899'),
            ("👤", "个人主页", "管理个人信息和设置", '#64748B'),
        ]

        for i, (icon, title, desc, color) in enumerate(modules):
            card = ModuleCard(icon, title, desc, color)
            card.clicked.connect(lambda x=i: self.module_selected.emit(x))
            layout.addWidget(card)

        layout.addStretch()

    def refresh(self):
        """刷新首页统计数据"""
        stats = data_service.get_user_statistics(self.user.id)

        total_time = stats.get('total_study_time', 0)
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60

        updates = {
            "total_study_time": f"{hours}小时{minutes}分钟" if hours > 0 else f"{minutes}分钟",
            "completed_knowledge": f"{stats.get('completed_knowledge', 0)} 个",
            "total_questions": f"{stats.get('total_questions', 0)} 道",
            "wrong_questions_count": f"{stats.get('wrong_questions_count', 0)} 道",
        }

        for key, value in updates.items():
            if key in self._stat_labels:
                label, _ = self._stat_labels[key]
                label.setText(value)


class ModulePage(QWidget):
    """模块页面"""
    back_clicked = pyqtSignal()

    def __init__(self, title, icon, content_widget):
        super().__init__()
        self._setup_ui(title, icon, content_widget)

    def _setup_ui(self, title, icon, content_widget):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(20)

        # 顶部
        header = QHBoxLayout()
        back_btn = QPushButton("← 返回")
        back_btn.setFixedHeight(44)
        back_btn.setFont(QFont("Microsoft YaHei", 16))
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['primary']};
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_alpha_hover']};
                border-radius: 8px;
            }}
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(back_btn)

        header.addSpacing(16)

        title_label = QLabel(f"{icon} {title}")
        title_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title_label.setStyleSheet("color: #1E293B; background: transparent;")
        header.addWidget(title_label)

        header.addStretch()
        layout.addLayout(header)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #E2E8F0; border: none; max-height: 1px;")
        layout.addWidget(line)

        # 内容
        layout.addWidget(content_widget, 1)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.modules = []
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(config.ui.app_title)
        self.setMinimumSize(config.ui.min_width, config.ui.min_height)
        self.showMaximized()

        central = GradientWidget()
        self.setCentralWidget(central)

        self.stack = QStackedWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(self.stack)

        self.home_page = HomePage(self.current_user)
        self.home_page.module_selected.connect(self._open_module)
        self.stack.addWidget(self.home_page)

        self._init_modules()

        # AI 助手（放在 centralWidget 上，这样位置相对于 centralWidget）
        try:
            from ui.widgets.ai_assistant import AIAssistant
            self.ai_assistant = AIAssistant(central)
            self.ai_assistant.raise_()
        except Exception as e:
            print(f"加载 AI 助手失败: {e}")

    def _init_modules(self):
        from ui.widgets.knowledge_widget import KnowledgeWidget
        from ui.widgets.practice_widget import PracticeWidget
        from ui.widgets.exam_widget import ExamWidget
        from ui.widgets.editor_widget import EditorWidget
        from ui.widgets.progress_widget import ProgressWidget
        from ui.widgets.mistakes_widget import MistakesWidget
        from ui.widgets.statistics_widget import StatisticsWidget
        from ui.widgets.profile_widget import ProfileWidget

        module_configs = [
            ("知识学习", "📚", KnowledgeWidget),
            ("题库练习", "✍️", PracticeWidget),
            ("模拟考试", "📝", ExamWidget),
            ("代码编辑", "💻", EditorWidget),
            ("学习进度", "📊", ProgressWidget),
            ("错题本", "❌", MistakesWidget),
            ("成绩统计", "📈", StatisticsWidget),
            ("个人主页", "👤", ProfileWidget),
        ]

        self.editor_widget = None  # 保存编辑器引用

        for title, icon, WidgetClass in module_configs:
            try:
                widget = WidgetClass(self.current_user)
                page = ModulePage(title, icon, widget)
                page.back_clicked.connect(self._go_home)
                self.stack.addWidget(page)
                self.modules.append(page)

                # 保存 content_widget 引用
                page.content_widget = widget

                # 保存编辑器引用
                if WidgetClass == EditorWidget:
                    self.editor_widget = widget

            except Exception as e:
                print(f"加载模块失败 {title}: {e}")

    def _open_module(self, index):
        if 0 <= index < len(self.modules):
            self.stack.setCurrentIndex(index + 1)
            # 更新 AI 助手可见性
            if hasattr(self, 'ai_assistant'):
                self.ai_assistant.update_module_visibility()

            # 刷新当前页面数据
            page = self.modules[index]
            if hasattr(page, 'content_widget') and hasattr(page.content_widget, 'refresh'):
                page.content_widget.refresh()

    def _go_home(self):
        self.stack.setCurrentIndex(0)
        # 回到首页时显示 AI 助手
        if hasattr(self, 'ai_assistant'):
            self.ai_assistant.show()
            self.ai_assistant.raise_()
        # 刷新首页统计数据
        if hasattr(self, 'home_page'):
            self.home_page.refresh()

    def closeEvent(self, event):
        if ask_question(self, '确认退出', '确定退出 PyStudyAssist 吗？'):
            auth_service.logout()
            event.accept()
        else:
            event.ignore()
