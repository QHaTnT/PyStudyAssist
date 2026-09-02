# -*- coding: utf-8 -*-
"""
PyStudyAssist 主题配置
定义颜色、字体、QSS 样式
"""

# ==================== 颜色配置 ====================

COLORS = {
    # 主色
    'primary': '#2563EB',
    'primary_light': '#3B82F6',
    'primary_dark': '#1D4ED8',
    'primary_alpha': 'rgba(37, 99, 235, 0.1)',
    'primary_alpha_hover': 'rgba(37, 99, 235, 0.15)',

    # 功能色
    'success': '#10B981',
    'success_light': '#D1FAE5',
    'warning': '#F59E0B',
    'warning_light': '#FEF3C7',
    'danger': '#EF4444',
    'danger_light': '#FEE2E2',
    'info': '#06B6D4',
    'info_light': '#CFFAFE',

    # 玻璃拟态色
    'glass_bg': 'rgba(255, 255, 255, 0.7)',
    'glass_bg_solid': '#FFFFFF',
    'glass_border': 'rgba(255, 255, 255, 0.3)',
    'glass_shadow': 'rgba(0, 0, 0, 0.08)',
    'glass_shadow_hover': 'rgba(0, 0, 0, 0.12)',

    # 背景渐变
    'gradient_start': '#EFF6FF',
    'gradient_mid': '#DBEAFE',
    'gradient_end': '#F0F9FF',

    # 文字色
    'text_primary': '#1E293B',
    'text_secondary': '#64748B',
    'text_hint': '#94A3B8',
    'text_white': '#FFFFFF',

    # 边框色
    'border': '#E2E8F0',
    'border_light': 'rgba(255, 255, 255, 0.5)',
    'border_focus': '#2563EB',

    # 代码编辑器
    'code_bg': '#1E293B',
    'code_text': '#E2E8F0',
    'code_keyword': '#C084FC',
    'code_string': '#86EFAC',
    'code_comment': '#64748B',
}

# ==================== 字体配置 ====================
# QFont weight 值: Normal=50, Medium=57, SemiBold=63, Bold=75, ExtraBold=81

FONTS = {
    'title': ('Microsoft YaHei', 32, 75),      # Bold
    'heading': ('Microsoft YaHei', 24, 75),    # Bold
    'subheading': ('Microsoft YaHei', 20, 63), # SemiBold
    'body': ('Microsoft YaHei', 16, 50),       # Normal
    'body_bold': ('Microsoft YaHei', 16, 75),  # Bold
    'caption': ('Microsoft YaHei', 14, 50),    # Normal
    'small': ('Microsoft YaHei', 13, 50),      # Normal
    'code': ('Consolas', 15, 50),              # Normal
    'code_small': ('Consolas', 13, 50),        # Normal
    'nav': ('Microsoft YaHei', 15, 57),        # Medium
    'button': ('Microsoft YaHei', 16, 63),     # SemiBold
    'button_small': ('Microsoft YaHei', 14, 57), # Medium
    'input': ('Microsoft YaHei', 16, 50),      # Normal
}

# ==================== 尺寸配置 ====================

SIZES = {
    'border_radius_small': 8,
    'border_radius': 12,
    'border_radius_large': 16,
    'border_radius_xl': 20,
    'border_radius_round': 9999,

    'padding_small': 8,
    'padding': 12,
    'padding_large': 16,
    'padding_xl': 24,

    'nav_width_collapsed': 72,
    'nav_width_expanded': 240,
    'nav_item_height': 48,

    'button_height': 44,
    'button_height_small': 36,
    'input_height': 44,
    'card_min_height': 120,
}

# ==================== QSS 样式生成 ====================

