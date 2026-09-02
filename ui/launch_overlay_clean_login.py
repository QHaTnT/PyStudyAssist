# -*- coding: utf-8 -*-
"""
PyStudyAssist 登录/注册页：玻璃拟态风格 (Glassmorphism)
支持登录和注册功能
"""
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QApplication, QLineEdit,
    QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QGraphicsDropShadowEffect, QMessageBox, QStackedWidget
)
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QRect, pyqtSignal,
    QTimer, QEasingCurve, QPoint
)
from PyQt5.QtGui import (
    QFont, QPalette, QColor, QPainter, QBrush,
    QLinearGradient
)
import math
from database.db_manager import db_manager


class GradientBackground(QWidget):
    """渐变背景组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor('#EFF6FF'))
        gradient.setColorAt(0.5, QColor('#DBEAFE'))
        gradient.setColorAt(1, QColor('#F0F9FF'))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


class GlassCard(QFrame):
    """玻璃卡片组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.65);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 24px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)


class GlassInput(QLineEdit):
    """玻璃输入框"""

    def __init__(self, placeholder='', parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.6);
                border: 1px solid rgba(226, 232, 240, 0.8);
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 15px;
                color: #1E293B;
                selection-background-color: rgba(37, 99, 235, 0.2);
            }}
            QLineEdit:focus {{
                border: 2px solid #2563EB;
                background-color: rgba(255, 255, 255, 0.85);
            }}
            QLineEdit::placeholder {{
                color: #94A3B8;
            }}
        """)


class GlassButton(QPushButton):
    """玻璃按钮"""

    def __init__(self, text, parent=None, variant='primary'):
        super().__init__(text, parent)
        self.variant = variant
        self._setup_style()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(52)

    def _setup_style(self):
        if self.variant == 'primary':
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2563EB, stop:1 #3B82F6);
                    border: none;
                    border-radius: 12px;
                    color: #FFFFFF;
                    font-size: 16px;
                    font-weight: 600;
                    padding: 0 24px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1D4ED8, stop:1 #2563EB);
                }}
                QPushButton:pressed {{
                    background: #1D4ED8;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.6);
                    border: 1px solid rgba(226, 232, 240, 0.8);
                    border-radius: 12px;
                    color: #64748B;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.8);
                    border-color: #2563EB;
                    color: #2563EB;
                }}
            """)


class LoginForm(QWidget):
    """登录表单"""
    login_clicked = pyqtSignal(str, str)
    switch_to_register = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # 玻璃卡片
        card = GlassCard()
        card.setFixedSize(420, 520)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 40, 36, 36)
        card_layout.setSpacing(0)

        # Logo
        logo_label = QLabel("🎓")
        logo_label.setFont(QFont("Segoe UI Emoji", 48))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        card_layout.addWidget(logo_label)

        # 标题
        title_label = QLabel("欢迎回来")
        title_label.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1E293B; background: transparent; margin-top: 8px;")
        card_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("登录您的 PyStudyAssist 账号")
        subtitle_label.setFont(QFont("SF Pro Display", 14))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #64748B; background: transparent; margin-bottom: 32px;")
        card_layout.addWidget(subtitle_label)

        # 用户名输入框
        self.username_input = GlassInput(placeholder="用户名")
        self.username_input.setFixedHeight(48)
        card_layout.addWidget(self.username_input)
        card_layout.addSpacing(12)

        # 密码输入框
        self.password_input = GlassInput(placeholder="密码")
        self.password_input.setFixedHeight(48)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._on_login)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(24)

        # 登录按钮
        login_btn = GlassButton("登 录", variant='primary')
        login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(login_btn)
        card_layout.addSpacing(16)

        # 注册链接
        register_layout = QHBoxLayout()
        register_layout.setAlignment(Qt.AlignCenter)

        no_account_label = QLabel("没有账号？")
        no_account_label.setFont(QFont("SF Pro Display", 12))
        no_account_label.setStyleSheet("color: #64748B; background: transparent;")
        register_layout.addWidget(no_account_label)

        register_btn = QPushButton("立即注册")
        register_btn.setFont(QFont("SF Pro Display", 12, QFont.Bold))
        register_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #2563EB;
                padding: 0;
            }
            QPushButton:hover {
                color: #1D4ED8;
            }
        """)
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.clicked.connect(self.switch_to_register.emit)
        register_layout.addWidget(register_btn)

        card_layout.addLayout(register_layout)
        card_layout.addSpacing(16)

        # 提示文字
        hint_label = QLabel("默认账号：1  密码：1")
        hint_label.setFont(QFont("SF Pro Display", 12))
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("color: #94A3B8; background: transparent;")
        card_layout.addWidget(hint_label)

        card_layout.addStretch()

        layout.addWidget(card, alignment=Qt.AlignCenter)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, '提示', '请输入用户名和密码')
            return

        self.login_clicked.emit(username, password)

    def clear_inputs(self):
        self.username_input.clear()
        self.password_input.clear()


class RegisterForm(QWidget):
    """注册表单"""
    register_clicked = pyqtSignal(str, str, str)  # username, password, nickname
    switch_to_login = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # 玻璃卡片
        card = GlassCard()
        card.setFixedSize(420, 580)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 40, 36, 36)
        card_layout.setSpacing(0)

        # Logo
        logo_label = QLabel("🎓")
        logo_label.setFont(QFont("Segoe UI Emoji", 48))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        card_layout.addWidget(logo_label)

        # 标题
        title_label = QLabel("创建账号")
        title_label.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1E293B; background: transparent; margin-top: 8px;")
        card_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("注册 PyStudyAssist 账号开始学习")
        subtitle_label.setFont(QFont("SF Pro Display", 14))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #64748B; background: transparent; margin-bottom: 32px;")
        card_layout.addWidget(subtitle_label)

        # 用户名输入框
        self.username_input = GlassInput(placeholder="用户名")
        self.username_input.setFixedHeight(48)
        card_layout.addWidget(self.username_input)
        card_layout.addSpacing(12)

        # 昵称输入框
        self.nickname_input = GlassInput(placeholder="昵称（可选）")
        self.nickname_input.setFixedHeight(48)
        card_layout.addWidget(self.nickname_input)
        card_layout.addSpacing(12)

        # 密码输入框
        self.password_input = GlassInput(placeholder="密码（至少6位）")
        self.password_input.setFixedHeight(48)
        self.password_input.setEchoMode(QLineEdit.Password)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(12)

        # 确认密码输入框
        self.confirm_password_input = GlassInput(placeholder="确认密码")
        self.confirm_password_input.setFixedHeight(48)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.returnPressed.connect(self._on_register)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addSpacing(24)

        # 注册按钮
        register_btn = GlassButton("注 册", variant='primary')
        register_btn.clicked.connect(self._on_register)
        card_layout.addWidget(register_btn)
        card_layout.addSpacing(16)

        # 登录链接
        login_layout = QHBoxLayout()
        login_layout.setAlignment(Qt.AlignCenter)

        has_account_label = QLabel("已有账号？")
        has_account_label.setFont(QFont("SF Pro Display", 12))
        has_account_label.setStyleSheet("color: #64748B; background: transparent;")
        login_layout.addWidget(has_account_label)

        login_btn = QPushButton("立即登录")
        login_btn.setFont(QFont("SF Pro Display", 12, QFont.Bold))
        login_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #2563EB;
                padding: 0;
            }
            QPushButton:hover {
                color: #1D4ED8;
            }
        """)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.switch_to_login.emit)
        login_layout.addWidget(login_btn)

        card_layout.addLayout(login_layout)

        card_layout.addStretch()

        layout.addWidget(card, alignment=Qt.AlignCenter)

    def _on_register(self):
        username = self.username_input.text().strip()
        nickname = self.nickname_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        # 验证输入
        if not username:
            QMessageBox.warning(self, '提示', '请输入用户名')
            return

        if len(username) < 3:
            QMessageBox.warning(self, '提示', '用户名至少3个字符')
            return

        if not password:
            QMessageBox.warning(self, '提示', '请输入密码')
            return

        if len(password) < 6:
            QMessageBox.warning(self, '提示', '密码至少6位')
            return

        if password != confirm_password:
            QMessageBox.warning(self, '提示', '两次输入的密码不一致')
            return

        self.register_clicked.emit(username, password, nickname)

    def clear_inputs(self):
        self.username_input.clear()
        self.nickname_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()


