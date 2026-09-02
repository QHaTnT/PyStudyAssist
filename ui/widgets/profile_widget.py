# -*- coding: utf-8 -*-
"""
个人主页模块
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QInputDialog, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.services.auth_service import auth_service
from core.services.data_service import data_service
from ui.styles.theme import COLORS, FONTS


class ProfileWidget(QWidget):
    """个人主页界面"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # 用户信息区
        user_card = QFrame()
        user_card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid #E2E8F0;
                border-radius: 16px;
            }}
        """)
        user_layout = QHBoxLayout(user_card)
        user_layout.setContentsMargins(32, 24, 32, 24)
        user_layout.setSpacing(24)

        # 头像（可点击上传）
        self.avatar_label = QLabel("👤")
        self.avatar_label.setFont(QFont("Segoe UI Emoji", 48))
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setCursor(Qt.PointingHandCursor)
        self.avatar_label.setStyleSheet(f"""
            background: {COLORS['primary']}15;
            border-radius: 50px;
            border: 2px dashed {COLORS['border']};
        """)
        self.avatar_label.setToolTip("点击上传头像")
        self.avatar_label.mousePressEvent = self._upload_avatar
        user_layout.addWidget(self.avatar_label)

        # 加载已有头像
        self._load_avatar()

        # 用户信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        name = QLabel(self.current_user.nickname or self.current_user.username)
        name.setFont(QFont("SF Pro Display", 24, QFont.Bold))
        name.setStyleSheet("color: #1E293B; background: transparent;")
        info_layout.addWidget(name)

        username = QLabel(f"用户名: {self.current_user.username}")
        username.setStyleSheet("color: #64748B; background: transparent; font-size: 14px;")
        info_layout.addWidget(username)

        user_id = QLabel(f"用户ID: {self.current_user.id}")
        user_id.setStyleSheet("color: #64748B; background: transparent; font-size: 14px;")
        info_layout.addWidget(user_id)

        info_layout.addStretch()
        user_layout.addLayout(info_layout, 1)

        layout.addWidget(user_card)

        # 学习统计
        stats_card = QFrame()
        stats_card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid #E2E8F0;
                border-radius: 16px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(24, 20, 24, 20)
        stats_layout.setSpacing(16)

        stats_title = QLabel("📊 学习统计")
        stats_title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        stats_title.setStyleSheet("color: #1E293B; background: transparent;")
        stats_layout.addWidget(stats_title)

        # 统计网格（保存为实例属性以便刷新）
        self._stat_labels = {}
        grid = QHBoxLayout()
        grid.setSpacing(20)

        for key, icon, title, color in [
            ("total_study_time", "⏱️", "学习时长", COLORS['primary']),
            ("completed_knowledge", "✅", "完成知识点", COLORS['success']),
            ("total_questions", "✍️", "练习题目", COLORS['info']),
            ("wrong_questions_count", "❌", "错题数", COLORS['danger']),
        ]:
            stat_item = QVBoxLayout()
            stat_item.setSpacing(4)

            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Segoe UI Emoji", 28))
            icon_label.setFixedSize(48, 48)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(f"background: {color}15; border-radius: 12px;")
            stat_item.addWidget(icon_label, alignment=Qt.AlignCenter)

            value_label = QLabel("0")
            value_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
            value_label.setStyleSheet(f"color: {color}; background: transparent;")
            stat_item.addWidget(value_label, alignment=Qt.AlignCenter)

            title_label = QLabel(title)
            title_label.setStyleSheet("color: #64748B; background: transparent; font-size: 15px;")
            stat_item.addWidget(title_label, alignment=Qt.AlignCenter)

            self._stat_labels[key] = value_label
            grid.addLayout(stat_item)

        stats_layout.addLayout(grid)
        layout.addWidget(stats_card)

        # 正确率
        accuracy_card = QFrame()
        accuracy_card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid #E2E8F0;
                border-radius: 16px;
            }}
        """)
        acc_layout = QHBoxLayout(accuracy_card)
        acc_layout.setContentsMargins(24, 20, 24, 20)

        acc_title = QLabel("📈 练习正确率")
        acc_title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        acc_title.setStyleSheet("color: #1E293B; background: transparent;")
        acc_layout.addWidget(acc_title)

        acc_layout.addStretch()

        self._accuracy_label = QLabel("0%")
        self._accuracy_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        self._accuracy_label.setStyleSheet(f"color: {COLORS['success']}; background: transparent;")
        acc_layout.addWidget(self._accuracy_label)

        layout.addWidget(accuracy_card)
        layout.addStretch()

    def _load_avatar(self):
        """加载用户头像"""
        from core.database.sqlite_manager import db
        import os

        user_data = db.get_user_by_username(self.current_user.username)
        if user_data and user_data.get('avatar_path'):
            avatar_path = user_data['avatar_path']
            if os.path.exists(avatar_path):
                from PyQt5.QtGui import QPixmap
                pixmap = QPixmap(avatar_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.avatar_label.setPixmap(scaled)
                    self.avatar_label.setStyleSheet("border-radius: 50px; border: 2px solid #E2E8F0;")

    def _upload_avatar(self, event=None):
        """上传头像"""
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtGui import QPixmap
        import os
        import shutil

        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择头像图片', '',
            '图片文件 (*.png *.jpg *.jpeg *.gif *.bmp);;所有文件 (*.*)'
        )

        if not file_path:
            return

        # 复制到项目的 avatars 目录
        avatar_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)

        # 生成文件名
        ext = os.path.splitext(file_path)[1]
        avatar_filename = f"avatar_{self.current_user.id}{ext}"
        avatar_path = os.path.join(avatar_dir, avatar_filename)

        try:
            shutil.copy2(file_path, avatar_path)

            # 更新数据库
            from core.database.sqlite_manager import db
            db.update_user(self.current_user.id, avatar_path=avatar_path)

            # 更新显示
            pixmap = QPixmap(avatar_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.avatar_label.setPixmap(scaled)
                self.avatar_label.setStyleSheet("border-radius: 50px; border: 2px solid #E2E8F0;")

            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, '成功', '头像上传成功！')

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, '错误', f'头像上传失败: {str(e)}')

    def refresh(self):
        """刷新统计数据"""
        stats = data_service.get_user_statistics(self.current_user.id)

        # 更新统计标签
        if hasattr(self, '_stat_labels'):
            total_time = stats.get('total_study_time', 0)
            hours = total_time // 3600
            minutes = (total_time % 3600) // 60
            if hours > 0:
                self._stat_labels['total_study_time'].setText(f"{hours}小时{minutes}分钟")
            else:
                self._stat_labels['total_study_time'].setText(f"{minutes}分钟")

            self._stat_labels['completed_knowledge'].setText(f"{stats.get('completed_knowledge', 0)} 个")
            self._stat_labels['total_questions'].setText(f"{stats.get('total_questions', 0)} 道")
            self._stat_labels['wrong_questions_count'].setText(f"{stats.get('wrong_questions_count', 0)} 道")

        # 更新正确率
        if hasattr(self, '_accuracy_label'):
            total = stats.get('total_questions', 0)
            correct = stats.get('correct_questions', 0)
            accuracy = round(correct / total * 100, 1) if total > 0 else 0
            self._accuracy_label.setText(f"{accuracy}%")
