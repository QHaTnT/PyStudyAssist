# -*- coding: utf-8 -*-
"""
错题本模块
显示和管理用户的错题
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QGroupBox,
                             QHeaderView, QTextEdit, QDialog, QDialogButtonBox,
                             QSplitter, QScrollArea, QFrame, QComboBox, QListWidget,
                             QListWidgetItem, QLineEdit, QProgressBar, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from utils.data_loader import DataLoader
from utils.code_executor import CodeExecutor
from models.question import Question
from ui.styles.message_box import show_info, show_warning, ask_question
from config import THEME_COLORS, QUESTION_TYPES
from database.db_manager import db_manager
from datetime import datetime


class MistakesWidget(QWidget):
    """错题本界面"""

    def __init__(self, user):
        """初始化错题本界面"""
        super().__init__()
        self.current_user = user
        # 代码执行器用于编程题重测
        self.code_executor = CodeExecutor()
        # 分栏尺寸缓存（进入复习前保存，退出时恢复）
        self._splitter_saved_sizes = None
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 标题和操作按钮
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # 避免全局 pageTitle 过大内边距，这里不使用该 objectName
        self.title_label = QLabel('我的错题本')
        self.title_label.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        self.title_label.setStyleSheet(f'color: {THEME_COLORS["danger"]}; padding: 4px 6px;')
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        refresh_btn = QPushButton('刷新')
        refresh_btn.setFont(QFont('Microsoft YaHei', 10))
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        # 顶部统计信息区已移除，使设置与分组更贴近标题

        # 主体：左右分栏
        self.body_splitter = QSplitter(Qt.Horizontal)
        self.body_splitter.setChildrenCollapsible(False)

        # 左侧：复习设置 + 卡片复习
        self.left_frame = QFrame()
        left_layout = QVBoxLayout(self.left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.settings_group = QGroupBox('复习设置')
        self.settings_group.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        self.settings_group.setStyleSheet('QGroupBox { padding-top: 25px; margin-top: 8px; border: 1px solid #ddd; border-radius: 4px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; top: 4px; padding: 0 5px; background-color: white; }')
        s_layout = QVBoxLayout()
        s_layout.setSpacing(6)
        s_layout.setContentsMargins(0, 0, 0, 0)

        # 当前知识点块（清透 + 立体效果）
        category_frame = QFrame()
        category_frame.setStyleSheet('''
            QFrame {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                              stop:0 rgba(255,255,255,200), stop:1 rgba(245,247,250,200));
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 10px;
                padding: 8px;
            }
        ''')
        category_layout = QVBoxLayout(category_frame)
        _shadow1 = QGraphicsDropShadowEffect(self)
        _shadow1.setBlurRadius(18)
        _shadow1.setOffset(0, 4)
        _shadow1.setColor(QColor(0, 0, 0, 60))
        category_frame.setGraphicsEffect(_shadow1)
        category_layout.setContentsMargins(6, 6, 6, 6)
        self.selected_category_label = QLabel('当前知识点：全部')
        self.selected_category_label.setFont(QFont('Microsoft YaHei', 12))
        category_layout.addWidget(self.selected_category_label)
        s_layout.addWidget(category_frame)
        # 题数选择块（清透 + 立体效果；默认横排：标签 + 题数）
        self.count_frame = QFrame()
        self.count_frame.setStyleSheet('''
            QFrame {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                              stop:0 rgba(255,255,255,200), stop:1 rgba(245,247,250,200));
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 10px;
                padding: 8px;
            }
        ''')
        self.count_layout = QVBoxLayout(self.count_frame)
        self.count_layout.setContentsMargins(6, 6, 6, 6)
        count_label = QLabel('每次复习题数：')
        count_label.setFont(QFont('Microsoft YaHei', 12))
        
        # 顶部横排（保持“设置好后的题数和文字在一排”）
        self.count_header_layout = QHBoxLayout()
        self.count_header_layout.setContentsMargins(0, 0, 0, 0)
        self.count_header_layout.setSpacing(8)
        self.count_header_layout.addWidget(count_label)

        # 用按钮显示当前选择的题数，点击时分割为上下两块
        self.review_count_btn = QPushButton('15题')
        self.review_count_btn.setFont(QFont('Microsoft YaHei', 13))
        self.review_count_btn.setMinimumHeight(28)
        self.review_count_btn.setCursor(Qt.PointingHandCursor)
        self.review_count_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(255,255,255,0.85);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 16px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.95); }
        ''')
        self.review_count_btn.clicked.connect(self.show_count_options_vertical)
        self.count_header_layout.addWidget(self.review_count_btn)
        self.count_header_layout.addStretch()
        self.count_layout.addLayout(self.count_header_layout)

        # 保存当前选择的题数
        self.review_count = 15

        # 阴影提升立体感
        _shadow2 = QGraphicsDropShadowEffect(self)
        _shadow2.setBlurRadius(18)
        _shadow2.setOffset(0, 4)
        _shadow2.setColor(QColor(0, 0, 0, 60))
        self.count_frame.setGraphicsEffect(_shadow2)
        s_layout.addWidget(self.count_frame)

        # 让整个题数框可点击，触发纵向上下拆分（上15/下25）
        def _count_frame_mousePress(event):
            try:
                # 仅当当前显示为“单一按钮”时，点击才触发拆分
                if self.review_count_btn.isVisible():
                    self.show_count_options_vertical()
                else:
                    QFrame.mousePressEvent(self.count_frame, event)
            except Exception:
                QFrame.mousePressEvent(self.count_frame, event)
        self.count_frame.mousePressEvent = _count_frame_mousePress

        # 开始复习块
        self.start_review_btn = QPushButton('开始复习')
        self.start_review_btn.setFont(QFont('Microsoft YaHei', 13))
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.start_review_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.start_review_btn.setMinimumHeight(52)
        self.start_review_btn.setStyleSheet(f'background-color: #f5f7fa; border-radius: 6px; padding: 8px;')
        self.start_review_btn.clicked.connect(self.start_review)
        s_layout.addWidget(self.start_review_btn)

        # 退出复习按钮（仅复习模式可见）
        self.exit_review_btn = QPushButton('退出复习')
        self.exit_review_btn.setFont(QFont('Microsoft YaHei', 12))
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.exit_review_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.exit_review_btn.setMinimumHeight(44)
        self.exit_review_btn.clicked.connect(self.exit_review_mode)
        self.exit_review_btn.setVisible(False)
        s_layout.addWidget(self.exit_review_btn)

        self.settings_group.setLayout(s_layout)
        left_layout.addWidget(self.settings_group)

        # 复习卡片区域
        self.card_group = QGroupBox('')
        self.card_group.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        self.card_group.setStyleSheet('QGroupBox { padding-top: 0px; margin-top: 0px; } QGroupBox::title { left: 10px; }')
        card_layout = QVBoxLayout()
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(0, 0, 0, 8)
        card_layout.setAlignment(Qt.AlignTop)

        # 卡片顶部退出按钮（只在复习模式显示）
        self.card_exit_btn = QPushButton('← 退出复习')
        self.card_exit_btn.setFont(QFont('Microsoft YaHei', 12))
        self.card_exit_btn.setStyleSheet('''
            QPushButton {
                background: transparent;
                border: none;
                color: #666;
                text-align: left;
                padding: 8px;
            }
            QPushButton:hover {
                color: #2d8cf0;
            }
        ''')
        self.card_exit_btn.setCursor(Qt.PointingHandCursor)
        self.card_exit_btn.clicked.connect(self.exit_review_mode)
        self.card_exit_btn.setVisible(False)
        card_layout.addWidget(self.card_exit_btn)

        # 进度条（浅灰色）
        self.review_progress_bar = QProgressBar()
        self.review_progress_bar.setStyleSheet('''
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f5f5f5;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #2d8cf0;
                border-radius: 3px;
            }
        ''')
        self.review_progress_bar.setVisible(False)
        self.review_progress_bar.setMaximumHeight(14)
        card_layout.addWidget(self.review_progress_bar)

        self.progress_label = QLabel('进度：0/0')
        self.progress_label.setFont(QFont('Microsoft YaHei', 12))
        self.progress_label.setMinimumHeight(22)
        card_layout.addWidget(self.progress_label)

        self.question_text = QTextEdit()
        self.question_text.setReadOnly(True)
        self.question_text.setFont(QFont('Microsoft YaHei', 16))
        self.question_text.setMinimumHeight(80)
        # 去掉固定最大高度，让内容自然决定高度
        # 题目置顶显示，移除中间弹性，保持题目与选项都靠上
        card_layout.addWidget(self.question_text)

        self.options_text = QTextEdit()
        self.options_text.setReadOnly(True)
        self.options_text.setFont(QFont('Microsoft YaHei', 14))
        self.options_text.setMinimumHeight(0)
        self.options_text.setVisible(False)
        card_layout.addWidget(self.options_text)

        self.answer_label = QLabel('')
        self.answer_label.setFont(QFont('Microsoft YaHei', 20, QFont.Bold))
        self.answer_label.setStyleSheet(f'color: {THEME_COLORS["success"]}; margin-top: -8px;')
        self.answer_label.setVisible(False)
        self.answer_label.setMinimumHeight(40)
        card_layout.addSpacing(5)
        card_layout.addWidget(self.answer_label)

        # 复习阶段按钮（左：模糊 / 中：查看答案 / 右：已掌握）
        self.review_btns_layout = QHBoxLayout()
        self.review_btns_layout.setSpacing(4)
        self.review_btns_layout.setContentsMargins(0, 0, 0, 0)
        self.ambiguous_btn = QPushButton('模糊')
        self.ambiguous_btn.setFont(QFont('Microsoft YaHei', 13))
        self.ambiguous_btn.clicked.connect(self.on_mark_ambiguous)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.ambiguous_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.ambiguous_btn.setMinimumHeight(70)
        self.review_btns_layout.addWidget(self.ambiguous_btn)

        self.show_answer_btn = QPushButton('查看答案')
        self.show_answer_btn.setFont(QFont('Microsoft YaHei', 13))
        self.show_answer_btn.clicked.connect(self.on_show_answer)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.show_answer_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.show_answer_btn.setMinimumHeight(70)
        self.review_btns_layout.addWidget(self.show_answer_btn)

        self.mastered_btn = QPushButton('已掌握')
        self.mastered_btn.setFont(QFont('Microsoft YaHei', 13))
        self.mastered_btn.clicked.connect(self.on_mark_mastered)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.mastered_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.mastered_btn.setMinimumHeight(70)
        self.review_btns_layout.addWidget(self.mastered_btn)

        card_layout.addLayout(self.review_btns_layout)

        # 重测阶段控件
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText('请输入你的答案（如：A 或 True 或 填空内容）')
        self.answer_input.setFont(QFont('Microsoft YaHei', 14))
        self.answer_input.setVisible(False)
        self.answer_input.setMinimumHeight(48)
        card_layout.addSpacing(20)
        card_layout.addWidget(self.answer_input)

        # 编程题重测控件（默认隐藏）
        code_label = QLabel('请输入Python代码:')
        code_label.setFont(QFont('Microsoft YaHei', 14))
        code_label.setVisible(False)
        self.code_label = code_label
        card_layout.addWidget(self.code_label)

        from PyQt5.QtWidgets import QTextEdit as _QTextEdit
        self.code_input = _QTextEdit()
        self.code_input.setFont(QFont('Consolas', 12))
        self.code_input.setPlaceholderText('在此输入Python代码...')
        self.code_input.setMinimumHeight(200)
        self.code_input.setStyleSheet('''
            QTextEdit {
                background-color: #263238;
                color: #AAAAAA;
                border: 1px solid #455A64;
                padding: 10px;
            }
        ''')
        self.code_input.setVisible(False)
        card_layout.addWidget(self.code_input)

        self.run_code_btn = QPushButton('▶️ 运行代码')
        self.run_code_btn.setFont(QFont('Microsoft YaHei', 12))
        self.run_code_btn.clicked.connect(self.run_code_retest)
        self.run_code_btn.setVisible(False)
        card_layout.addWidget(self.run_code_btn)

        output_label = QLabel('运行结果:')
        output_label.setFont(QFont('Microsoft YaHei', 12))
        output_label.setVisible(False)
        self.output_label = output_label
        card_layout.addWidget(self.output_label)

        self.code_output = _QTextEdit()
        self.code_output.setFont(QFont('Consolas', 11))
        self.code_output.setReadOnly(True)
        self.code_output.setMaximumHeight(150)
        self.code_output.setVisible(False)
        card_layout.addWidget(self.code_output)

        # 统一隐藏编程题控件的便捷方法
        def _hide_code_controls():
            for w in (self.code_label, self.code_input, self.run_code_btn, self.output_label, self.code_output):
                w.setVisible(False)
            self.code_input.clear()
            self.code_output.clear()

        self.hide_code_controls = _hide_code_controls

        self.retest_btns_layout = QHBoxLayout()
        self.retest_btns_layout.setSpacing(12)
        self.retest_btns_layout.setContentsMargins(0, 12, 0, 12)
        
        self.submit_answer_btn = QPushButton('提交')
        self.submit_answer_btn.setVisible(False)
        self.submit_answer_btn.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        self.submit_answer_btn.clicked.connect(self.on_submit_retest_answer)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.submit_answer_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.submit_answer_btn.setMinimumHeight(70)
        self.submit_answer_btn.setMinimumWidth(160)
        self.retest_btns_layout.addWidget(self.submit_answer_btn)

        self.next_retest_btn = QPushButton('下一题')
        self.next_retest_btn.setVisible(False)
        self.next_retest_btn.setFont(QFont('Microsoft YaHei', 13))
        self.next_retest_btn.clicked.connect(self.on_next_retest)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            self.next_retest_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass
        self.next_retest_btn.setMinimumHeight(70)
        self.next_retest_btn.setMinimumWidth(160)
        self.retest_btns_layout.addWidget(self.next_retest_btn)
        card_layout.addLayout(self.retest_btns_layout)

        self.card_group.setLayout(card_layout)
        self.card_group.setVisible(False)
        left_layout.addWidget(self.card_group)

        self.body_splitter.addWidget(self.left_frame)

        # 右侧：按知识点分组 + 滚动
        self.right_frame = QFrame()
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        groups_group = QGroupBox('知识点分组（点击查看该组错题）')
        groups_group.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        groups_group.setStyleSheet('QGroupBox { padding-top: 22px; margin-top: 8px; } QGroupBox::title { left: 10px; }')
        g_layout = QVBoxLayout()

        # 右侧顶部操作区：返回分组 + 当前选择
        top_bar = QHBoxLayout()
        self.back_to_groups_btn = QPushButton('返回分组')
        self.back_to_groups_btn.setVisible(False)
        self.back_to_groups_btn.clicked.connect(self.back_to_groups)
        top_bar.addWidget(self.back_to_groups_btn)

        self.right_title_label = QLabel('')
        top_bar.addWidget(self.right_title_label)
        top_bar.addStretch()
        g_layout.addLayout(top_bar)

        self.groups_scroll = QScrollArea()
        self.groups_scroll.setWidgetResizable(True)
        self.groups_container = QWidget()
        self.groups_container_layout = QVBoxLayout(self.groups_container)
        self.groups_container_layout.setContentsMargins(10, 10, 10, 10)
        self.groups_container_layout.setSpacing(10)
        self.groups_scroll.setWidget(self.groups_container)
        g_layout.addWidget(self.groups_scroll)

        # 当前分组的错题预览列表
        self.group_list = QListWidget()
        self.group_list.setFont(QFont('Microsoft YaHei', 12))
        self.group_list.setSpacing(3)
        self.group_list.setStyleSheet('QListWidget::item { padding: 8px; }')
        self.group_list.setVisible(False)
        g_layout.addWidget(self.group_list)

        groups_group.setLayout(g_layout)
        right_layout.addWidget(groups_group)

        self.body_splitter.addWidget(self.right_frame)
        self.body_splitter.setStretchFactor(0, 1)
        self.body_splitter.setStretchFactor(1, 3)
        try:
            # 初始化时左栏稍窄一些
            self.body_splitter.setSizes([360, 840])
        except Exception:
            pass

        main_layout.addWidget(self.body_splitter)

        self.setLayout(main_layout)
        
        # 运行期状态
        self.selected_category = None
        self.review_queue = []
        self.current_index = 0
        self.mastered_for_retest = []
        self.in_retest = False
        self.review_mode = False

    def load_data(self):
        """加载错题数据"""
        wrong_questions = DataLoader.load_user_wrong_questions(self.current_user.id)

        # 保存数据引用
        self.wrong_questions_data = wrong_questions

        # 构建分组（按分类作为知识点分组），并按错题数降序显示
        self.populate_category_groups()

    def populate_category_groups(self):
        """填充分组滚动区与预览列表"""
        # 清空容器
        while self.groups_container_layout.count():
            item = self.groups_container_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # 汇总所有分类（来自所有题目，保证“都显示”）
        all_questions = DataLoader.load_all_questions()
        all_categories = sorted({q.category or '未分类' for q in all_questions})

        # 错题计数
        wrong_counts = {}
        for wq in getattr(self, 'wrong_questions_data', []):
            cat = wq.get('category') or '未分类'
            wrong_counts[cat] = wrong_counts.get(cat, 0) + 1

        # 排序：先按错题数降序，再按名称
        sorted_categories = sorted(all_categories, key=lambda c: (-wrong_counts.get(c, 0), c))

        # “全部”卡片
        total_wrong = len(getattr(self, 'wrong_questions_data', []))
        self.groups_container_layout.addWidget(self._create_category_card('全部', total_wrong, None))

        # 分类卡片（竖向大块，可滚动）
        for cat in sorted_categories:
            cnt = wrong_counts.get(cat, 0)
            self.groups_container_layout.addWidget(self._create_category_card(cat, cnt, cat))

        self.groups_container_layout.addStretch()
        # 初始隐藏预览列表
        self.group_list.clear()
        self.group_list.setVisible(False)

    def _create_category_card(self, title, count, category_key):
        """创建竖向卡片按钮，显示名称与错题数并可进入该组"""
        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 12px 14px;
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 12px;
                background-color: rgba(255,255,255,0.9);
                min-height: 68px;
            }
            QPushButton:hover { background-color: rgba(0,0,0,0.03); }
            """
        )
        # 富文本：标题 + 计数
        color_count = THEME_COLORS.get('primary', '#2d8cf0')
        btn.setText(f"{title}    错题数：{count}")
        btn.clicked.connect(lambda: self._on_category_card_clicked(category_key))

        # 右键直接开始复习该组（默认数量）
        def context_menu(event):
            if event.button() == 2:  # Right button
                self.selected_category = category_key
                self.start_review()
            else:
                QPushButton.mousePressEvent(btn, event)
        btn.mousePressEvent = context_menu
        return btn

    def _on_category_card_clicked(self, category):
        self.select_category(category)

    def select_category(self, category):
        """选择分组并显示该组错题预览"""
        self.selected_category = category
        text = category if category else '全部'
        self.selected_category_label.setText(f'当前知识点：{text}')

        # 切换右栏为列表视图
        self.groups_scroll.setVisible(False)
        self.right_title_label.setText(f'当前：{text}')
        self.back_to_groups_btn.setVisible(True)

        # 更新预览列表
        self.group_list.clear()
        filtered = [wq for wq in self.wrong_questions_data if (not category or wq.get('category') == category)]
        for idx, wq in enumerate(filtered):
            short = wq.get('question', '')
            if len(short) > 60:
                short = short[:60] + '...'
            item = QListWidgetItem(f'[{QUESTION_TYPES.get(wq.get("type"), wq.get("type",""))}] {short}')
            item.setData(Qt.UserRole, wq)
            self.group_list.addItem(item)
        self.group_list.setVisible(True)

        # 双击预览项目查看详情
        try:
            self.group_list.itemDoubleClicked.disconnect()
        except Exception:
            pass
        self.group_list.itemDoubleClicked.connect(self.open_preview_item)

    def back_to_groups(self):
        """返回分组视图"""
        self.group_list.setVisible(False)
        self.back_to_groups_btn.setVisible(False)
        self.right_title_label.setText('')
        self.groups_scroll.setVisible(True)

    def open_preview_item(self, item):
        """双击预览项，打开详情对话框"""
        wq = item.data(Qt.UserRole)
        if wq:
            self.view_question_detail(wq)

    def view_question_detail(self, wq):
        """查看题目详情"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle('错题详情')
        dialog.setMinimumSize(1100, 850)
        try:
            dialog.resize(1100, 850)
        except Exception:
            pass

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 题目信息
        info_text = f'''
题型: {QUESTION_TYPES.get(wq.get('type', ''), wq.get('type', ''))}
分类: {wq.get('category', '')}
错误次数: {wq.get('wrong_count', 0)}
        '''
        info_label = QLabel(info_text)
        info_label.setFont(QFont('Microsoft YaHei', 12))
        try:
            info_label.setWordWrap(True)
        except Exception:
            pass
        layout.addWidget(info_label)

        # 题目内容
        question_group = QGroupBox('题目')
        question_group.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        question_group.setStyleSheet('QGroupBox { padding-top: 24px; } QGroupBox::title { left: 10px; top: 4px; }')
        question_layout = QVBoxLayout()
        question_layout.setContentsMargins(10, 20, 10, 12)
        question_text = QTextEdit()
        question_text.setFont(QFont('Microsoft YaHei', 13))
        question_text.setReadOnly(True)
        question_text.setPlainText(wq.get('question', ''))
        question_text.setMinimumHeight(200)
        question_layout.addWidget(question_text)
        question_group.setLayout(question_layout)
        layout.addWidget(question_group)

        # 选项（如果有）
        options = wq.get('options')
        if options:
            try:
                import json
                if isinstance(options, str):
                    options_list = json.loads(options)
                else:
                    options_list = options

                options_group = QGroupBox('选项')
                options_group.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
                options_group.setStyleSheet('QGroupBox { padding-top: 24px; } QGroupBox::title { left: 10px; top: 4px; }')
                options_layout = QVBoxLayout()
                options_layout.setContentsMargins(10, 20, 10, 12)
                options_text = QTextEdit()
                options_text.setFont(QFont('Microsoft YaHei', 13))
                options_text.setReadOnly(True)
                options_text.setPlainText('\n'.join(options_list))
                options_text.setMinimumHeight(140)
                options_layout.addWidget(options_text)
                options_group.setLayout(options_layout)
                layout.addWidget(options_group)
            except:
                pass

        # 正确答案
        answer_group = QGroupBox('正确答案')
        answer_group.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        answer_group.setStyleSheet('QGroupBox { padding-top: 24px; } QGroupBox::title { left: 10px; top: 4px; }')
        answer_layout = QVBoxLayout()
        answer_layout.setContentsMargins(10, 20, 10, 12)
        answer_label = QLabel(wq.get('answer', ''))
        answer_label.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        answer_label.setStyleSheet(f'color: {THEME_COLORS["success"]}; padding: 10px;')
        try:
            answer_label.setWordWrap(True)
        except Exception:
            pass
        answer_layout.addWidget(answer_label)
        answer_group.setLayout(answer_layout)
        layout.addWidget(answer_group)

        # 解析
        explanation = wq.get('explanation', '')
        if explanation:
            explanation_group = QGroupBox('解析')
            explanation_group.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
            explanation_group.setStyleSheet('QGroupBox { padding-top: 24px; } QGroupBox::title { left: 10px; top: 4px; }')
            explanation_layout = QVBoxLayout()
            explanation_layout.setContentsMargins(10, 20, 10, 12)
            explanation_text = QTextEdit()
            explanation_text.setFont(QFont('Microsoft YaHei', 13))
            explanation_text.setReadOnly(True)
            explanation_text.setPlainText(explanation)
            explanation_text.setMinimumHeight(160)
            explanation_layout.addWidget(explanation_text)
            explanation_group.setLayout(explanation_layout)
            layout.addWidget(explanation_group)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.button(QDialogButtonBox.Ok).setFont(QFont('Microsoft YaHei', 12))
        button_box.button(QDialogButtonBox.Ok).setMinimumHeight(40)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec_()

    def show_count_options(self):
        """点击题数框时，显示上下两块（15/25）——兼容旧入口"""
        self.show_count_options_vertical()

    def show_count_options_vertical(self):
        """将题数选择框纵向拆分，上15/下25（整框或按钮点击触发）"""
        # 隐藏当前显示按钮
        self.review_count_btn.setVisible(False)

        # 创建纵向按钮容器（上下两块）
        options_vlayout = QVBoxLayout()
        options_vlayout.setSpacing(6)

        btn_15 = QPushButton('15')
        btn_15.setFont(QFont('Microsoft YaHei', 13))
        btn_15.setMinimumHeight(40)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            btn_15.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        except Exception:
            pass
        btn_15.clicked.connect(lambda: self.set_count_and_restore(15))
        options_vlayout.addWidget(btn_15)

        btn_25 = QPushButton('25')
        btn_25.setFont(QFont('Microsoft YaHei', 13))
        btn_25.setMinimumHeight(40)
        try:
            from PyQt5.QtWidgets import QSizePolicy
            btn_25.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        except Exception:
            pass
        btn_25.clicked.connect(lambda: self.set_count_and_restore(25))
        options_vlayout.addWidget(btn_25)

        # 使上下两块尽可能均分高度
        options_vlayout.setStretch(0, 1)
        options_vlayout.setStretch(1, 1)

        # 添加到计数框内并保存引用，便于恢复时移除
        self._count_options_item = options_vlayout
        self.count_layout.addLayout(options_vlayout)
    
    def set_count_and_restore(self, count):
        """设置题数并恢复显示"""
        self.review_count = count
        self.review_count_btn.setText(f'{count}题')
        # 恢复按钮显示
        self.review_count_btn.setVisible(True)
        # 移除拆分选项布局（若存在）
        try:
            if hasattr(self, '_count_options_item') and self._count_options_item is not None:
                # 在父布局中查找并移除对应项
                for i in range(self.count_layout.count()):
                    item = self.count_layout.itemAt(i)
                    if item is not None and item.layout() is self._count_options_item:
                        self.count_layout.takeAt(i)
                        # 逐个删除其子控件
                        while self._count_options_item.count():
                            child = self._count_options_item.takeAt(0)
                            if child.widget():
                                child.widget().deleteLater()
                        self._count_options_item = None
                        break
        except Exception:
            self._count_options_item = None


    def start_review(self):
        """开始卡片式复习"""
        # 使用保存的review_count值
        count = self.review_count

        pool = [wq for wq in self.wrong_questions_data if (not self.selected_category or wq.get('category') == self.selected_category)]
        self.review_queue = pool[:count]
        self.current_index = 0
        self.mastered_for_retest = []
        self.mastered_candidates = []
        self.in_retest = False

        if not self.review_queue:
            show_info(self, '提示', '当前分组没有可复习的错题。')
            return

        self.enter_review_mode()
        self.card_group.setVisible(True)
        self.show_current_card()

    def enter_review_mode(self):
        """进入全屏复习模式（隐藏右侧与标题统计，突出卡片）"""
        if self.review_mode:
            return
        self.review_mode = True
        # 记录进入复习前的分栏尺寸
        try:
            self._splitter_saved_sizes = self.body_splitter.sizes()
        except Exception:
            self._splitter_saved_sizes = None
        # 隐藏右侧
        self.right_frame.setVisible(False)
        # 隐藏标题
        self.title_label.setVisible(False)
        # 隐藏设置框
        self.settings_group.setVisible(False)
        # 隐藏设置区的开始复习按钮和题数框
        self.start_review_btn.setVisible(False)
        self.count_frame.setVisible(False)
        # 设置退出复习按钮可见
        self.exit_review_btn.setVisible(True)
        # 显示卡片顶部退出按钮
        self.card_exit_btn.setVisible(True)
        # 显示进度条
        self.review_progress_bar.setVisible(True)
        # 拉伸左侧充满
        self.body_splitter.setSizes([max(sum(self.body_splitter.sizes()), 1), 0])

    def exit_review_mode(self):
        """退出全屏复习模式"""
        if not self.review_mode:
            return
        self.review_mode = False
        self.right_frame.setVisible(True)
        self.title_label.setVisible(True)
        # 显示设置框
        self.settings_group.setVisible(True)
        # 显示开始复习按钮和题数框
        self.start_review_btn.setVisible(True)
        self.count_frame.setVisible(True)
        self.exit_review_btn.setVisible(False)
        # 隐藏卡片顶部退出按钮
        self.card_exit_btn.setVisible(False)
        self.card_group.setVisible(False)
        self.review_progress_bar.setVisible(False)
        # 恢复分栏比例
        self.body_splitter.setStretchFactor(0, 1)
        self.body_splitter.setStretchFactor(1, 2)
        # 恢复进入复习前保存的分栏尺寸
        if self._splitter_saved_sizes and len(self._splitter_saved_sizes) == 2:
            try:
                self.body_splitter.setSizes(self._splitter_saved_sizes)
            except Exception:
                pass
        # 刷新右侧分组列表
        self.populate_category_groups()

    def show_current_card(self):
        """显示当前卡片内容"""
        total = len(self.review_queue)
        cur = min(self.current_index + 1, total) if total > 0 else 0
        self.progress_label.setText(f'进度：{cur}/{total}')
        
        # 更新进度条
        self.review_progress_bar.setMaximum(total)
        self.review_progress_bar.setValue(cur)

        if self.current_index >= total:
            # 队列完成
            self.finish_review()
            return

        wq = self.review_queue[self.current_index]

        # 进入复习模式时，先隐藏编程题控件，避免占据上部空间
        if hasattr(self, 'hide_code_controls'):
            self.hide_code_controls()

        # 填充题干
        self.question_text.setPlainText(wq.get('question', ''))

        # 填充选项（如有）
        options = wq.get('options')
        self.options_text.setVisible(False)
        if options:
            try:
                import json
                opts = json.loads(options) if isinstance(options, str) else options
                self.options_text.setPlainText('\n'.join(opts))
                self.options_text.setVisible(True)
            except Exception:
                self.options_text.setVisible(False)

        # 隐藏答案，显示复习阶段按钮
        self.answer_label.setText(wq.get('answer', ''))
        self.answer_label.setVisible(False)
        self.answer_input.setVisible(False)
        self.submit_answer_btn.setVisible(False)
        self.next_retest_btn.setVisible(False)
        self.show_answer_btn.setVisible(True)
        self.mastered_btn.setVisible(True)
        self.ambiguous_btn.setVisible(True)

    def on_show_answer(self):
        """点击查看答案"""
        self.answer_label.setVisible(True)

    def on_mark_mastered(self):
        """当前题标记为已掌握（本次会话先标记，后续统一重测再决定是否移除）"""
        if self.current_index >= len(self.review_queue):
            return
        wq = self.review_queue[self.current_index]
        # 加入待重测集合
        self.mastered_candidates.append(wq)

        # 从队列中移除当前题，继续下一题
        del self.review_queue[self.current_index]
        # 当前索引不变（因为删除后，下一题正好在该位置）
        self.show_current_card()

    def on_mark_ambiguous(self):
        """当前题标记为模糊（稍后重复出现）"""
        if self.current_index >= len(self.review_queue):
            return
        # 将当前题移到队尾
        wq = self.review_queue[self.current_index]
        del self.review_queue[self.current_index]
        self.review_queue.append(wq)
        # 显示下一题（当前位置现在是下一题）
        self.show_current_card()

    def finish_review(self):
        """复习完成，进入重新测试提示"""
        # 隐藏卡片显示，提示开始重测
        self.card_group.setVisible(False)

        retest_count = len(self.mastered_candidates)
        if retest_count == 0:
            show_info(self, '复习完成', '本次复习已结束。没有标记“已掌握”的题目需要重测。')
            self.exit_review_mode()
            self.refresh()
            return

        reply = ask_question(
            self, '复习完成', f'本次有 {retest_count} 道已掌握题目。是否开始重新测试？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.start_retest()
        else:
            self.exit_review_mode()
            self.refresh()

    def start_retest(self):
        """开始重新测试（对“已掌握”集合再过一遍）"""
        self.in_retest = True
        self.review_queue = list(self.mastered_candidates)
        self.current_index = 0
        # 保持复习卡片不显示“重新测试”字样
        self.card_group.setTitle('')
        self.card_group.setVisible(True)
        self.retest_results = {}
        self.show_current_retest_card()

    def show_current_retest_card(self):
        """显示重测卡片（逻辑同复习，但“模糊”仅回到队尾，不再改库）"""
        total = len(self.review_queue)
        cur = min(self.current_index + 1, total) if total > 0 else 0
        self.progress_label.setText(f'进度：{cur}/{total}')

        if self.current_index >= total:
            # 重测结束：将回答正确的题移出错题本
            correct_ids = [qid for qid, ok in self.retest_results.items() if ok]
            removed = 0
            if correct_ids:
                try:
                    db_manager.connect()
                    for qid in correct_ids:
                        update_query = """
                            UPDATE wrong_questions
                            SET mastered = 1
                            WHERE user_id = ? AND question_id = ?
                        """
                        db_manager.execute_update(update_query, (self.current_user.id, qid))
                        removed += 1
                finally:
                    db_manager.disconnect()

            show_info(self, '重测完成', f'重新测试完成！本次共移除 {removed} 道错题。')
            self.card_group.setTitle('卡片式复习')
            self.card_group.setVisible(False)
            self.in_retest = False
            self.exit_review_mode()
            self.refresh()
            return

        wq = self.review_queue[self.current_index]
        self.question_text.setPlainText(wq.get('question', ''))

        options = wq.get('options')
        self.options_text.setVisible(False)
        if options:
            try:
                import json
                opts = json.loads(options) if isinstance(options, str) else options
                self.options_text.setPlainText('\n'.join(opts))
                self.options_text.setVisible(True)
            except Exception:
                self.options_text.setVisible(False)

        self.answer_label.setText('')
        self.answer_label.setVisible(False)
        # 切换为重测模式：隐藏复习按钮，显示输入与提交
        self.show_answer_btn.setVisible(False)
        self.mastered_btn.setVisible(False)
        self.ambiguous_btn.setVisible(False)
        self.submit_answer_btn.setVisible(True)
        self.next_retest_btn.setVisible(False)

        # 根据题型显示不同的输入控件
        q_type = wq.get('type')
        if q_type == 'code':
            # 显示代码编辑相关控件
            self.code_label.setVisible(True)
            self.code_input.setVisible(True)
            self.run_code_btn.setVisible(True)
            self.output_label.setVisible(True)
            self.code_output.setVisible(True)
            self.answer_input.setVisible(False)
            self.answer_input.setText('')
            # 清空代码区
            self.code_input.clear()
            self.code_output.clear()
        else:
            # 显示普通输入框
            self.code_label.setVisible(False)
            self.code_input.setVisible(False)
            self.run_code_btn.setVisible(False)
            self.output_label.setVisible(False)
            self.code_output.setVisible(False)
            self.answer_input.setVisible(True)
            self.answer_input.setText('')

    def on_submit_retest_answer(self):
        """提交重测答案并判断对错"""
        if self.current_index >= len(self.review_queue):
            return
        wq = self.review_queue[self.current_index]
        # 根据题型获取用户答案
        if (wq.get('type') == 'code') and self.code_input.isVisible():
            user_ans = self.code_input.toPlainText().strip()
        else:
            user_ans = self.answer_input.text().strip()

        # 构造 Question 校验
        q = Question(
            question_id=wq.get('question_id') or wq.get('id'),
            category=wq.get('category'),
            q_type=wq.get('type'),
            question=wq.get('question'),
            options=wq.get('options'),
            answer=wq.get('answer'),
            explanation=wq.get('explanation')
        )
        is_correct = q.check_answer(user_ans)
        self.retest_results[q.id] = is_correct

        # 显示反馈
        if is_correct:
            self.answer_label.setStyleSheet(f'color: {THEME_COLORS["success"]};')
            self.answer_label.setText('回答正确！')
        else:
            self.answer_label.setStyleSheet(f'color: {THEME_COLORS["danger"]};')
            self.answer_label.setText(f'回答错误，正确答案：{wq.get("answer", "")}')
        self.answer_label.setVisible(True)
        self.next_retest_btn.setVisible(True)
        self.submit_answer_btn.setVisible(False)

    def run_code_retest(self):
        """在重测页面运行代码并显示输出"""
        code = self.code_input.toPlainText().strip()
        if not code:
            self.code_output.setPlainText('请输入代码！')
            return
        # 语法校验
        is_valid, error = self.code_executor.validate_code(code)
        if not is_valid:
            self.code_output.setPlainText(f'❌ 语法错误:\n{error}')
            return
        # 执行代码
        success, output, err = self.code_executor.execute(code)
        if success:
            self.code_output.setPlainText(output if output else '(无输出)')
        else:
            self.code_output.setPlainText(f'❌ 执行错误:\n{err}')

    def on_next_retest(self):
        if self.current_index >= len(self.review_queue):
            return
        self.current_index += 1
        self.show_current_retest_card()

    def on_retest_mastered(self):
        """重测期间，已掌握：跳过此题进入下一题"""
        if self.current_index >= len(self.review_queue):
            return
        del self.review_queue[self.current_index]
        self.show_current_retest_card()

    def on_retest_ambiguous(self):
        """重测期间，模糊：送到队尾"""
        if self.current_index >= len(self.review_queue):
            return
        wq = self.review_queue[self.current_index]
        del self.review_queue[self.current_index]
        self.review_queue.append(wq)
        self.show_current_retest_card()

    def refresh(self):
        """刷新数据"""
        # 重置部分运行期状态
        self.card_group.setVisible(False)
        self.selected_category = None
        self.selected_category_label.setText('当前知识点：全部')
        self.group_list.clear()
        self.group_list.setVisible(False)
        self.load_data()
