# -*- coding: utf-8 -*-
"""
成绩统计模块
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt5.QtGui import QFont
from core.services.data_service import data_service
from ui.styles.theme import COLORS, FONTS, SIZES
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# 配置 matplotlib 中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'PingFang SC']
plt.rcParams['axes.unicode_minus'] = False


class StatisticsWidget(QWidget):
    """成绩统计界面"""

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("📈 成绩统计分析")
        title.setFont(QFont(*FONTS['heading']))
        title.setStyleSheet(f"color: {COLORS['primary']}; background: transparent;")
        layout.addWidget(title)

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(16)

        # 饼图
        pie_frame = QFrame()
        pie_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        pie_layout = QVBoxLayout(pie_frame)
        pie_layout.setContentsMargins(16, 16, 16, 16)

        pie_title = QLabel("各分类准确率")
        pie_title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        pie_title.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        pie_layout.addWidget(pie_title)

        self.pie_figure = Figure(figsize=(5, 4), dpi=100)
        self.pie_figure.patch.set_facecolor('none')
        self.pie_canvas = FigureCanvas(self.pie_figure)
        pie_layout.addWidget(self.pie_canvas)

        charts_layout.addWidget(pie_frame)

        # 柱状图
        bar_frame = QFrame()
        bar_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        bar_layout = QVBoxLayout(bar_frame)
        bar_layout.setContentsMargins(16, 16, 16, 16)

        bar_title = QLabel("题型练习分布")
        bar_title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        bar_title.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        bar_layout.addWidget(bar_title)

        self.bar_figure = Figure(figsize=(5, 4), dpi=100)
        self.bar_figure.patch.set_facecolor('none')
        self.bar_canvas = FigureCanvas(self.bar_figure)
        bar_layout.addWidget(self.bar_canvas)

        charts_layout.addWidget(bar_frame)

        layout.addLayout(charts_layout, 1)

    def refresh(self):
        self._update_pie_chart()
        self._update_bar_chart()

    def _update_pie_chart(self):
        stats = data_service.get_category_statistics(self.current_user.id)
        categories = [s['category'] for s in stats if s['accuracy'] is not None and s['accuracy'] > 0]
        accuracies = [s['accuracy'] for s in stats if s['accuracy'] is not None and s['accuracy'] > 0]

        self.pie_figure.clear()
        ax = self.pie_figure.add_subplot(111)

        if categories:
            colors = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#06B6D4',
                     '#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#6366F1']
            # 自定义标签显示准确率值
            def make_label(pct, values):
                absolute = int(round(pct * sum(values) / 100.0))
                return f'{absolute}%'

            wedges, texts, autotexts = ax.pie(
                accuracies,
                labels=categories,
                autopct=lambda pct: f'{pct:.1f}%',
                colors=colors[:len(categories)],
                startangle=90
            )
            # 设置标签字体大小
            for text in texts:
                text.set_fontsize(12)
            for autotext in autotexts:
                autotext.set_fontsize(11)
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            ax.set_title('各分类准确率分布', fontsize=16, fontweight='bold')
        else:
            ax.text(0.5, 0.5, '暂无数据\n请先完成一些练习', ha='center', va='center', fontsize=16, color='#94A3B8')
            ax.set_title('各分类准确率分布', fontsize=16, fontweight='bold')

        self.pie_canvas.draw()

    def _update_bar_chart(self):
        from core.database.sqlite_manager import db
        from config import config

        # 单次查询获取所有题型的练习次数
        results = db.execute(
            """SELECT q.type, COUNT(*) as count FROM practice_records pr
            JOIN questions q ON pr.question_id = q.id
            WHERE pr.user_id = ?
            GROUP BY q.type""",
            (self.current_user.id,)
        )

        # 构建类型映射
        type_map = {r['type']: r['count'] for r in results}
        question_types = config.knowledge.question_types

        types = []
        counts = []
        for q_type, type_name in question_types.items():
            count = type_map.get(q_type, 0)
            if count > 0:
                types.append(type_name)
                counts.append(count)

        self.bar_figure.clear()
        ax = self.bar_figure.add_subplot(111)

        if types:
            colors = ['#2563EB', '#10B981', '#F59E0B', '#EF4444']
            bars = ax.bar(types, counts, color=colors[:len(types)], alpha=0.8)
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom', fontsize=10)
            ax.set_ylabel('练习数量')
            ax.set_title('题型练习分布', fontsize=12, fontweight='bold')
        else:
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=14)
            ax.set_title('题型练习分布', fontsize=12, fontweight='bold')

        self.bar_canvas.draw()
