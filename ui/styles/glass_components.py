# -*- coding: utf-8 -*-
"""
PyStudyAssist 玻璃拟态组件库
提供可复用的 Glassmorphism 风格组件
"""
from PyQt5.QtWidgets import (
    QFrame, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QRadioButton, QProgressBar,
    QLabel, QWidget, QGraphicsDropShadowEffect,
    QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QColor, QFont, QPainter, QLinearGradient, QBrush
from ui.styles.theme import COLORS, SIZES, FONTS


class GradientBackground(QWidget):
    """渐变背景组件"""

    def __init__(self, parent=None, start_color=None, end_color=None):
        super().__init__(parent)
        self.start_color = QColor(start_color or COLORS['gradient_start'])
        self.end_color = QColor(end_color or COLORS['gradient_end'])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.start_color)
        gradient.setColorAt(1, self.end_color)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


class GlassCard(QFrame):
    """玻璃卡片组件"""

    def __init__(self, parent=None, title=None):
        super().__init__(parent)
        self._setup_style()
        if title:
            self._add_title(title)

    def _setup_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
            }}
        """)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

    def _add_title(self, title):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)

        title_label = QLabel(title)
        title_label.setFont(QFont(*FONTS['subheading']))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title_label)


class GlassButton(QPushButton):
    """玻璃按钮组件"""

    def __init__(self, text, parent=None, variant='default', icon=None):
        super().__init__(text, parent)
        self.variant = variant
        self._setup_style()
        if icon:
            self.setIcon(icon)

    def _setup_style(self):
        if self.variant == 'primary':
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                    border: none;
                    border-radius: {SIZES['border_radius']}px;
                    color: {COLORS['text_white']};
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 600;
                    min-height: {SIZES['button_height_small']}px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['primary']});
                }}
                QPushButton:pressed {{
                    background: {COLORS['primary_dark']};
                }}
                QPushButton:disabled {{
                    background: {COLORS['border']};
                    color: {COLORS['text_hint']};
                }}
            """)
        elif self.variant == 'danger':
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['danger']}, stop:1 #F87171);
                    border: none;
                    border-radius: {SIZES['border_radius']}px;
                    color: {COLORS['text_white']};
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 600;
                    min-height: {SIZES['button_height_small']}px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #DC2626, stop:1 {COLORS['danger']});
                }}
            """)
        elif self.variant == 'ghost':
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {COLORS['border']};
                    border-radius: {SIZES['border_radius']}px;
                    color: {COLORS['text_secondary']};
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 500;
                    min-height: {SIZES['button_height_small']}px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_alpha_hover']};
                    border-color: {COLORS['primary_light']};
                    color: {COLORS['primary']};
                }}
            """)
        else:  # default
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['glass_bg']};
                    border: 1px solid {COLORS['border']};
                    border-radius: {SIZES['border_radius']}px;
                    color: {COLORS['text_primary']};
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 500;
                    min-height: {SIZES['button_height_small']}px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_alpha_hover']};
                    border-color: {COLORS['primary_light']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['primary_alpha']};
                }}
            """)


class GlassInput(QLineEdit):
    """玻璃输入框组件"""

    def __init__(self, parent=None, placeholder=''):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 10px 14px;
                font-size: 14px;
                color: {COLORS['text_primary']};
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['glass_bg_solid']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_hint']};
            }}
        """)


class GlassTextEdit(QTextEdit):
    """玻璃文本框组件"""

    def __init__(self, parent=None, placeholder=''):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 10px 14px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
            QTextEdit:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['glass_bg_solid']};
            }}
        """)


class GlassComboBox(QComboBox):
    """玻璃下拉框组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 8px 12px;
                font-size: 14px;
                color: {COLORS['text_primary']};
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['primary_light']};
            }}
            QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLORS['text_secondary']};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['glass_bg_solid']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 4px;
                selection-background-color: {COLORS['primary_alpha']};
                selection-color: {COLORS['primary']};
            }}
        """)


class GlassCheckBox(QCheckBox):
    """玻璃复选框组件"""

    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QCheckBox {{
                spacing: 8px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {COLORS['border']};
                border-radius: 4px;
                background-color: {COLORS['glass_bg_solid']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS['primary_light']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
        """)


class GlassRadioButton(QRadioButton):
    """玻璃单选按钮组件"""

    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QRadioButton {{
                spacing: 8px;
                font-size: 14px;
                color: {COLORS['text_primary']};
                padding: 8px;
                border-radius: {SIZES['border_radius_small']}px;
            }}
            QRadioButton:hover {{
                background-color: {COLORS['primary_alpha_hover']};
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {COLORS['border']};
                border-radius: 9px;
                background-color: {COLORS['glass_bg_solid']};
            }}
            QRadioButton::indicator:hover {{
                border-color: {COLORS['primary_light']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
        """)


class GlassProgressBar(QProgressBar):
    """玻璃进度条组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(0, 0, 0, 0.06);
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                font-size: 0px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                border-radius: 4px;
            }}
        """)


class SectionTitle(QLabel):
    """段落标题组件"""

    def __init__(self, text, parent=None, level=1):
        super().__init__(text, parent)
        if level == 1:
            self.setFont(QFont(*FONTS['heading']))
            self.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        elif level == 2:
            self.setFont(QFont(*FONTS['subheading']))
            self.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        else:
            self.setFont(QFont(*FONTS['body_bold']))
            self.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")


class BodyText(QLabel):
    """正文文本组件"""

    def __init__(self, text='', parent=None, hint=False):
        super().__init__(text, parent)
        self.setFont(QFont(*FONTS['body']))
        color = COLORS['text_hint'] if hint else COLORS['text_secondary']
        self.setStyleSheet(f"color: {color}; background: transparent;")
        self.setWordWrap(True)


class StatCard(QFrame):
    """统计卡片组件"""

    def __init__(self, title, value, color=None, parent=None):
        super().__init__(parent)
        self.color = color or COLORS['primary']
        self._setup_ui(title, value)

    def _setup_ui(self, title, value):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius_large']}px;
                border-left: 4px solid {self.color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont(*FONTS['caption']))
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(title_label)

        # 数值
        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont(*FONTS['title']))
        self.value_label.setStyleSheet(f"color: {self.color}; background: transparent;")
        layout.addWidget(self.value_label)

        layout.addStretch()

    def set_value(self, value):
        self.value_label.setText(str(value))


class CodeBlock(QTextEdit):
    """代码块组件（深色主题）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['code_bg']};
                color: {COLORS['code_text']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 12px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 13px;
                line-height: 1.6;
                selection-background-color: rgba(37, 99, 235, 0.3);
            }}
        """)
