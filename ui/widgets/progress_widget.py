# -*- coding: utf-8 -*-
"""
学习进度模块
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt5.QtGui import QFont
from core.services.data_service import data_service
from ui.styles.theme import COLORS, FONTS, SIZES


class ProgressWidget(QWidget):
    """学习进度界面"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("📊 学习进度概览")
        title.setFont(QFont(*FONTS['heading']))
        title.setStyleSheet(f"color: {COLORS['primary']}; background: transparent;")
        layout.addWidget(title)

        # 统计卡片
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.stat_cards = {}
        for key, label, color in [
            ('time', '总学习时长', COLORS['primary']),
            ('knowledge', '完成知识点', COLORS['success']),
            ('questions', '完成题目', COLORS['info']),
        ]:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['glass_bg']};
                    border: 1px solid {COLORS['border_light']};
                    border-left: 4px solid {color};
                    border-radius: 12px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)

            title_label = QLabel(label)
            title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 15px;")
            card_layout.addWidget(title_label)

            value_label = QLabel("0")
            value_label.setStyleSheet(f"color: {color}; background: transparent; font-size: 24px; font-weight: bold;")
            card_layout.addWidget(value_label)

            self.stat_cards[key] = value_label
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        # 分类进度表
        self.progress_table = QTableWidget()
        self.progress_table.setColumnCount(4)
        self.progress_table.setHorizontalHeaderLabels(['分类', '总知识点', '已完成', '进度'])
        self.progress_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.progress_table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        layout.addWidget(self.progress_table, 1)

    def refresh(self):
        """刷新数据"""
        from core.database.sqlite_manager import db

        # 直接从数据库查询，确保数据最新
        total_study_time = db.execute_one(
            "SELECT COALESCE(SUM(study_time), 0) as total FROM learning_records WHERE user_id = ?",
            (self.current_user.id,)
        )
        total_seconds = total_study_time['total'] if total_study_time else 0

        completed_count = db.execute_one(
            "SELECT COUNT(*) as count FROM learning_records WHERE user_id = ? AND completed = 1",
            (self.current_user.id,)
        )
        completed_knowledge = completed_count['count'] if completed_count else 0

        questions_count = db.execute_one(
            "SELECT COUNT(*) as count FROM practice_records WHERE user_id = ?",
            (self.current_user.id,)
        )
        total_questions = questions_count['count'] if questions_count else 0

        # 更新卡片
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            self.stat_cards['time'].setText(f"{hours}小时{minutes}分钟")
        else:
            self.stat_cards['time'].setText(f"{minutes}分钟")

        self.stat_cards['knowledge'].setText(str(completed_knowledge))
        self.stat_cards['questions'].setText(str(total_questions))

        # 更新表格
        category_stats = data_service.get_category_statistics(self.current_user.id)
        self.progress_table.setRowCount(0)
        for stat in category_stats:
            row = self.progress_table.rowCount()
            self.progress_table.insertRow(row)
            self.progress_table.setItem(row, 0, QTableWidgetItem(stat['category']))
            self.progress_table.setItem(row, 1, QTableWidgetItem(str(stat['total'])))
            self.progress_table.setItem(row, 2, QTableWidgetItem(str(stat['completed'])))
            self.progress_table.setItem(row, 3, QTableWidgetItem(f"{stat['progress']}%"))