def get_qss():
    """生成全局 QSS 样式表"""
    return f"""
    /* ==================== 全局样式 ==================== */
    * {{
        font-family: 'Microsoft YaHei', 'PingFang SC', 'SF Pro Display', 'Segoe UI';
    }}

    QWidget {{
        background-color: transparent;
        color: {COLORS['text_primary']};
        font-size: 15px;
    }}

    /* ==================== 滚动条 ==================== */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: rgba(0, 0, 0, 0.15);
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: rgba(0, 0, 0, 0.25);
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: rgba(0, 0, 0, 0.15);
        border-radius: 5px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: rgba(0, 0, 0, 0.25);
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* ==================== 按钮 ==================== */
    QPushButton {{
        background-color: {COLORS['glass_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: {SIZES['border_radius']}px;
        padding: 10px 20px;
        font-size: 15px;
        font-weight: 500;
        color: {COLORS['text_primary']};
        min-height: {SIZES['button_height']}px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['primary_alpha_hover']};
        border-color: {COLORS['primary_light']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['primary_alpha']};
    }}

    QPushButton:disabled {{
        background-color: rgba(0, 0, 0, 0.05);
        color: {COLORS['text_hint']};
        border-color: {COLORS['border']};
    }}

    /* ==================== 输入框 ==================== */
    QLineEdit, QTextEdit {{
        background-color: {COLORS['glass_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: {SIZES['border_radius']}px;
        padding: 10px 14px;
        font-size: 15px;
        color: {COLORS['text_primary']};
        selection-background-color: {COLORS['primary_alpha']};
    }}

    QLineEdit:focus, QTextEdit:focus {{
        border: 2px solid {COLORS['primary']};
        background-color: {COLORS['glass_bg_solid']};
    }}

    QLineEdit::placeholder, QTextEdit::placeholder {{
        color: {COLORS['text_hint']};
    }}

    /* ==================== 下拉框 ==================== */
    QComboBox {{
        background-color: {COLORS['glass_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: {SIZES['border_radius']}px;
        padding: 8px 12px;
        font-size: 15px;
        color: {COLORS['text_primary']};
        min-height: 25px;
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
        font-size: 15px;
        selection-background-color: {COLORS['primary_alpha']};
        selection-color: {COLORS['primary']};
    }}

    /* ==================== 复选框 ==================== */
    QCheckBox {{
        spacing: 8px;
        font-size: 15px;
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

    /* ==================== 单选按钮 ==================== */
    QRadioButton {{
        spacing: 8px;
        font-size: 15px;
        color: {COLORS['text_primary']};
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

    /* ==================== 进度条 ==================== */
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

    /* ==================== 表格 ==================== */
    QTableWidget {{
        background-color: {COLORS['glass_bg_solid']};
        border: 1px solid {COLORS['border']};
        border-radius: {SIZES['border_radius']}px;
        gridline-color: {COLORS['border']};
        selection-background-color: {COLORS['primary_alpha']};
        font-size: 15px;
    }}

    QTableWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {COLORS['border']};
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS['primary_alpha']};
        color: {COLORS['primary']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['gradient_start']};
        border: none;
        border-bottom: 2px solid {COLORS['border']};
        padding: 10px 12px;
        font-weight: 600;
        font-size: 14px;
        color: {COLORS['text_secondary']};
    }}

    /* ==================== 列表 ==================== */
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
        font-size: 15px;
    }}

    QListWidget::item {{
        padding: 12px 14px;
        border-radius: {SIZES['border_radius_small']}px;
        margin: 2px 4px;
    }}

    QListWidget::item:hover {{
        background-color: {COLORS['primary_alpha_hover']};
    }}

    QListWidget::item:selected {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
    }}

    /* ==================== 分组框 ==================== */
    QGroupBox {{
        background-color: {COLORS['glass_bg']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {SIZES['border_radius_large']}px;
        margin-top: 20px;
        padding: 20px 16px 16px 16px;
        font-weight: 600;
        font-size: 15px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        top: 8px;
        padding: 0 8px;
        background-color: {COLORS['glass_bg_solid']};
        border-radius: 6px;
        color: {COLORS['text_secondary']};
        font-size: 14px;
    }}

    /* ==================== 标签页 ==================== */
    QTabWidget::pane {{
        background-color: transparent;
        border: none;
    }}

    QTabBar::tab {{
        background-color: transparent;
        border: none;
        padding: 10px 20px;
        margin-right: 4px;
        font-size: 15px;
        font-weight: 500;
        color: {COLORS['text_secondary']};
        border-bottom: 2px solid transparent;
    }}

    QTabBar::tab:hover {{
        color: {COLORS['primary']};
        background-color: {COLORS['primary_alpha_hover']};
    }}

    QTabBar::tab:selected {{
        color: {COLORS['primary']};
        border-bottom: 2px solid {COLORS['primary']};
        font-weight: 600;
    }}

    /* ==================== 工具提示 ==================== */
    QToolTip {{
        background-color: {COLORS['code_bg']};
        color: {COLORS['text_white']};
        border: none;
        border-radius: {SIZES['border_radius_small']}px;
        padding: 8px 12px;
        font-size: 13px;
    }}

    /* ==================== 分割器 ==================== */
    QSplitter::handle {{
        background-color: {COLORS['border']};
        width: 1px;
        height: 1px;
    }}

    QSplitter::handle:hover {{
        background-color: {COLORS['primary_light']};
    }}
    """


def get_nav_qss():
    """导航栏专用 QSS"""
    return f"""
    QListWidget#navList {{
        background-color: {COLORS['glass_bg']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {SIZES['border_radius_large']}px;
        padding: 8px;
    }}

    QListWidget#navList::item {{
        background-color: transparent;
        border: none;
        border-radius: {SIZES['border_radius']}px;
        padding: 12px 16px;
        margin: 2px 0;
        color: {COLORS['text_secondary']};
        font-size: 14px;
        font-weight: 500;
    }}

    QListWidget#navList::item:hover {{
        background-color: {COLORS['primary_alpha_hover']};
        color: {COLORS['primary']};
    }}

    QListWidget#navList::item:selected {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
        font-weight: 600;
    }}
    """


def get_card_qss():
    """卡片通用 QSS"""
    return f"""
    background-color: {COLORS['glass_bg']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {SIZES['border_radius_large']}px;
    """


def get_primary_button_qss():
    """主按钮 QSS"""
    return f"""
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
    """


def get_danger_button_qss():
    """危险按钮 QSS"""
    return f"""
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
    """


def get_code_editor_qss():
    """代码编辑器 QSS"""
    return f"""
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
    """