class LaunchOverlay(QWidget):
    """PyStudyAssist 登录/注册页：玻璃拟态风格"""
    finished = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._setup_ui()

    def _setup_ui(self):
        screen = QApplication.primaryScreen()
        self.resize(screen.size())

        # 渐变背景
        self.background = GradientBackground(self)
        self.background.setGeometry(0, 0, self.width(), self.height())

        # 中央内容区
        self.content_stack = QStackedWidget(self)
        self.content_stack.setStyleSheet("background: transparent;")

        # 登录表单
        self.login_form = LoginForm()
        self.login_form.login_clicked.connect(self._on_login)
        self.login_form.switch_to_register.connect(self._show_register)
        self.content_stack.addWidget(self.login_form)

        # 注册表单
        self.register_form = RegisterForm()
        self.register_form.register_clicked.connect(self._on_register)
        self.register_form.switch_to_login.connect(self._show_login)
        self.content_stack.addWidget(self.register_form)

        # 设置位置
        self._update_positions()

        # 底部版权信息
        self.copyright_label = QLabel("© 2025 PyStudyAssist. All rights reserved.", self)
        self.copyright_label.setFont(QFont("SF Pro Display", 11))
        self.copyright_label.setAlignment(Qt.AlignCenter)
        self.copyright_label.setStyleSheet("color: #94A3B8;")
        self.copyright_label.setGeometry(0, self.height() - 50, self.width(), 30)

    def _update_positions(self):
        """更新组件位置"""
        if hasattr(self, 'content_stack'):
            card_width = 420
            card_height = 580
            self.content_stack.setGeometry(
                (self.width() - card_width) // 2,
                (self.height() - card_height) // 2,
                card_width,
                card_height
            )

        if hasattr(self, 'copyright_label'):
            self.copyright_label.setGeometry(0, self.height() - 50, self.width(), 30)

    def _show_login(self):
        """切换到登录表单"""
        self.content_stack.setCurrentIndex(0)
        self.login_form.clear_inputs()

    def _show_register(self):
        """切换到注册表单"""
        self.content_stack.setCurrentIndex(1)
        self.register_form.clear_inputs()

    def _on_login(self, username, password):
        """处理登录"""
        # 验证用户
        user = db_manager.verify_user(username, password)
        if user:
            self.finished.emit(username, password)
            self.close()
        else:
            QMessageBox.critical(self, '登录失败', '用户名或密码错误')

    def _on_register(self, username, password, nickname):
        """处理注册"""
        # 创建用户
        user_id = db_manager.create_user(username, password, nickname)
        if user_id:
            QMessageBox.information(self, '注册成功', '账号注册成功，请登录')
            self._show_login()
        else:
            QMessageBox.critical(self, '注册失败', '用户名已存在')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'background'):
            self.background.setGeometry(0, 0, self.width(), self.height())
        self._update_positions()
