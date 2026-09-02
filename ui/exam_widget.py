# -*- coding: utf-8 -*-
"""
模拟考试模块
提供PTA风格的考试功能，支持多测试点编程题并发验证
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem, QTextEdit,
                             QRadioButton, QButtonGroup, QGroupBox,
                             QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QScrollArea, QFrame, QLineEdit, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QColor
from config import THEME_COLORS
from database.db_manager import DatabaseManager
from utils.code_executor import CodeExecutor
from ui.styles.message_box import show_info, show_warning, show_error, ask_question
import json
import time


class ExamWidget(QWidget):
    """模拟考试模块"""

    def __init__(self, user):
        """
        初始化考试模块
        :param user: 当前登录用户
        """
        super().__init__()
        self.current_user = user
        self.db = DatabaseManager()

        # 考试状态
        self.current_exam = None
        self.exam_record_id = None
        self.current_question_index = 0
        self.questions = []
        self.answers = {}
        self.start_time = None
        self.timer = None

        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel('📝 模拟考试')
        title_label.setFont(QFont('Microsoft YaHei', 22, QFont.Bold))
        title_label.setStyleSheet(f'color: {THEME_COLORS["primary"]}; padding: 15px;')
        main_layout.addWidget(title_label)

        # 创建Tab标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont('Microsoft YaHei', 12))

        # 考试列表标签页
        self.exam_list_widget = self.create_exam_list_widget()
        self.tab_widget.addTab(self.exam_list_widget, '可用考试')

        # 考试中标签页
        self.exam_progress_widget = self.create_exam_progress_widget()
        self.tab_widget.addTab(self.exam_progress_widget, '考试进行中')

        # 考试记录标签页
        self.exam_history_widget = self.create_exam_history_widget()
        self.tab_widget.addTab(self.exam_history_widget, '考试记录')

        main_layout.addWidget(self.tab_widget)

        self.setLayout(main_layout)

        # 初始加载考试列表
        self.load_available_exams()

    def create_exam_list_widget(self):
        """创建考试列表界面"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 说明文字
        info_label = QLabel('选择一场考试开始测试：')
        info_label.setFont(QFont('Microsoft YaHei', 11))
        layout.addWidget(info_label)

        # 考试列表
        self.exam_list = QListWidget()
        self.exam_list.setFont(QFont('Microsoft YaHei', 11))
        self.exam_list.setStyleSheet(f'''
            QListWidget {{
                border: 2px solid {THEME_COLORS["primary"]};
                border-radius: 8px;
                padding: 10px;
                background-color: white;
            }}
            QListWidget::item {{
                padding: 15px;
                margin: 5px;
                border-radius: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {THEME_COLORS["primary"]};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {THEME_COLORS["background"]};
            }}
        ''')
        self.exam_list.itemClicked.connect(self.show_exam_detail)
        layout.addWidget(self.exam_list)

        # 考试详情显示
        detail_group = QGroupBox('考试详情')
        detail_group.setFont(QFont('Microsoft YaHei', 11))
        detail_layout = QVBoxLayout()

        self.exam_detail_label = QLabel('请选择一场考试查看详情')
        self.exam_detail_label.setWordWrap(True)
        self.exam_detail_label.setFont(QFont('Microsoft YaHei', 10))
        self.exam_detail_label.setStyleSheet('padding: 15px;')
        detail_layout.addWidget(self.exam_detail_label)

        # 开始考试按钮
        self.start_exam_button = QPushButton('🚀 开始考试')
        self.start_exam_button.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        self.start_exam_button.setMinimumHeight(50)
        self.start_exam_button.setStyleSheet(f'''
            QPushButton {{
                background-color: {THEME_COLORS["success"]};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #5ea365;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
            }}
        ''')
        self.start_exam_button.clicked.connect(self.start_exam)
        self.start_exam_button.setEnabled(False)
        detail_layout.addWidget(self.start_exam_button)

        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)

        widget.setLayout(layout)
        return widget

    def create_exam_progress_widget(self):
        """创建考试进行中界面"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 考试信息和计时器
        info_layout = QHBoxLayout()

        self.exam_info_label = QLabel('当前无考试')
        self.exam_info_label.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        info_layout.addWidget(self.exam_info_label)

        info_layout.addStretch()

        self.timer_label = QLabel('剩余时间: --:--')
        self.timer_label.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        self.timer_label.setStyleSheet(f'color: {THEME_COLORS["danger"]};')
        info_layout.addWidget(self.timer_label)

        layout.addLayout(info_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('%v / %m 题')
        self.progress_bar.setStyleSheet(f'''
            QProgressBar {{
                border: 2px solid {THEME_COLORS["primary"]};
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME_COLORS["success"]};
            }}
        ''')
        layout.addWidget(self.progress_bar)

        # 题目显示区域（固定高度，保证题目位置稳定）
        self.question_widget = QWidget()
        self.question_layout = QVBoxLayout()
        self.question_layout.setContentsMargins(0, 0, 0, 0)
        self.question_widget.setLayout(self.question_layout)
        self.question_widget.setMinimumHeight(480)
        self.question_widget.setMaximumHeight(480)

        scroll = QScrollArea()
        scroll.setWidget(self.question_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('''
            QScrollArea {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
        ''')
        layout.addWidget(scroll)

        # 导航按钮
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(12)
        nav_layout.setContentsMargins(0, 12, 0, 12)

        self.prev_button = QPushButton('上一题')
        self.prev_button.setFont(QFont('Microsoft YaHei', 13))
        self.prev_button.setMinimumHeight(70)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.prev_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.prev_button.clicked.connect(self.prev_question)
        nav_layout.addWidget(self.prev_button)

        self.next_button = QPushButton('下一题')
        self.next_button.setFont(QFont('Microsoft YaHei', 13))
        self.next_button.setMinimumHeight(70)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.next_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.next_button.clicked.connect(self.next_question)
        nav_layout.addWidget(self.next_button)

        self.submit_exam_button = QPushButton('提交考试')
        self.submit_exam_button.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        self.submit_exam_button.setMinimumHeight(70)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.submit_exam_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.submit_exam_button.setStyleSheet(f'''
            QPushButton {{
                background-color: {THEME_COLORS["primary"]};
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #4a8fc7;
            }}
        ''')
        self.submit_exam_button.clicked.connect(self.submit_exam)
        nav_layout.addWidget(self.submit_exam_button)

        layout.addLayout(nav_layout)

        widget.setLayout(layout)
        return widget

    def create_exam_history_widget(self):
        """创建考试记录界面"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 说明
        info_label = QLabel('查看历史考试记录：')
        info_label.setFont(QFont('Microsoft YaHei', 11))
        layout.addWidget(info_label)

        # 考试记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            '考试名称', '开始时间', '结束时间', '用时(分钟)',
            '总分', '得分', '状态'
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setStyleSheet('''
            QTableWidget {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #5B9BD5;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        ''')
        layout.addWidget(self.history_table)

        # 刷新按钮
        refresh_button = QPushButton('🔄 刷新记录')
        refresh_button.setFont(QFont('Microsoft YaHei', 11))
        refresh_button.setMinimumHeight(40)
        refresh_button.clicked.connect(self.load_exam_history)
        layout.addWidget(refresh_button)

        widget.setLayout(layout)
        return widget

    def load_available_exams(self):
        """加载可用的考试列表"""
        try:
            self.db.connect()
            result = self.db.execute_query(
                'SELECT * FROM exams ORDER BY created_at DESC'
            )

            self.exam_list.clear()
            for row in result:
                exam = dict(row)
                item_text = f"{exam['name']} ({exam['difficulty']}) - {exam['duration']}分钟"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, exam)
                self.exam_list.addItem(item)

        except Exception as e:
            show_warning(self, '错误', f'加载考试列表失败: {str(e)}')
        finally:
            self.db.disconnect()

    def show_exam_detail(self, item):
        """显示考试详情"""
        exam = item.data(Qt.UserRole)
        if not exam:
            return

        detail_text = f"""
<h3>{exam['name']}</h3>
<p><b>描述：</b>{exam.get('description', '无')}</p>
<p><b>难度：</b>{exam['difficulty']}</p>
<p><b>时长：</b>{exam['duration']} 分钟</p>
<p><b>总分：</b>{exam['total_score']} 分</p>
<p><b>及格分：</b>{exam['pass_score']} 分</p>
<p><b>分类：</b>{exam.get('category', '综合')}</p>
        """
        self.exam_detail_label.setText(detail_text)
        self.current_exam = exam
        self.start_exam_button.setEnabled(True)

    def start_exam(self):
        """开始考试"""
        if not self.current_exam:
            show_warning(self, '提示', '请先选择一场考试')
            return

        # 确认开始考试
        reply = ask_question(
            self, '确认',
            f"确定要开始「{self.current_exam['name']}」考试吗？\n考试时长：{self.current_exam['duration']}分钟",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # 加载考试题目
            self.load_exam_questions()

            # 创建考试记录
            self.create_exam_record()

            # 初始化答案字典
            self.answers = {}
            self.current_question_index = 0

            # 开始计时
            self.start_time = time.time()
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_timer)
            self.timer.start(1000)  # 每秒更新

            # 切换到考试界面
            self.tab_widget.setCurrentWidget(self.exam_progress_widget)

            # 显示第一题
            self.show_question()

            # 更新进度
            self.update_progress()

            show_info(self, '提示', '考试已开始，请认真作答！')

        except Exception as e:
            show_error(self, '错误', f'开始考试失败: {str(e)}')

    def load_exam_questions(self):
        """加载考试题目"""
        try:
            self.db.connect()
            result = self.db.execute_query('''
                SELECT q.*, eq.score, eq.order_num
                FROM questions q
                JOIN exam_questions eq ON q.id = eq.question_id
                WHERE eq.exam_id = ?
                ORDER BY eq.order_num
            ''', (self.current_exam['id'],))

            self.questions = [dict(row) for row in result]

            if not self.questions:
                raise Exception('该考试没有题目')

        finally:
            self.db.disconnect()

    def create_exam_record(self):
        """创建考试记录"""
        try:
            self.db.connect()
            self.db.cursor.execute('''
                INSERT INTO exam_records (user_id, exam_id, total_score, status)
                VALUES (?, ?, ?, 'in_progress')
            ''', (self.current_user.id, self.current_exam['id'], self.current_exam['total_score']))
            self.exam_record_id = self.db.cursor.lastrowid
            self.db.commit()
        finally:
            self.db.disconnect()

    def show_question(self):
        """显示当前题目"""
        # 清空题目区域
        for i in reversed(range(self.question_layout.count())):
            widget = self.question_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if self.current_question_index >= len(self.questions):
            return

        question = self.questions[self.current_question_index]

        # 题目标题
        title_label = QLabel(f"第 {self.current_question_index + 1} 题 ({question['score']}分)")
        title_label.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        title_label.setStyleSheet(f'color: {THEME_COLORS["primary"]}; padding: 10px;')
        self.question_layout.addWidget(title_label)

        # 题目内容
        question_label = QLabel(f"<b>{question['question']}</b>")
        question_label.setWordWrap(True)
        question_label.setFont(QFont('Microsoft YaHei', 15))
        question_label.setStyleSheet('padding: 10px; background-color: white; border-radius: 5px;')
        self.question_layout.addWidget(question_label)

        # 根据题型显示答题区域
        q_type = question.get('type', '')
        if q_type == 'choice':
            self.show_choice_question(question)
        elif q_type == 'judge':
            self.show_judge_question(question)
        elif q_type == 'fill':
            self.show_fill_question(question)
        elif q_type == 'code':
            self.show_coding_question(question)
        else:
            # 如果类型不匹配，显示警告
            warning_label = QLabel(f'未知题型: {q_type}')
            warning_label.setFont(QFont('Microsoft YaHei', 10))
            warning_label.setStyleSheet('color: red; padding: 10px;')
            self.question_layout.addWidget(warning_label)

        # 由于固定了高度，不再需要 addStretch() 来填充剩余空间


    def show_choice_question(self, question):
        """显示选择题"""
        try:
            # 调试：打印 options 字段的原始值
            print(f"[DEBUG] question['options'] = {question.get('options', 'KEY_NOT_FOUND')}")

            options = json.loads(question['options']) if question['options'] else []

            # 调试：打印解析后的选项数量
            print(f"[DEBUG] Parsed {len(options)} options: {options}")

            if not options:
                # 如果没有选项，显示警告
                warning_label = QLabel("⚠️ 该题目缺少选项数据")
                warning_label.setFont(QFont('Microsoft YaHei', 10))
                warning_label.setStyleSheet('color: red; padding: 10px;')
                self.question_layout.addWidget(warning_label)
                return

            self.button_group = QButtonGroup()
            for i, option in enumerate(options):
                radio = QRadioButton(f"{chr(65+i)}. {option}")
                radio.setFont(QFont('Microsoft YaHei', 13))
                radio.setStyleSheet('padding: 8px; background-color: white;')
                self.button_group.addButton(radio, i)

                # 恢复之前的答案
                if question['id'] in self.answers and self.answers[question['id']] == chr(65+i):
                    radio.setChecked(True)

                self.question_layout.addWidget(radio)
                print(f"[DEBUG] Added radio button: {chr(65+i)}. {option}")

            # 保存答案
            self.button_group.buttonClicked.connect(
                lambda btn: self.save_answer(question['id'], chr(65+self.button_group.id(btn)))
            )
        except Exception as e:
            # 显示错误信息
            error_label = QLabel(f"❌ 选项加载失败: {str(e)}")
            error_label.setFont(QFont('Microsoft YaHei', 10))
            error_label.setStyleSheet('color: red; padding: 10px;')
            self.question_layout.addWidget(error_label)
            print(f"[ERROR] show_choice_question failed: {e}")
            import traceback
            traceback.print_exc()


    def show_judge_question(self, question):
        """显示判断题"""
        self.button_group = QButtonGroup()

        true_radio = QRadioButton('正确')
        true_radio.setFont(QFont('Microsoft YaHei', 13))
        true_radio.setStyleSheet('padding: 8px; background-color: white;')
        self.button_group.addButton(true_radio, 1)
        self.question_layout.addWidget(true_radio)

        false_radio = QRadioButton('错误')
        false_radio.setFont(QFont('Microsoft YaHei', 13))
        false_radio.setStyleSheet('padding: 8px; background-color: white;')
        self.button_group.addButton(false_radio, 0)
        self.question_layout.addWidget(false_radio)

        # 恢复之前的答案
        if question['id'] in self.answers:
            if self.answers[question['id']] == '正确':
                true_radio.setChecked(True)
            else:
                false_radio.setChecked(True)

        # 保存答案
        self.button_group.buttonClicked.connect(
            lambda btn: self.save_answer(question['id'], '正确' if self.button_group.id(btn) == 1 else '错误')
        )

    def show_fill_question(self, question):
        """显示填空题"""
        self.answer_input = QLineEdit()
        self.answer_input.setFont(QFont('Microsoft YaHei', 10))
        self.answer_input.setPlaceholderText('请输入答案...')
        self.answer_input.setStyleSheet('''
            QLineEdit {
                padding: 10px;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                font-size: 12px;
            }
        ''')

        # 恢复之前的答案
        if question['id'] in self.answers:
            self.answer_input.setText(self.answers[question['id']])

        self.answer_input.textChanged.connect(
            lambda text: self.save_answer(question['id'], text)
        )
        self.question_layout.addWidget(self.answer_input)

    def show_coding_question(self, question):
        """显示编程题"""
        # 代码编辑器
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont('Consolas', 10))
        self.code_editor.setPlaceholderText('# 请在此编写Python代码...\n')
        self.code_editor.setStyleSheet('''
            QTextEdit {
                background-color: #2b2b2b;
                color: #f8f8f2;
                border: 2px solid #5B9BD5;
                border-radius: 5px;
                padding: 10px;
            }
        ''')
        self.code_editor.setMinimumHeight(300)

        # 恢复之前的答案
        if question['id'] in self.answers:
            self.code_editor.setText(self.answers[question['id']])

        self.code_editor.textChanged.connect(
            lambda: self.save_answer(question['id'], self.code_editor.toPlainText())
        )
        self.question_layout.addWidget(self.code_editor)

        # 测试点提示
        hint_label = QLabel('💡 提示：本题将通过多个测试点进行评分')
        hint_label.setFont(QFont('Microsoft YaHei', 9))
        hint_label.setStyleSheet(f'color: {THEME_COLORS["info"]}; padding: 5px;')
        self.question_layout.addWidget(hint_label)

    def save_answer(self, question_id, answer):
        """保存答案"""
        self.answers[question_id] = answer

    def update_timer(self):
        """更新计时器"""
        if not self.start_time:
            return

        elapsed = int(time.time() - self.start_time)
        total_seconds = self.current_exam['duration'] * 60
        remaining = total_seconds - elapsed

        if remaining <= 0:
            # 时间到，自动提交
            self.timer.stop()
            show_warning(self, '时间到', '考试时间已到，系统将自动提交！')
            self.submit_exam()
            return

        minutes = remaining // 60
        seconds = remaining % 60
        self.timer_label.setText(f'剩余时间: {minutes:02d}:{seconds:02d}')

        # 最后5分钟提醒
        if remaining == 300:
            show_warning(self, '提醒', '还剩5分钟，请抓紧时间！')

    def update_progress(self):
        """更新进度条"""
        self.progress_bar.setMaximum(len(self.questions))
        self.progress_bar.setValue(self.current_question_index + 1)

        # 更新考试信息
        if self.current_exam:
            self.exam_info_label.setText(f"考试: {self.current_exam['name']} | 第 {self.current_question_index + 1}/{len(self.questions)} 题")

    def prev_question(self):
        """上一题"""
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.show_question()
            self.update_progress()

    def next_question(self):
        """下一题"""
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.show_question()
            self.update_progress()

    def submit_exam(self):
        """提交考试"""
        # 确认提交
        reply = ask_question(
            self, '确认提交',
            f'已答 {len(self.answers)}/{len(self.questions)} 题\n确定要提交考试吗？',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # 停止计时
        if self.timer:
            self.timer.stop()

        # 计算用时
        time_spent = int((time.time() - self.start_time) / 60) if self.start_time else 0

        try:
            # 统一连接数据库，避免嵌套连接导致锁定
            self.db.connect()

            # 判题并保存结果（使用内部方法，不再嵌套connect）
            total_score = 0
            for question in self.questions:
                score = self.grade_question_internal(question)
                total_score += score

            # 更新考试记录
            self.db.cursor.execute('''
                UPDATE exam_records
                SET end_time = CURRENT_TIMESTAMP,
                    obtained_score = ?,
                    status = 'completed',
                    time_spent = ?
                WHERE id = ?
            ''', (total_score, time_spent, self.exam_record_id))
            self.db.commit()

            # 显示成绩
            pass_score = self.current_exam['pass_score']
            passed = total_score >= pass_score
            result_msg = f"""
考试已提交！

得分：{total_score} / {self.current_exam['total_score']}
用时：{time_spent} 分钟
结果：{'✓ 及格' if passed else '✗ 不及格'}
            """
            show_info(self, '考试结果', result_msg)

            # 切换到考试记录页
            self.load_exam_history()
            self.tab_widget.setCurrentWidget(self.exam_history_widget)

            # 重置状态
            self.current_exam = None
            self.exam_record_id = None
            self.questions = []
            self.answers = {}
            self.start_time = None

            # 清空考试进行中界面
            for i in reversed(range(self.question_layout.count())):
                widget = self.question_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # 重置界面显示
            self.exam_info_label.setText('当前无考试')
            self.timer_label.setText('剩余时间: --:--')
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(0)
            
            # 停止计时器
            if self.timer:
                self.timer.stop()

        except Exception as e:
            show_error(self, '错误', f'提交考试失败: {str(e)}')
        finally:
            self.db.disconnect()

    def grade_question(self, question):
        """判题并返回得分（带数据库连接管理，供外部调用）"""
        try:
            self.db.connect()
            score = self.grade_question_internal(question)
            self.db.commit()
            return score
        finally:
            self.db.disconnect()

    def grade_question_internal(self, question):
        """判题并返回得分（内部方法，假设数据库已连接）"""
        question_id = question['id']
        if question_id not in self.answers:
            # 未作答
            return 0

        user_answer = self.answers[question_id]
        correct_answer = question['answer']
        score = question['score']

        is_correct = False

        if question['type'] == 'code':
            # 编程题通过测试点判题
            score = self.grade_coding_question_internal(question, user_answer)
            is_correct = score > 0
        else:
            # 其他题型直接比对答案
            if question['type'] == 'fill':
                is_correct = user_answer.strip() == correct_answer.strip()
            else:
                is_correct = user_answer == correct_answer

            score = score if is_correct else 0

        # 记录答题详情（假设已连接）
        self.db.cursor.execute('''
            INSERT INTO exam_answers (exam_record_id, question_id, user_answer, is_correct, obtained_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.exam_record_id, question_id, user_answer, is_correct, score))

        # 如果答错，加入错题本
        if not is_correct:
            self.add_to_wrong_questions_internal(question_id, 'exam')

        return score

    def grade_coding_question(self, question, user_code):
        """编程题判题（带数据库连接管理，供外部调用）"""
        try:
            self.db.connect()
            score = self.grade_coding_question_internal(question, user_code)
            self.db.commit()
            return score
        except Exception as e:
            print(f"编程题判题失败: {e}")
            return 0
        finally:
            self.db.disconnect()

    def grade_coding_question_internal(self, question, user_code):
        """编程题判题（PTA风格并发验证）"""
        # 获取测试点
        result = self.db.execute_query(
            'SELECT * FROM test_cases WHERE question_id = ? ORDER BY order_num',
            (question['id'],)
        )
        test_cases = [dict(row) for row in result]

        if not test_cases:
            # 没有测试点，使用标准答案比对
            return question['score'] if user_code.strip() == question['answer'].strip() else 0

        # 使用 PTA 风格并发验证
        executor = CodeExecutor()
        test_case_list = [
            {
                'input': tc.get('input_data', ''),
                'expected': tc.get('expected_output', ''),
                'score': tc.get('score', 1)
            }
            for tc in test_cases
        ]

        # 同步执行所有测试点（并发）
        passed_count = 0
        total_score = 0

        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=min(len(test_cases), 5)) as thread_executor:
            futures = {}
            for i, tc in enumerate(test_cases):
                future = thread_executor.submit(
                    executor.execute,
                    f"import sys\nfrom io import StringIO\nsys.stdin = StringIO('''{tc.get('input_data', '')}''')\n{user_code}"
                )
                futures[future] = i

            results = {}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    success, output, error = future.result()
                    expected = test_cases[idx].get('expected_output', '').strip()
                    actual = output.strip() if success else ''
                    passed = (actual == expected) and success
                except:
                    passed = False

                results[idx] = passed
                if passed:
                    passed_count += 1
                    total_score += test_cases[idx].get('score', 1)

        # 更新答题记录的测试点信息
        self.db.cursor.execute('''
            UPDATE exam_answers
            SET test_cases_passed = ?, test_cases_total = ?
            WHERE exam_record_id = ? AND question_id = ?
        ''', (passed_count, len(test_cases), self.exam_record_id, question['id']))

        return total_score

    def run_test_case(self, code, test_case):
        """运行单个测试点"""
        try:
            import io
            import sys
            from contextlib import redirect_stdout

            # 准备输入
            input_data = test_case['input_data']
            expected_output = test_case['expected_output'].strip()

            # 创建输入流
            old_stdin = sys.stdin
            sys.stdin = io.StringIO(input_data)

            # 捕获输出
            f = io.StringIO()
            with redirect_stdout(f):
                exec(code, {'__builtins__': __builtins__})

            # 恢复stdin
            sys.stdin = old_stdin

            # 比对输出
            actual_output = f.getvalue().strip()
            return actual_output == expected_output

        except Exception as e:
            print(f"测试点执行失败: {e}")
            return False

    def add_to_wrong_questions(self, question_id, source='exam'):
        """添加到错题本（带数据库连接管理，供外部调用）"""
        try:
            self.db.connect()
            self.add_to_wrong_questions_internal(question_id, source)
            self.db.commit()
        finally:
            self.db.disconnect()

    def add_to_wrong_questions_internal(self, question_id, source='exam'):
        """添加到错题本（内部方法，假设数据库已连接）"""
        self.db.cursor.execute('''
            INSERT OR REPLACE INTO wrong_questions
            (user_id, question_id, wrong_count, source, last_wrong_at)
            VALUES (
                ?,
                ?,
                COALESCE((SELECT wrong_count + 1 FROM wrong_questions WHERE user_id = ? AND question_id = ?), 1),
                ?,
                CURRENT_TIMESTAMP
            )
        ''', (self.current_user.id, question_id, self.current_user.id, question_id, source))

    def load_exam_history(self):
        """加载考试历史记录"""
        try:
            self.db.connect()
            result = self.db.execute_query('''
                SELECT er.*, e.name as exam_name
                FROM exam_records er
                JOIN exams e ON er.exam_id = e.id
                WHERE er.user_id = ?
                ORDER BY er.start_time DESC
            ''', (self.current_user.id,))

            self.history_table.setRowCount(0)
            for row in result:
                record = dict(row)
                row_position = self.history_table.rowCount()
                self.history_table.insertRow(row_position)

                # 填充数据
                self.history_table.setItem(row_position, 0, QTableWidgetItem(record['exam_name']))
                self.history_table.setItem(row_position, 1, QTableWidgetItem(record['start_time'][:19] if record['start_time'] else '-'))
                self.history_table.setItem(row_position, 2, QTableWidgetItem(record['end_time'][:19] if record['end_time'] else '-'))
                self.history_table.setItem(row_position, 3, QTableWidgetItem(str(record.get('time_spent', 0))))
                self.history_table.setItem(row_position, 4, QTableWidgetItem(str(record.get('exam_total_score', record.get('total_score', 0)))))
                self.history_table.setItem(row_position, 5, QTableWidgetItem(str(record['obtained_score'])))

                status_text = '已完成' if record['status'] == 'completed' else '进行中'
                self.history_table.setItem(row_position, 6, QTableWidgetItem(status_text))

        except Exception as e:
            show_warning(self, '错误', f'加载考试记录失败: {str(e)}')
        finally:
            self.db.disconnect()

    def refresh(self):
        """刷新界面"""
        self.load_available_exams()
        self.load_exam_history()

