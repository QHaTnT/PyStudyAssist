# -*- coding: utf-8 -*-
"""
知识点学习模块：玻璃拟态风格
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QTextEdit, QSplitter, QMessageBox,
    QListWidgetItem, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor
from database.db_manager import db_manager
from utils.data_loader import DataLoader
from config import KNOWLEDGE_CATEGORIES
from ui.styles.theme import COLORS, FONTS, SIZES
from datetime import datetime
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
        """初始化界面"""
        self.setStyleSheet("background: transparent;")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # 左侧面板
        left_panel = QFrame()
        left_panel.setFixedWidth(280)
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 20, 16, 16)
        left_layout.setSpacing(12)

        # 分类标题
        cat_title = QLabel("知识点分类")
        cat_title.setFont(QFont(*FONTS['subheading']))
        cat_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        left_layout.addWidget(cat_title)

        # 分类列表
        self.category_list = QListWidget()
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: {SIZES['border_radius_small']}px;
                margin: 2px 0;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['primary_alpha_hover']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """)
        self.category_list.itemClicked.connect(self.on_category_selected)
        left_layout.addWidget(self.category_list)

        # 知识点标题
        kp_title = QLabel("知识点列表")
        kp_title.setFont(QFont(*FONTS['subheading']))
        kp_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        left_layout.addWidget(kp_title)

        # 知识点列表
        self.knowledge_list = QListWidget()
        self.knowledge_list.setStyleSheet(self.category_list.styleSheet())
        self.knowledge_list.itemClicked.connect(self.on_knowledge_selected)
        left_layout.addWidget(self.knowledge_list)

        main_layout.addWidget(left_panel)

        # 右侧内容区
        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
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

        self.mark_btn = QPushButton("标记为已完成")
        self.mark_btn.setFont(QFont(*FONTS['button_small']))
        self.mark_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['success']}, stop:1 #34D399);
                color: white;
                border: none;
                border-radius: {SIZES['border_radius']}px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 {COLORS['success']});
            }}
        """)
        self.mark_btn.clicked.connect(self.mark_as_completed)
        self.mark_btn.setEnabled(False)
        header_layout.addWidget(self.mark_btn)

        right_layout.addLayout(header_layout)

        # 进度条
        progress_layout = QHBoxLayout()
        progress_label = QLabel("学习进度:")
        progress_label.setFont(QFont(*FONTS['body']))
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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                border-radius: 4px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar, 1)

        self.progress_label = QLabel("0%")
        self.progress_label.setFont(QFont(*FONTS['caption']))
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        progress_layout.addWidget(self.progress_label)

        right_layout.addLayout(progress_layout)

        # 知识点内容
        content_label = QLabel("知识点内容")
        content_label.setFont(QFont(*FONTS['body_bold']))
        content_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        right_layout.addWidget(content_label)

        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 16px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
        """)
        right_layout.addWidget(self.content_text, 2)

        # 代码示例
        code_label = QLabel("代码示例")
        code_label.setFont(QFont(*FONTS['body_bold']))
        code_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        right_layout.addWidget(code_label)

        self.code_text = QTextEdit()
        self.code_text.setReadOnly(True)
        self.code_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['code_bg']};
                color: {COLORS['code_text']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 16px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 13px;
            }}
        """)
        right_layout.addWidget(self.code_text, 1)

        # 学习时长
        self.time_label = QLabel("学习时长: 0 秒")
        self.time_label.setFont(QFont(*FONTS['caption']))
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        right_layout.addWidget(self.time_label)

        main_layout.addWidget(right_panel, 1)

        # 计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_study_time)

    def load_categories(self):
        self.category_list.clear()
        for category in KNOWLEDGE_CATEGORIES:
            item = QListWidgetItem(category)
            self.category_list.addItem(item)

    def on_category_selected(self, item):
        category = item.text()
        self.load_knowledge_by_category(category)

    def load_knowledge_by_category(self, category):
        self.knowledge_list.clear()
        knowledge_points = DataLoader.load_knowledge_by_category(category)
        for kp in knowledge_points:
            item = QListWidgetItem(kp.title)
            item.setData(Qt.UserRole, kp)
            self.knowledge_list.addItem(item)

    def on_knowledge_selected(self, item):
        knowledge = item.data(Qt.UserRole)
        if knowledge:
            self.display_knowledge(knowledge)
            self.start_learning_timer()

    def display_knowledge(self, knowledge):
        self.current_knowledge = knowledge
        self.title_label.setText(f"{knowledge.category} - {knowledge.title}")
        self.content_text.setPlainText(knowledge.content)
        if knowledge.code_example:
            self.code_text.setPlainText(knowledge.code_example)
        else:
            self.code_text.setPlainText("# 暂无代码示例")
        self.mark_btn.setEnabled(True)
        self.update_progress()

    def start_learning_timer(self):
        self.start_time = time.time()
        self.timer.start(1000)

    def update_study_time(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.time_label.setText(f'学习时长: {minutes} 分 {seconds} 秒')

    def mark_as_completed(self):
        if not self.current_knowledge:
            return

        study_time = int(time.time() - self.start_time) if self.start_time else 0
        db_manager.connect()
        query = "SELECT id, study_time FROM learning_records WHERE user_id = ? AND knowledge_id = ?"
        result = db_manager.execute_query(query, (self.current_user.id, self.current_knowledge.id))

        if result:
            record = dict(result[0])
            total_time = record['study_time'] + study_time
            db_manager.execute_update(
                "UPDATE learning_records SET study_time = ?, completed = 1, last_study_at = ? WHERE id = ?",
                (total_time, datetime.now(), record['id'])
            )
        else:
            db_manager.insert(
                "INSERT INTO learning_records (user_id, knowledge_id, study_time, completed, last_study_at) VALUES (?, ?, ?, 1, ?)",
                (self.current_user.id, self.current_knowledge.id, study_time, datetime.now())
            )
        db_manager.disconnect()

        from ui.styles.message_box import show_info
        show_info(self, '成功', '已标记为完成！')
        self.update_progress()
        self.timer.stop()
        self.start_time = None
        self.time_label.setText('学习时长: 0 秒')

    def update_progress(self):
        db_manager.connect()
        total_result = db_manager.execute_query("SELECT COUNT(*) as count FROM knowledge_points")
        total_count = dict(total_result[0])['count'] if total_result else 0

        completed_result = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM learning_records WHERE user_id = ? AND completed = 1",
            (self.current_user.id,)
        )
        completed_count = dict(completed_result[0])['count'] if completed_result else 0
        db_manager.disconnect()

        if total_count > 0:
            progress = int((completed_count / total_count) * 100)
            self.progress_bar.setValue(progress)
            self.progress_label.setText(f'{progress}%')
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText('0%')

    def refresh(self):
        self.load_categories()
        self.update_progress()
