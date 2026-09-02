# -*- coding: utf-8 -*-
"""
全屏登录/注册界面
像网页一样的大界面
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QStackedWidget,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QLinearGradient
from core.services.auth_service import auth_service
from ui.styles.theme import COLORS, FONTS


class GradientBackground(QWidget):
    """渐变背景"""

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
    """玻璃卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 24px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)


class LoginWindow(QWidget):
    """全屏登录/注册窗口"""
    finished = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyStudyAssist - 登录")
        self._setup_ui()

    def _setup_ui(self):
        # 全屏显示
        self.showMaximized()
        self.setMinimumSize(1000, 700)

        # 背景
        self.background = GradientBackground(self)
        self.background.setGeometry(0, 0, self.width(), self.height())

        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧装饰区
        left_panel = QFrame()
        left_panel.setStyleSheet("background: transparent;")
        left_panel.setMinimumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(60, 60, 40, 60)

        # Logo
        logo = QLabel("🎓")
        logo.setFont(QFont("Segoe UI Emoji", 72))
        logo.setStyleSheet("background: transparent;")
        left_layout.addWidget(logo)

        # 标题
        title = QLabel("PyStudyAssist")
        title.setFont(QFont("Microsoft YaHei", 32, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']}; background: transparent;")
        left_layout.addWidget(title)

        # 副标题
        subtitle = QLabel("Python 学习助手")
        subtitle.setFont(QFont("SF Pro Display", 20))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        left_layout.addWidget(subtitle)

        left_layout.addSpacing(40)

        # 特性列表
        features = [
            "📚 系统化的Python知识点学习",
            "✍️ 丰富的题库练习",
            "📝 模拟考试环境",
            "💻 在线代码编辑器",
        ]
        for feature in features:
            label = QLabel(feature)
            label.setFont(QFont("SF Pro Display", 14))
            label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; padding: 8px 0;")
            left_layout.addWidget(label)

        left_layout.addStretch()

        main_layout.addWidget(left_panel)

        # 右侧登录/注册区
        right_panel = QFrame()
        right_panel.setStyleSheet("background: transparent;")
        right_panel.setMaximumWidth(500)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 60, 60, 60)

        # 内容栈
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        # 登录表单
        self.login_form = self._create_login_form()
        self.stack.addWidget(self.login_form)

        # 注册表单
        self.register_form = self._create_register_form()
        self.stack.addWidget(self.register_form)

        right_layout.addWidget(self.stack)
        right_layout.addStretch()

        main_layout.addWidget(right_panel)

        # 加载保存的登录凭据
        saved_username, saved_password = self._load_credentials()
        if saved_username:
            self.login_username.setText(saved_username)
        if saved_password:
            self.login_password.setText(saved_password)

    def _create_login_form(self):
        """创建登录表单"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # 标题
        title = QLabel("欢迎回来")
        title.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel("登录您的账号继续学习")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # 用户名
        username_label = QLabel("用户名")
        username_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-weight: bold;")
        layout.addWidget(username_label)

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("请输入用户名")
        self.login_username.setFixedHeight(50)
        self.login_username.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)
        layout.addWidget(self.login_username)

        # 密码
        password_label = QLabel("密码")
        password_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-weight: bold;")
        layout.addWidget(password_label)

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("请输入密码")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setFixedHeight(50)
        self.login_password.returnPressed.connect(self._on_login)
        self.login_password.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)
        layout.addWidget(self.login_password)

        layout.addSpacing(10)

        # 登录按钮
        login_btn = QPushButton("登 录")
        login_btn.setFixedHeight(50)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['primary']});
            }}
        """)
        login_btn.clicked.connect(self._on_login)
        layout.addWidget(login_btn)

        layout.addSpacing(20)

        # 切换到注册
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)
        no_account = QLabel("没有账号？")
        no_account.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        switch_layout.addWidget(no_account)

        switch_btn = QPushButton("立即注册")
        switch_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['primary']};
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {COLORS['primary_dark']};
            }}
        """)
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        switch_layout.addWidget(switch_btn)
        layout.addLayout(switch_layout)

        return widget

    def _create_register_form(self):
        """创建注册表单"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 标题
        title = QLabel("创建账号")
        title.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel("注册账号开始学习之旅")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        # 用户名
        username_label = QLabel("用户名")
        username_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-weight: bold;")
        layout.addWidget(username_label)

        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("至少3个字符")
        self.reg_username.setFixedHeight(45)
        self.reg_username.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{ border: 2px solid {COLORS['primary']}; }}
        """)
        layout.addWidget(self.reg_username)

        # 昵称
        nickname_label = QLabel("昵称（可选）")
        nickname_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-weight: bold;")
        layout.addWidget(nickname_label)

        self.reg_nickname = QLineEdit()
        self.reg_nickname.setPlaceholderText("您的显示名称")
        self.reg_nickname.setFixedHeight(45)
        self.reg_nickname.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{ border: 2px solid {COLORS['primary']}; }}
        """)
        layout.addWidget(self.reg_nickname)

        # 密码
        password_label = QLabel("密码")
        password_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-weight: bold;")
        layout.addWidget(password_label)

        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("至少6位")
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_password.setFixedHeight(45)
        self.reg_password.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{ border: 2px solid {COLORS['primary']}; }}
        """)
        layout.addWidget(self.reg_password)

        # 确认密码
        confirm_label = QLabel("确认密码")
        confirm_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-weight: bold;")
        layout.addWidget(confirm_label)

        self.reg_confirm = QLineEdit()
        self.reg_confirm.setPlaceholderText("再次输入密码")
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        self.reg_confirm.setFixedHeight(45)
        self.reg_confirm.returnPressed.connect(self._on_register)
        self.reg_confirm.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{ border: 2px solid {COLORS['primary']}; }}
        """)
        layout.addWidget(self.reg_confirm)

        layout.addSpacing(8)

        # 注册按钮
        register_btn = QPushButton("注 册")
        register_btn.setFixedHeight(50)
        register_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['primary']});
            }}
        """)
        register_btn.clicked.connect(self._on_register)
        layout.addWidget(register_btn)

        layout.addSpacing(12)

        # 切换到登录
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)
        has_account = QLabel("已有账号？")
        has_account.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        switch_layout.addWidget(has_account)

        switch_btn = QPushButton("立即登录")
        switch_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['primary']};
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {COLORS['primary_dark']};
            }}
        """)
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        switch_layout.addWidget(switch_btn)
        layout.addLayout(switch_layout)

        return widget

    def _on_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, '提示', '请输入用户名和密码')
            return

        user = auth_service.login(username, password)
        if user:
            # 保存登录凭据
            self._save_credentials(username, password)
            self.finished.emit(username, password)
            self.close()
        else:
            QMessageBox.critical(self, '登录失败', '用户名或密码错误')

    def _save_credentials(self, username, password):
        """保存登录凭据到文件"""
        import os
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.credentials')
        try:
            with open(cred_path, 'w', encoding='utf-8') as f:
                f.write(f"{username}\n{password}\n")
        except Exception:
            pass

    def _load_credentials(self):
        """从文件加载登录凭据"""
        import os
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.credentials')
        try:
            if os.path.exists(cred_path):
                with open(cred_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        return lines[0].strip(), lines[1].strip()
        except Exception:
            pass
        return None, None

    def _on_register(self):
        username = self.reg_username.text().strip()
        nickname = self.reg_nickname.text().strip()
        password = self.reg_password.text().strip()
        confirm = self.reg_confirm.text().strip()

        if not username or len(username) < 3:
            QMessageBox.warning(self, '提示', '用户名至少3个字符')
            return

        if not password or len(password) < 6:
            QMessageBox.warning(self, '提示', '密码至少6位')
            return

        if password != confirm:
            QMessageBox.warning(self, '提示', '两次输入的密码不一致')
            return

        user_id = auth_service.register(username, password, nickname)
        if user_id:
            QMessageBox.information(self, '注册成功', '账号注册成功，请登录')
            self.stack.setCurrentIndex(0)
            self.login_username.setText(username)
        else:
            QMessageBox.critical(self, '注册失败', '用户名已存在')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'background'):
            self.background.setGeometry(0, 0, self.width(), self.height())
