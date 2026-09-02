# -*- coding: utf-8 -*-
"""
模拟考试模块
"""
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QRadioButton,
    QButtonGroup, QMessageBox, QGroupBox, QProgressBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from core.services.exam_service import exam_service
from ui.styles.theme import COLORS, FONTS, SIZES
import time


class ExamWidget(QWidget):
    """模拟考试界面"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.current_exam = None
        self.exam_record_id = None
        self.questions = []
        self.answers = {}
        self.current_index = 0
        self.start_time = None
        self.timer = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("📝 模拟考试")
        title.setFont(QFont(*FONTS['heading']))
        title.setStyleSheet(f"color: {COLORS['primary']}; background: transparent;")
        layout.addWidget(title)

        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Microsoft YaHei", 16))
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{
                padding: 14px 28px;
                border-bottom: 2px solid transparent;
                color: {COLORS['text_secondary']};
                font-size: 17px;
            }}
            QTabBar::tab:selected {{
                color: {COLORS['primary']};
                border-bottom: 2px solid {COLORS['primary']};
                font-weight: bold;
            }}
        """)

        # 考试列表
        self.exam_list = QListWidget()
        self.exam_list.setFont(QFont("Microsoft YaHei", 16))
        self.exam_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
            }}
            QListWidget::item {{
                padding: 16px;
                border-radius: 8px;
                margin: 4px 0;
            }}
            QListWidget::item:hover {{
                background: {COLORS['primary_alpha_hover']};
            }}
        """)
        self.exam_list.itemClicked.connect(self._show_exam_detail)
        self.tab_widget.addTab(self.exam_list, "可用考试")

        # 考试中
        self.exam_widget = QWidget()
        self.exam_layout = QVBoxLayout(self.exam_widget)
        self.tab_widget.addTab(self.exam_widget, "考试进行中")

        # 考试记录
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(['考试名称', '时间', '得分', '用时', '状态'])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tab_widget.addTab(self.history_table, "考试记录")

        layout.addWidget(self.tab_widget, 1)

        self._load_exams()

    def _load_exams(self):
        exams = exam_service.get_all_exams()
        self.exam_list.clear()
        for exam in exams:
            item = QListWidgetItem(f"{exam['name']} ({exam['difficulty']}) - {exam['duration']}分钟")
            item.setData(Qt.UserRole, exam)
            self.exam_list.addItem(item)

    def _show_exam_detail(self, item):
        self.current_exam = item.data(Qt.UserRole)
        # 清空考试中界面
        while self.exam_layout.count():
            child = self.exam_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        detail = QLabel(f"考试: {self.current_exam['name']}\n时长: {self.current_exam['duration']}分钟\n总分: {self.current_exam['total_score']}")
        self.exam_layout.addWidget(detail)

        start_btn = QPushButton("开始考试")
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
            }}
        """)
        start_btn.clicked.connect(self._start_exam)
        self.exam_layout.addWidget(start_btn)

        self.exam_layout.addStretch()

    def _start_exam(self):
        if not self.current_exam:
            return

        reply = self._show_question_box('确认', f"确定开始「{self.current_exam['name']}」考试？")
        if not reply:
            return

        try:
            self.questions = exam_service.get_exam_questions(self.current_exam['id'])
            self.exam_record_id = exam_service.start_exam(
                self.current_user.id, self.current_exam['id']
            )
            self.answers = {}
            self.current_index = 0
            self.start_time = time.time()

            # 显示题目
            self.tab_widget.setCurrentIndex(1)
            self._show_question()
        except Exception as e:
            self._show_error_box('错误', f'开始考试失败: {e}')

    def _show_question_box(self, title, text):
        """显示带样式的确认对话框"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-size: 16px;
            }
            QMessageBox QLabel {
                color: #1E293B;
                font-size: 16px;
                min-width: 300px;
            }
            QMessageBox QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: #1D4ED8;
            }
        """)
        return msg.exec_() == QMessageBox.Yes

    def _show_info_box(self, title, text):
        """显示带样式的提示对话框"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-size: 16px;
            }
            QMessageBox QLabel {
                color: #1E293B;
                font-size: 16px;
                min-width: 300px;
            }
            QMessageBox QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: #1D4ED8;
            }
        """)
        msg.exec_()

    def _show_error_box(self, title, text):
        """显示带样式的错误对话框"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-size: 16px;
            }
            QMessageBox QLabel {
                color: #1E293B;
                font-size: 16px;
                min-width: 300px;
            }
            QMessageBox QPushButton {
                background: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: #DC2626;
            }
        """)
        msg.exec_()

    def _show_question(self):
        if self.current_index >= len(self.questions):
            return

        # 清空
        while self.exam_layout.count():
            child = self.exam_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        q = self.questions[self.current_index]

        # 题目
        title = QLabel(f"第 {self.current_index + 1} 题 ({q['score']}分)")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']}; background: transparent;")
        self.exam_layout.addWidget(title)

        question_text = QLabel(q['question'])
        question_text.setWordWrap(True)
        question_text.setFont(QFont("Microsoft YaHei", 16))
        question_text.setStyleSheet(f"background: {COLORS['glass_bg']}; padding: 16px; border-radius: 8px;")
        self.exam_layout.addWidget(question_text)

        # 答题区
        self.button_group = QButtonGroup()
        if q['type'] == 'choice':
            import json
            options = json.loads(q['options']) if q['options'] else []
            for i, opt in enumerate(options):
                # 如果选项已经有 A. B. C. D. 前缀，不再添加
                if opt and len(opt) > 2 and opt[0] in 'ABCDEFGH' and opt[1] in '.．、':
                    radio = QRadioButton(opt)
                else:
                    radio = QRadioButton(f"{chr(65+i)}. {opt}")
                radio.setFont(QFont("Microsoft YaHei", 15))
                radio.setStyleSheet("""
                    QRadioButton {
                        padding: 12px 16px;
                        margin: 4px 0;
                        border-radius: 8px;
                    }
                    QRadioButton:hover {
                        background: rgba(37, 99, 235, 0.1);
                    }
                    QRadioButton::indicator {
                        width: 20px;
                        height: 20px;
                    }
                """)
                self.button_group.addButton(radio, i)
                self.exam_layout.addWidget(radio)
        elif q['type'] == 'judge':
            for i, text in enumerate(["正确", "错误"]):
                radio = QRadioButton(text)
                radio.setFont(QFont("Microsoft YaHei", 15))
                radio.setStyleSheet("""
                    QRadioButton {
                        padding: 12px 16px;
                        margin: 4px 0;
                        border-radius: 8px;
                    }
                    QRadioButton:hover {
                        background: rgba(37, 99, 235, 0.1);
                    }
                    QRadioButton::indicator {
                        width: 20px;
                        height: 20px;
                    }
                """)
                self.button_group.addButton(radio, i)
                self.exam_layout.addWidget(radio)

        # 按钮
        btn_layout = QHBoxLayout()
        prev_btn = QPushButton("上一题")
        prev_btn.clicked.connect(self._prev_question)
        prev_btn.setEnabled(self.current_index > 0)
        btn_layout.addWidget(prev_btn)

        submit_btn = QPushButton("提交考试")
        submit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
            }}
        """)
        submit_btn.clicked.connect(self._submit_exam)
        btn_layout.addWidget(submit_btn)

        next_btn = QPushButton("下一题")
        next_btn.clicked.connect(self._next_question)
        next_btn.setEnabled(self.current_index < len(self.questions) - 1)
        btn_layout.addWidget(next_btn)

        self.exam_layout.addLayout(btn_layout)

    def _prev_question(self):
        if self.current_index > 0:
            self._save_answer()
            self.current_index -= 1
            self._show_question()

    def _next_question(self):
        if self.current_index < len(self.questions) - 1:
            self._save_answer()
            self.current_index += 1
            self._show_question()

    def _save_answer(self):
        if self.current_index >= len(self.questions):
            return
        q = self.questions[self.current_index]
        if q['type'] in ['choice', 'judge']:
            checked = self.button_group.checkedId()
            if checked >= 0:
                self.answers[q['id']] = chr(65 + checked) if q['type'] == 'choice' else ('正确' if checked == 0 else '错误')

    def _submit_exam(self):
        self._save_answer()

        reply = self._show_question_box(
            '确认提交',
            f'已答 {len(self.answers)}/{len(self.questions)} 题\n确定提交？'
        )
        if not reply:
            return

        result = exam_service.submit_exam(
            self.exam_record_id, self.answers, self.questions, self.start_time
        )

        msg = f"得分: {result['obtained_score']}/{result['total_score']}\n用时: {result['time_spent']}分钟\n{'及格' if result['passed'] else '不及格'}"
        self._show_info_box('考试结果', msg)

        self.tab_widget.setCurrentIndex(2)
        self._load_history()

    def _load_history(self):
        records = exam_service.get_user_exam_records(self.current_user.id)
        self.history_table.setRowCount(0)
        for record in records:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(record.get('exam_name', '')))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(record.get('start_time', ''))[:19]))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(record.get('obtained_score', 0))))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(record.get('time_spent', 0))))
            self.history_table.setItem(row, 4, QTableWidgetItem(record.get('status', '')))

    def refresh(self):
        self._load_exams()
        self._load_history()
