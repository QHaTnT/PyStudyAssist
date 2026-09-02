# -*- coding: utf-8 -*-
"""
错题本模块
支持选择题、判断题、填空题、编程题的答题和自动判分
"""
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QTextEdit, QMessageBox,
    QFrame, QProgressBar, QListWidgetItem,
    QLineEdit, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from core.services.data_service import data_service
from ui.styles.theme import COLORS, FONTS, SIZES


class MistakesWidget(QWidget):
    """错题本界面"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.wrong_questions = []
        self.current_index = 0
        self.current_question = None
        self.review_mode = False
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧
        left = QFrame()
        left.setFixedWidth(320)
        left.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 16)

        title = QLabel("❌ 我的错题本")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['danger']}; background: transparent;")
        left_layout.addWidget(title)

        self.count_label = QLabel("共 0 道错题")
        self.count_label.setFont(QFont("Microsoft YaHei", 16))
        self.count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        left_layout.addWidget(self.count_label)

        self.start_btn = QPushButton("开始复习")
        self.start_btn.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
        """)
        self.start_btn.clicked.connect(self._start_review)
        left_layout.addWidget(self.start_btn)

        left_layout.addStretch()
        layout.addWidget(left)

        # 右侧
        right = QFrame()
        right.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 16)
        right_layout.setSpacing(12)

        # 题目内容
        self.question_text = QTextEdit()
        self.question_text.setReadOnly(True)
        self.question_text.setFont(QFont("Microsoft YaHei", 18))
        self.question_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                line-height: 1.6;
            }}
        """)
        right_layout.addWidget(self.question_text, 1)

        # 答题区域
        self.answer_input_frame = QFrame()
        self.answer_input_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        self.answer_input_layout = QVBoxLayout(self.answer_input_frame)
        self.answer_input_layout.setContentsMargins(16, 16, 16, 16)
        self.answer_input_layout.setSpacing(8)
        self.answer_input_frame.setVisible(False)
        right_layout.addWidget(self.answer_input_frame)

        # 结果提示
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        self.result_label.setWordWrap(True)
        self.result_label.setVisible(False)
        right_layout.addWidget(self.result_label)

        # 解析
        self.answer_label = QLabel("")
        self.answer_label.setFont(QFont("Microsoft YaHei", 16))
        self.answer_label.setWordWrap(True)
        self.answer_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; padding: 8px; border: 1px solid {COLORS['border']}; border-radius: 8px;")
        self.answer_label.setVisible(False)
        right_layout.addWidget(self.answer_label)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
            QPushButton:disabled {{ background: {COLORS['border']}; color: {COLORS['text_hint']}; }}
        """)
        self.submit_btn.clicked.connect(self._submit_answer)
        self.submit_btn.setEnabled(False)
        btn_layout.addWidget(self.submit_btn)

        self.next_btn = QPushButton("下一题 →")
        self.next_btn.setFont(QFont("Microsoft YaHei", 15))
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_alpha_hover']}; }}
        """)
        self.next_btn.clicked.connect(self._next_question)
        btn_layout.addWidget(self.next_btn)

        right_layout.addLayout(btn_layout)
        layout.addWidget(right, 1)

    def _start_review(self):
        """开始复习"""
        self.wrong_questions = data_service.get_user_wrong_questions(self.current_user.id)
        if not self.wrong_questions:
            QMessageBox.information(self, '提示', '没有错题，继续加油！')
            return

        self.review_mode = True
        self.current_index = 0
        self._show_question()

    def _show_question(self):
        """显示当前题目"""
        if not self.wrong_questions or self.current_index >= len(self.wrong_questions):
            QMessageBox.information(self, '复习完成', '所有错题已复习完成！')
            self.review_mode = False
            return

        q = self.wrong_questions[self.current_index]
        self.current_question = q

        # 显示题目
        self.question_text.setPlainText(q.get('question', ''))

        # 重置状态
        self.result_label.setVisible(False)
        self.answer_label.setVisible(False)
        self.submit_btn.setEnabled(True)
        self.count_label.setText(f"进度: {self.current_index + 1}/{len(self.wrong_questions)}")

        # 清空答题区域
        self._clear_answer_area()

        # 根据题型显示答题框
        q_type = q.get('type', '')
        options = q.get('options', '')

        if q_type == 'choice' and options:
            self._show_choice_options(options)
        elif q_type == 'judge':
            self._show_judge_options()
        elif q_type == 'fill':
            self._show_fill_input()
        elif q_type == 'code':
            self._show_code_input()

    def _clear_answer_area(self):
        """清空答题区域"""
        while self.answer_input_layout.count():
            child = self.answer_input_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _show_choice_options(self, options):
        """显示选择题选项"""
        self.answer_input_frame.setVisible(True)
        self.choice_group = QButtonGroup()
        self.choice_group.setExclusive(True)

        import json
        try:
            if isinstance(options, str):
                options_list = json.loads(options)
            else:
                options_list = options

            for i, opt in enumerate(options_list):
                radio = QRadioButton(opt)
                radio.setFont(QFont("Microsoft YaHei", 16))
                radio.setStyleSheet(f"""
                    QRadioButton {{
                        padding: 12px 16px;
                        margin: 4px 0;
                        border-radius: 8px;
                    }}
                    QRadioButton:hover {{
                        background: {COLORS['primary_alpha_hover']};
                    }}
                    QRadioButton::indicator {{
                        width: 20px;
                        height: 20px;
                    }}
                """)
                self.choice_group.addButton(radio, i)
                self.answer_input_layout.addWidget(radio)
        except Exception as e:
            print(f"解析选项失败: {e}")

    def _show_judge_options(self):
        """显示判断题选项"""
        self.answer_input_frame.setVisible(True)
        self.judge_group = QButtonGroup()
        self.judge_group.setExclusive(True)

        for i, text in enumerate(["✓ 正确", "✗ 错误"]):
            radio = QRadioButton(text)
            radio.setFont(QFont("Microsoft YaHei", 16))
            radio.setStyleSheet(f"""
                QRadioButton {{
                    padding: 12px 16px;
                    margin: 4px 0;
                    border-radius: 8px;
                }}
                QRadioButton:hover {{
                    background: {COLORS['primary_alpha_hover']};
                }}
                QRadioButton::indicator {{
                    width: 20px;
                    height: 20px;
                }}
            """)
            self.judge_group.addButton(radio, i)
            self.answer_input_layout.addWidget(radio)

    def _show_fill_input(self):
        """显示填空题输入框"""
        self.answer_input_frame.setVisible(True)
        self.fill_input = QLineEdit()
        self.fill_input.setPlaceholderText("请输入答案...")
        self.fill_input.setMinimumHeight(50)
        self.fill_input.setFont(QFont("Microsoft YaHei", 16))
        self.fill_input.setStyleSheet(f"""
            QLineEdit {{
                background: white;
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px 16px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        self.answer_input_layout.addWidget(self.fill_input)

    def _show_code_input(self):
        """显示编程题输入框"""
        self.answer_input_frame.setVisible(True)
        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText("请输入 Python 代码...")
        self.code_input.setMinimumHeight(150)
        self.code_input.setFont(QFont("Consolas", 15))
        self.code_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['code_bg']};
                color: {COLORS['code_text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        self.answer_input_layout.addWidget(self.code_input)

    def _get_answer(self):
        """获取用户答案"""
        q = self.current_question
        q_type = q.get('type', '')

        if q_type == 'choice':
            if hasattr(self, 'choice_group') and self.choice_group.checkedButton():
                return self.choice_group.checkedButton().text()
        elif q_type == 'judge':
            if hasattr(self, 'judge_group') and self.judge_group.checkedButton():
                return "正确" if self.judge_group.checkedId() == 0 else "错误"
        elif q_type == 'fill':
            if hasattr(self, 'fill_input'):
                return self.fill_input.text().strip()
        elif q_type == 'code':
            if hasattr(self, 'code_input'):
                return self.code_input.toPlainText().strip()
        return None

    def _submit_answer(self):
        """提交答案"""
        answer = self._get_answer()
        if not answer:
            QMessageBox.warning(self, '提示', '请先作答！')
            return

        q = self.current_question
        correct_answer = q.get('answer', '')
        q_type = q.get('type', '')

        # 判断是否正确
        is_correct = False
        if q_type == 'choice':
            is_correct = (answer.strip() == correct_answer.strip())
        elif q_type == 'judge':
            is_correct = (answer.strip() == correct_answer.strip())
        elif q_type == 'fill':
            is_correct = (answer.strip().lower() == correct_answer.strip().lower())
        elif q_type == 'code':
            is_correct = False  # 编程题需要手动判断

        # 显示结果
        self.result_label.setVisible(True)
        if is_correct:
            self.result_label.setText("✓ 回答正确！已从错题本移除")
            self.result_label.setStyleSheet(f"color: {COLORS['success']}; background: transparent; padding: 8px;")
            # 正确则移出错题本
            data_service.mark_wrong_question_mastered(self.current_user.id, q['question_id'])
            self.wrong_questions.pop(self.current_index)
            if self.current_index >= len(self.wrong_questions):
                self.current_index = max(0, len(self.wrong_questions) - 1)
            # 延迟跳转下一题
            QTimer.singleShot(1500, self._next_or_finish)
        else:
            self.result_label.setText(f"✗ 回答错误！")
            self.result_label.setStyleSheet(f"color: {COLORS['danger']}; background: transparent; padding: 8px;")
            # 显示正确答案
            self.answer_label.setText(f"正确答案: {correct_answer}")
            self.answer_label.setVisible(True)

        # 显示解析
        explanation = q.get('explanation', '')
        if explanation:
            self.answer_label.setText(f"正确答案: {correct_answer}\n\n解析: {explanation}")
            self.answer_label.setVisible(True)

        self.submit_btn.setEnabled(False)

    def _next_or_finish(self):
        """跳转下一题或结束"""
        if self.current_index >= len(self.wrong_questions):
            QMessageBox.information(self, '复习完成', '所有错题已复习完成！')
            self.review_mode = False
            self._clear_answer_area()
            self.question_text.clear()
            self.result_label.setVisible(False)
            self.answer_label.setVisible(False)
        else:
            self._show_question()

    def _next_question(self):
        """下一题"""
        if self.current_index < len(self.wrong_questions) - 1:
            self.current_index += 1
            self._show_question()
        else:
            QMessageBox.information(self, '提示', '已经是最后一题了')

    def refresh(self):
        """刷新数据"""
        self.wrong_questions = data_service.get_user_wrong_questions(self.current_user.id)
        self.count_label.setText(f"共 {len(self.wrong_questions)} 道错题")
