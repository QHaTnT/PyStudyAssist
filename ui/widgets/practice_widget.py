# -*- coding: utf-8 -*-
"""
题库练习模块
"""
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QTextEdit, QRadioButton, QLineEdit,
    QGroupBox, QMessageBox, QButtonGroup, QComboBox,
    QCheckBox, QSplitter, QProgressBar, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from core.services.data_service import data_service
from ui.styles.theme import COLORS, FONTS, SIZES
from config import config
import time
import json


class PracticeWidget(QWidget):
    """题库练习界面"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.current_questions = []
        self.current_index = 0
        self.current_question = None
        self.start_time = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 筛选区
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)

        filter_layout.addWidget(QLabel("分类:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(['全部'] + config.knowledge.categories)
        filter_layout.addWidget(self.category_combo)

        filter_layout.addWidget(QLabel("题型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['全部'] + list(config.knowledge.question_types.values()))
        filter_layout.addWidget(self.type_combo)

        self.only_new = QCheckBox("只显示未做")
        filter_layout.addWidget(self.only_new)

        load_btn = QPushButton("加载题目")
        load_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }}
        """)
        load_btn.clicked.connect(self._load_questions)
        filter_layout.addWidget(load_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # 题目区
        question_frame = QFrame()
        question_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
            }}
        """)
        q_layout = QVBoxLayout(question_frame)
        q_layout.setContentsMargins(16, 16, 16, 16)

        self.question_label = QLabel("题目: 0/0")
        self.question_label.setFont(QFont("Microsoft YaHei", 16))
        self.question_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        q_layout.addWidget(self.question_label)

        self.question_text = QTextEdit()
        self.question_text.setReadOnly(True)
        self.question_text.setMaximumHeight(200)
        self.question_text.setFont(QFont("Microsoft YaHei", 18))
        self.question_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                line-height: 1.5;
            }}
        """)
        q_layout.addWidget(self.question_text)

        layout.addWidget(question_frame)

        # 答题区
        answer_frame = QFrame()
        answer_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
            }}
        """)
        self.answer_layout = QVBoxLayout(answer_frame)
        self.answer_layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(answer_frame, 1)

        # 解析区
        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        self.explanation_text.setMaximumHeight(150)
        self.explanation_text.setFont(QFont("Microsoft YaHei", 16))
        self.explanation_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        self.explanation_text.setVisible(False)
        layout.addWidget(self.explanation_text)

        # 按钮区
        btn_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一题")
        self.prev_btn.clicked.connect(self._prev_question)
        self.prev_btn.setEnabled(False)
        btn_layout.addWidget(self.prev_btn)

        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }}
        """)
        self.submit_btn.clicked.connect(self._submit_answer)
        self.submit_btn.setEnabled(False)
        btn_layout.addWidget(self.submit_btn)

        self.next_btn = QPushButton("下一题")
        self.next_btn.clicked.connect(self._next_question)
        self.next_btn.setEnabled(False)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)

    def _load_questions(self):
        category = self.category_combo.currentText()
        q_type = self.type_combo.currentText()
        type_map = {v: k for k, v in config.knowledge.question_types.items()}
        type_key = type_map.get(q_type)

        self.current_questions = data_service.get_random_questions(
            category=category if category != '全部' else None,
            q_type=type_key,
            exclude_done=self.only_new.isChecked(),
            user_id=self.current_user.id
        )

        if self.current_questions:
            self.current_index = 0
            self._show_question()
            self.question_label.setText(f"题目: 1/{len(self.current_questions)}")
        else:
            QMessageBox.warning(self, '提示', '没有找到题目')

    def _show_question(self):
        if not self.current_questions or self.current_index >= len(self.current_questions):
            return

        self.current_question = self.current_questions[self.current_index]
        self.question_text.setPlainText(self.current_question.question)

        # 清空答题区
        while self.answer_layout.count():
            child = self.answer_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 根据题型显示
        q_type = self.current_question.type
        if q_type == 'choice':
            self._show_choice()
        elif q_type == 'judge':
            self._show_judge()
        elif q_type == 'fill':
            self._show_fill()
        elif q_type == 'code':
            self._show_code()

        # 重置按钮状态
        self.submit_btn.setEnabled(True)
        self.explanation_text.setVisible(False)

        # 启用/禁用导航按钮
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.current_questions) - 1)

        # 记录开始时间
        self.start_time = time.time()

        # 更新题目标签
        self.question_label.setText(f"题目: {self.current_index + 1}/{len(self.current_questions)}")

    def _show_choice(self):
        self.button_group = QButtonGroup()
        options = self.current_question.options
        if isinstance(options, str):
            options = json.loads(options) if options else []
        for i, opt in enumerate(options):
            radio = QRadioButton(opt)
            radio.setFont(QFont(*FONTS['body']))
            self.button_group.addButton(radio, i)
            self.answer_layout.addWidget(radio)

    def _show_judge(self):
        self.button_group = QButtonGroup()
        true_radio = QRadioButton("正确")
        false_radio = QRadioButton("错误")
        self.button_group.addButton(true_radio, 0)
        self.button_group.addButton(false_radio, 1)
        self.answer_layout.addWidget(true_radio)
        self.answer_layout.addWidget(false_radio)

    def _show_fill(self):
        self.fill_input = QLineEdit()
        self.fill_input.setPlaceholderText("请输入答案")
        self.fill_input.setMinimumHeight(50)
        self.fill_input.setFont(QFont("Microsoft YaHei", 16))
        self.fill_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['glass_bg']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px 16px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        self.answer_layout.addWidget(self.fill_input)

    def _show_code(self):
        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText("请输入 Python 代码")
        self.code_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['code_bg']};
                color: {COLORS['code_text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', monospace;
            }}
        """)
        self.answer_layout.addWidget(self.code_input)

    def _get_answer(self):
        q_type = self.current_question.type
        if q_type == 'choice':
            checked = self.button_group.checkedId()
            return chr(65 + checked) if checked >= 0 else None
        elif q_type == 'judge':
            checked = self.button_group.checkedId()
            return '正确' if checked == 0 else '错误' if checked == 1 else None
        elif q_type == 'fill':
            return self.fill_input.text().strip() if hasattr(self, 'fill_input') else None
        elif q_type == 'code':
            return self.code_input.toPlainText().strip() if hasattr(self, 'code_input') else None
        return None

    def _submit_answer(self):
        answer = self._get_answer()
        if not answer:
            QMessageBox.warning(self, '提示', '请先作答')
            return

        is_correct = self.current_question.check_answer(answer)
        time_spent = int(time.time() - self.start_time) if self.start_time else 0

        data_service.record_practice(
            self.current_user.id,
            self.current_question.id,
            answer,
            is_correct,
            time_spent
        )

        # 显示解析
        result = "✓ 回答正确！" if is_correct else f"✗ 回答错误！正确答案: {self.current_question.answer}"
        if self.current_question.explanation:
            result += f"\n\n{self.current_question.explanation}"
        self.explanation_text.setPlainText(result)
        self.explanation_text.setVisible(True)
        self.submit_btn.setEnabled(False)

        # 启用下一题按钮
        self.next_btn.setEnabled(self.current_index < len(self.current_questions) - 1)

    def _prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._show_question()

    def _next_question(self):
        if self.current_index < len(self.current_questions) - 1:
            self.current_index += 1
            self._show_question()

    def refresh(self):
        """刷新数据"""
        pass
