# -*- coding: utf-8 -*-
"""
知识点学习模块
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QTextEdit, QMessageBox,
    QListWidgetItem, QProgressBar, QFrame, QPushButton, QSplitter
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from core.services.data_service import data_service
from ui.styles.theme import COLORS, FONTS, SIZES
import time


class KnowledgeWidget(QWidget):
    """知识点学习界面"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.current_knowledge = None
        self.start_time = None
        self._setup_ui()
        self.load_categories()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧面板
        left_panel = QFrame()
        left_panel.setFixedWidth(350)  # 增加宽度到350
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 16)
        left_layout.setSpacing(12)

        # 分类标题
        cat_title = QLabel("📚 知识点分类")
        cat_title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        cat_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        left_layout.addWidget(cat_title)

        # 分类列表
        self.category_list = QListWidget()
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px 14px;
                border-radius: 8px;
                margin: 2px 0;
                color: {COLORS['text_secondary']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['primary_alpha_hover']};
                color: {COLORS['primary']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """)
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        left_layout.addWidget(self.category_list, 1)

        # 知识点标题
        kp_title = QLabel("📋 知识点列表")
        kp_title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        kp_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        left_layout.addWidget(kp_title)

        # 知识点列表
        self.knowledge_list = QListWidget()
        self.knowledge_list.setStyleSheet(self.category_list.styleSheet())
        self.knowledge_list.currentRowChanged.connect(self._on_knowledge_changed)
        left_layout.addWidget(self.knowledge_list, 1)

        layout.addWidget(left_panel)

        # 右侧内容区
        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(16)

        # 标题栏
        header_layout = QHBoxLayout()
        self.title_label = QLabel("请选择知识点")
        self.title_label.setFont(QFont(*FONTS['heading']))
        self.title_label.setStyleSheet(f"color: {COLORS['primary']}; background: transparent;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.mark_btn = QPushButton("✓ 标记为已完成")
        self.mark_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #059669; }}
            QPushButton:disabled {{ background-color: {COLORS['border']}; color: {COLORS['text_hint']}; }}
        """)
        self.mark_btn.clicked.connect(self._mark_completed)
        self.mark_btn.setEnabled(False)
        header_layout.addWidget(self.mark_btn)
        right_layout.addLayout(header_layout)

        # 进度条
        progress_layout = QHBoxLayout()
        progress_label = QLabel("学习进度:")
        progress_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        progress_layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(0, 0, 0, 0.06);
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['primary']};
                border-radius: 4px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar, 1)

        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        progress_layout.addWidget(self.progress_label)
        right_layout.addLayout(progress_layout)

        # 内容区分割器
        content_splitter = QSplitter(Qt.Vertical)

        # 知识点内容
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        content_inner = QVBoxLayout(content_frame)
        content_inner.setContentsMargins(16, 16, 16, 16)

        content_title = QLabel("📖 知识点内容")
        content_title.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-weight: bold;")
        content_inner.addWidget(content_title)

        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setFont(QFont("Microsoft YaHei", 18))
        self.content_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                line-height: 1.6;
            }}
        """)
        content_inner.addWidget(self.content_text)
        content_splitter.addWidget(content_frame)

        # 代码示例
        code_frame = QFrame()
        code_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['code_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        code_inner = QVBoxLayout(code_frame)
        code_inner.setContentsMargins(16, 16, 16, 16)

        code_title = QLabel("💻 代码示例")
        code_title.setStyleSheet(f"color: {COLORS['code_text']}; background: transparent; font-weight: bold;")
        code_inner.addWidget(code_title)

        self.code_text = QTextEdit()
        self.code_text.setReadOnly(True)
        self.code_text.setFont(QFont("Consolas", 16))
        self.code_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                color: {COLORS['code_text']};
                font-family: 'Consolas', monospace;
            }}
        """)
        code_inner.addWidget(self.code_text)
        content_splitter.addWidget(code_frame)

        content_splitter.setSizes([400, 200])
        right_layout.addWidget(content_splitter, 1)

        # 底部状态栏
        status_layout = QHBoxLayout()
        self.time_label = QLabel("⏱️ 学习时长: 0 秒")
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        status_layout.addWidget(self.time_label)
        status_layout.addStretch()
        right_layout.addLayout(status_layout)

        layout.addWidget(right_panel, 1)

        # 计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)

    def load_categories(self):
        from config import config
        self.category_list.clear()
        for cat in config.knowledge.categories:
            self.category_list.addItem(cat)

    def _on_category_changed(self, index):
        if index < 0:
            return
        category = self.category_list.item(index).text()
        points = data_service.get_knowledge_by_category(category)

        # 获取已完成的知识点ID
        from core.database.sqlite_manager import db
        completed_ids = set()
        records = db.execute(
            "SELECT knowledge_id FROM learning_records WHERE user_id = ? AND completed = 1",
            (self.current_user.id,)
        )
        for r in records:
            completed_ids.add(r['knowledge_id'])

        self.knowledge_list.clear()
        for kp in points:
            # 标记已完成的知识点
            if kp.id in completed_ids:
                title = f"✓ {kp.title}"
            else:
                title = kp.title
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, kp)
            self.knowledge_list.addItem(item)

    def _on_knowledge_changed(self, index):
        if index < 0:
            return
        item = self.knowledge_list.item(index)
        knowledge = item.data(Qt.UserRole)
        if knowledge:
            self.current_knowledge = knowledge
            self.title_label.setText(f"{knowledge.category} - {knowledge.title}")
            self.content_text.setPlainText(knowledge.content)
            self.code_text.setPlainText(knowledge.code_example or "# 暂无代码示例")
            self.mark_btn.setEnabled(True)
            self._start_timer()

    def _start_timer(self):
        self.start_time = time.time()
        self.timer.start(1000)

    def _update_time(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.time_label.setText(f'⏱️ 学习时长: {elapsed // 60} 分 {elapsed % 60} 秒')

    def _mark_completed(self):
        if not self.current_knowledge:
            return
        study_time = int(time.time() - self.start_time) if self.start_time else 0
        data_service.mark_knowledge_completed(
            self.current_user.id,
            self.current_knowledge.id,
            study_time
        )

        # 显示美观的提示
        self._show_toast("✓ 已标记为完成！")

        self.timer.stop()
        self.start_time = None
        self.time_label.setText('⏱️ 学习时长: 0 秒')
        self._update_progress()

        # 刷新左侧列表，显示完成标记
        current_cat_index = self.category_list.currentRow()
        if current_cat_index >= 0:
            self._on_category_changed(current_cat_index)

    def _show_toast(self, message, duration=2000):
        """显示美观的提示框"""
        from PyQt5.QtCore import QPropertyAnimation, QPoint

        toast = QLabel(message, self)
        toast.setStyleSheet("""
            QLabel {
                background: #10B981;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        toast.setAlignment(Qt.AlignCenter)
        toast.adjustSize()

        # 居中显示
        x = (self.width() - toast.width()) // 2
        y = (self.height() - toast.height()) // 2
        toast.move(x, y)
        toast.show()

        # 动画：淡入
        toast.setGraphicsEffect(None)
        from PyQt5.QtWidgets import QGraphicsOpacityEffect
        from PyQt5.QtCore import QPropertyAnimation
        opacity_effect = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(opacity_effect)
        anim = QPropertyAnimation(opacity_effect, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()

        # 定时消失
        QTimer.singleShot(duration, toast.deleteLater)

    def _update_progress(self):
        from core.database.sqlite_manager import db
        total = db.execute_one("SELECT COUNT(*) as count FROM knowledge_points")
        completed = db.execute_one(
            "SELECT COUNT(*) as count FROM learning_records WHERE user_id = ? AND completed = 1",
            (self.current_user.id,)
        )
        total_count = total['count'] if total else 0
        completed_count = completed['count'] if completed else 0
        if total_count > 0:
            progress = int(completed_count / total_count * 100)
            self.progress_bar.setValue(progress)
            self.progress_label.setText(f'{progress}%')

    def refresh(self):
        self.load_categories()
        self._update_progress()
