# -*- coding: utf-8 -*-
"""
个人主页模块
包含用户信息、头像更换、背景选择和最近学习记录
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QApplication, QInputDialog, QLineEdit
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from utils.data_loader import DataLoader
from database.db_manager import db_manager
from ui.styles.message_box import show_info, show_warning, show_error, ask_question
from config import THEME_COLORS


class ProfileWidget(QWidget):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.avatar_path = None
        self.bg_path = None
        self.init_ui()
        self.load_recent_records()
        self.load_my_stats()  # 加载统计数据

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 顶部信息卡片（头像居中）
        info_group = QGroupBox()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(16, 36, 16, 16)  # 顶部更大留白，头像整体下移
        info_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        # 头像（放大并可点击更换，圆形裁剪）
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(180, 180)
        self.avatar_label.setStyleSheet('border-radius:90px; background-color: #EFEFEF; border: none;')
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setScaledContents(True)
        self.avatar_label.mousePressEvent = lambda event: self.change_avatar()
        # 投影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.black)
        self.avatar_label.setGraphicsEffect(shadow)
        self.set_default_avatar()
        info_layout.addWidget(self.avatar_label, alignment=Qt.AlignHCenter)

        name_label = QLabel(self.current_user.nickname)
        name_label.setFont(QFont('SF Pro Display', 18, QFont.Bold))
        name_label.setAlignment(Qt.AlignHCenter)
        info_layout.addWidget(name_label)

        # 个人信息下方保留一定留白
        info_layout.addSpacing(8)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # 我的数据
        stats_group = QGroupBox('我的数据')
        stats_group.setStyleSheet('QGroupBox { padding-top: 20px; margin-top: 10px; }')
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(12, 12, 12, 12)
        stats_layout.setSpacing(12)

        self.stat_wrong = self.create_stat_badge('错题数', '0', THEME_COLORS['danger'])
        self.stat_review = self.create_stat_badge('巩固量', '0', THEME_COLORS['success'])
        self.stat_total_time = self.create_stat_badge('累计时长', '0 分钟', THEME_COLORS['primary'])
        self.stat_today_time = self.create_stat_badge('今日时长', '0 分钟', THEME_COLORS['warning'])

        stats_layout.addWidget(self.stat_wrong)
        stats_layout.addWidget(self.stat_review)
        stats_layout.addWidget(self.stat_total_time)
        stats_layout.addWidget(self.stat_today_time)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # 外观设置（背景 + 字体）
        appearance_group = QGroupBox('外观设置')
        appearance_group.setStyleSheet('QGroupBox { padding-top: 20px; margin-top: 10px; }')
        appearance_layout = QVBoxLayout()
        appearance_layout.setContentsMargins(12, 12, 12, 12)
        appearance_layout.setSpacing(10)
        appearance_layout.setAlignment(Qt.AlignTop)

        # 背景
        bg_row1 = QHBoxLayout()
        upload_bg_btn = QPushButton('上传背景图片')
        upload_bg_btn.setEnabled(False)  # 功能已禁用
        upload_bg_btn.setToolTip("壁纸功能暂时禁用")
        upload_bg_btn.clicked.connect(self.change_background)
        bg_row1.addWidget(upload_bg_btn)
        bg_row1.addStretch()
        appearance_layout.addLayout(bg_row1)

        bg_row2 = QHBoxLayout()
        color_label = QLabel('纯色：')
        self.bg_color_combo = QComboBox()
        self.bg_color_combo.addItems(['黑色', '白色', '灰色'])
        apply_color_btn = QPushButton('应用纯色背景')
        apply_color_btn.setEnabled(False)  # 功能已禁用
        apply_color_btn.setToolTip("壁纸功能暂时禁用")
        apply_color_btn.clicked.connect(self.apply_selected_color)
        reset_btn = QPushButton('恢复默认背景')
        reset_btn.setEnabled(False)  # 功能已禁用
        reset_btn.setToolTip("壁纸功能暂时禁用")
        reset_btn.clicked.connect(self.reset_background)
        bg_row2.addWidget(color_label)
        bg_row2.addWidget(self.bg_color_combo, 1)
        bg_row2.addWidget(apply_color_btn)
        bg_row2.addWidget(reset_btn)
        appearance_layout.addLayout(bg_row2)

        # 字体大小
        font_row = QHBoxLayout()
        font_row.setSpacing(8)
        font_label = QLabel('字体大小：')
        self.font_combo = QComboBox()
        self.font_combo.addItems(['小(90%)', '默认(100%)', '大(110%)', '特大(125%)'])
        self.font_combo.setCurrentIndex(1)
        apply_font_btn = QPushButton('应用字体')
        apply_font_btn.clicked.connect(self.apply_selected_font_scale)
        font_row.addWidget(font_label)
        font_row.addWidget(self.font_combo, 1)
        font_row.addWidget(apply_font_btn)
        appearance_layout.addLayout(font_row)

        appearance_group.setLayout(appearance_layout)
        main_layout.addWidget(appearance_group)

        # 系统设置（数据库重置）
        system_group = QGroupBox('系统设置')
        system_group.setStyleSheet('QGroupBox { padding-top: 20px; margin-top: 10px; }')
        system_layout = QVBoxLayout()
        system_layout.setContentsMargins(12, 12, 12, 12)
        system_layout.setSpacing(10)

        reset_db_row = QHBoxLayout()
        reset_db_label = QLabel('重置学习记录：清空所有个人数据，保留题库和考试（不可恢复）')
        reset_db_label.setStyleSheet(f'color: {THEME_COLORS["danger"]};')
        reset_db_btn = QPushButton('🗑️ 重置学习记录')
        reset_db_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: {THEME_COLORS["danger"]};
                color: white;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #dc3545;
            }}
        ''')
        reset_db_btn.clicked.connect(self.reset_database)
        reset_db_row.addWidget(reset_db_label)
        reset_db_row.addStretch()
        reset_db_row.addWidget(reset_db_btn)
        system_layout.addLayout(reset_db_row)

        system_group.setLayout(system_layout)
        main_layout.addWidget(system_group)

        self.setLayout(main_layout)

    def set_default_avatar(self):
        size = self.avatar_label.width()
        pix = QPixmap(size, size)
        pix.fill(Qt.lightGray)
        # 创建圆形掩码
        from PyQt5.QtGui import QPainter, QBrush
        mask = QPixmap(size, size)
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawEllipse(0, 0, size, size)
        painter.end()
        pix.setMask(mask.createMaskFromColor(Qt.transparent))
        self.avatar_label.setPixmap(pix)

    def change_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择头像', '', 'Images (*.png *.jpg *.jpeg)')
        if path:
            size = self.avatar_label.width()
            # 加载并裁剪为正方形
            source_pix = QPixmap(path)
            side = min(source_pix.width(), source_pix.height())
            x = (source_pix.width() - side) // 2
            y = (source_pix.height() - side) // 2
            cropped = source_pix.copy(x, y, side, side)
            pix = cropped.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 创建圆形掩码
            from PyQt5.QtGui import QPainter, QBrush
            mask = QPixmap(size, size)
            mask.fill(Qt.transparent)
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(Qt.white)
            painter.drawEllipse(0, 0, size, size)
            painter.end()
            pix.setMask(mask.createMaskFromColor(Qt.transparent))
            
            self.avatar_label.setPixmap(pix)
            self.avatar_path = path
            # 持久化头像路径到数据库
            try:
                db_manager.connect()
                db_manager.execute_update('UPDATE users SET avatar_path = ? WHERE id = ?', (path, self.current_user.id))
            finally:
                db_manager.disconnect()

    def change_background(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择背景图片', '', 'Images (*.png *.jpg *.jpeg)')
        if path:
            # 简单存储路径即可，主窗口可使用该路径设置背景
            self.bg_path = path
            self.save_background_pref(path)
            self.apply_background_to_main(path)

    def apply_selected_color(self):
        color_map = {
            '黑色': '#000000',
            '白色': '#FFFFFF',
            '灰色': '#888888'
        }
        choice = self.bg_color_combo.currentText()
        color_value = color_map.get(choice, '#FFFFFF')
        pref = f'color:{color_value}'
        self.save_background_pref(pref)
        self.apply_background_to_main(pref)

    def reset_background(self):
        default_color = THEME_COLORS.get('background', '#F6F7F9')
        pref = f'color:{default_color}'
        self.save_background_pref(pref)
        self.apply_background_to_main(pref)

    def save_background_pref(self, value):
        try:
            db_manager.connect()
            db_manager.execute_update('UPDATE users SET bg_path = ? WHERE id = ?', (value, self.current_user.id))
        finally:
            db_manager.disconnect()

    def apply_background_to_main(self, value):
        main_window = self.window()
        if main_window and hasattr(main_window, 'apply_background_theme'):
            main_window.apply_background_theme(value)

    def load_recent_records(self):
        # 安全检查：如果表格不存在则直接返回
        if not hasattr(self, "recent_table"):
            return

        self.recent_table.setRowCount(0)
        records = DataLoader.load_user_learning_records(self.current_user.id)
        for i, record in enumerate(records[:50]):
            self.recent_table.insertRow(i)
            self.recent_table.setItem(i, 0, QTableWidgetItem(record.get('title', '')))
            self.recent_table.setItem(i, 1, QTableWidgetItem(record.get('category', '')))
            study_time = record.get('study_time', 0)
            minutes = study_time // 60
            seconds = study_time % 60
            self.recent_table.setItem(i, 2, QTableWidgetItem(f'{minutes}分{seconds}秒'))
            last = record.get('last_study_at', '')
            self.recent_table.setItem(i, 3, QTableWidgetItem(str(last)[:19] if last else ''))

    def refresh(self):
        self.load_recent_records()
        self.load_my_stats()

    # ---- 自定义方法 ----
    def create_stat_badge(self, title, value, color):
        box = QGroupBox()
        box.setStyleSheet(f'''QGroupBox {{ background-color: rgba(255,255,255,0.86); border: 1px solid rgba(0,0,0,0.06); border-radius: 10px; padding: 12px; }}''')
        lay = QVBoxLayout(); lay.setContentsMargins(10,10,10,10)
        t = QLabel(title); t.setFont(QFont('Microsoft YaHei', 12)); t.setStyleSheet(f'color:{color}; font-weight:600;')
        v = QLabel(value); v.setFont(QFont('Microsoft YaHei', 22, QFont.Bold)); v.setStyleSheet(f'color:{color};')
        v.setAlignment(Qt.AlignCenter)
        lay.addWidget(t)
        lay.addWidget(v)
        box.setLayout(lay)
        # 存储value label引用，便于更新
        box.value_label = v
        return box

    def load_my_stats(self):
        # 错题数
        wrong_list = DataLoader.load_user_wrong_questions(self.current_user.id)
        self.stat_wrong.value_label.setText(str(len(wrong_list)))

        # 巩固量：使用已完成知识点数量
        stats = DataLoader.get_user_statistics(self.current_user.id)
        self.stat_review.value_label.setText(str(stats.get('completed_knowledge', 0)))

        # 累计时长
        total_secs = int(stats.get('total_study_time', 0))
        self.stat_total_time.value_label.setText(self.format_minutes(total_secs))

        # 今日时长
        today_secs = self.query_today_study_seconds()
        self.stat_today_time.value_label.setText(self.format_minutes(today_secs))

    def query_today_study_seconds(self):
        try:
            db_manager.connect()
            sql = """
                SELECT COALESCE(SUM(study_time),0) AS s
                FROM learning_records
                WHERE user_id = ? AND date(last_study_at) = date('now','localtime')
            """
            rows = db_manager.execute_query(sql, (self.current_user.id,))
            return int(dict(rows[0])['s']) if rows else 0
        except Exception:
            return 0
        finally:
            db_manager.disconnect()

    def format_minutes(self, seconds):
        m = seconds // 60
        h = m // 60
        m = m % 60
        if h > 0:
            return f"{h} 小时 {m} 分钟"
        return f"{m} 分钟"

    def apply_selected_font_scale(self):
        sel = self.font_combo.currentText()
        scale = 1.0
        if '90%' in sel:
            scale = 0.9
        elif '110%' in sel:
            scale = 1.1
        elif '125%' in sel:
            scale = 1.25
        app = QApplication.instance()
        if app is not None:
            f = app.font()
            ps = f.pointSizeF()
            if ps > 0:
                f.setPointSizeF(ps * scale)
            else:
                f.setPointSize(int(12 * scale))
            app.setFont(f)

    def reset_database(self):
        """重置学习记录：清空所有个人学习数据，保留题库和考试"""
        # 第一次确认
        reply1 = show_warning(
            self,
            '⚠️ 危险操作',
            '您确定要重置学习记录吗？\n\n'
            '此操作将：\n'
            '• 清空所有学习记录\n'
            '• 清空所有练习记录\n'
            '• 清空所有错题记录\n'
            '• 清空所有考试记录\n'
            '• 回到初始状态（题库和考试保留）\n\n'
            '⚠️ 此操作不可恢复！'
        )

        if not reply1:
            return

        # 第二次确认（要求输入确认文字）
        text, ok = QInputDialog.getText(
            self,
            '最终确认',
            '请输入 "确认重置" 来执行此操作：',
            QLineEdit.Normal,
            ''
        )

        if not ok or text.strip() != '确认重置':
            show_info(self, '已取消', '学习记录重置操作已取消。')
            return

        # 执行重置
        try:
            # 只清空用户相关的记录表，保留题库、知识点、考试等数据
            db_manager.connect()

            # 1. 先删除答题详情（有外键约束，需要先删除）
            db_manager.execute_update('''
                DELETE FROM exam_answers
                WHERE exam_record_id IN (
                    SELECT id FROM exam_records WHERE user_id = ?
                )
            ''', (self.current_user.id,))

            # 2. 清空考试记录
            db_manager.execute_update('DELETE FROM exam_records WHERE user_id = ?', (self.current_user.id,))

            # 3. 清空学习记录
            db_manager.execute_update('DELETE FROM learning_records WHERE user_id = ?', (self.current_user.id,))

            # 4. 清空练习记录
            db_manager.execute_update('DELETE FROM practice_records WHERE user_id = ?', (self.current_user.id,))

            # 5. 清空错题本
            db_manager.execute_update('DELETE FROM wrong_questions WHERE user_id = ?', (self.current_user.id,))

            # 6. 清空学习统计
            db_manager.execute_update('DELETE FROM study_statistics WHERE user_id = ?', (self.current_user.id,))

            db_manager.disconnect()

            show_info(
                self,
                '✅ 重置成功',
                '学习记录已成功清空！\n\n'
                '题库、知识点和考试已保留。\n'
                '程序将在3秒后自动退出，请重新启动程序。'
            )

            # 延迟退出程序
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(3000, lambda: QApplication.instance().quit())

        except Exception as e:
            show_error(
                self,
                '❌ 重置失败',
                f'学习记录重置失败：\n\n{str(e)}\n\n'
                '请检查错误信息或联系管理员。'
            )
            db_manager.disconnect()
