# -*- coding: utf-8 -*-
"""
图标定义
使用 Unicode emoji 作为图标
"""


class Icons:
    """图标常量"""

    # 导航图标
    NAV_KNOWLEDGE = "📚"
    NAV_PRACTICE = "✍️"
    NAV_EXAM = "📝"
    NAV_EDITOR = "💻"
    NAV_PROGRESS = "📊"
    NAV_MISTAKES = "❌"
    NAV_STATISTICS = "📈"
    NAV_PROFILE = "👤"
    NAV_SETTINGS = "⚙️"

    # 功能图标
    ADD = "➕"
    DELETE = "🗑️"
    EDIT = "✏️"
    SAVE = "💾"
    OPEN = "📂"
    NEW = "📄"
    RUN = "▶️"
    STOP = "⏹️"
    REFRESH = "🔄"
    SEARCH = "🔍"
    BACK = "←"
    FORWARD = "→"

    # 状态图标
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"

    # AI 助手
    AI_LOGO = "🎓"
    AI_SEND = "✈"
    AI_ATTACH = "📎"
    AI_CLEAR = "🗑"
    AI_DIAGNOSE = "🔍 诊断代码"
    AI_QUICK = "📎 快速问题"

    # 学习相关
    CLOCK = "⏱️"
    STAR = "⭐"
    BOOK = "📖"
    TROPHY = "🏆"
    FIRE = "🔥"
    HEART = "❤️"

    # 用户相关
    AVATAR_DEFAULT = "👤"
    LOGOUT = "🚪"
    LOGIN = "🔑"
    REGISTER = "📝"

    @classmethod
    def get_nav_icon(cls, index: int) -> str:
        """根据索引获取导航图标"""
        nav_icons = [
            cls.NAV_KNOWLEDGE,
            cls.NAV_PRACTICE,
            cls.NAV_EXAM,
            cls.NAV_EDITOR,
            cls.NAV_PROGRESS,
            cls.NAV_MISTAKES,
            cls.NAV_STATISTICS,
            cls.NAV_PROFILE,
        ]
        return nav_icons[index] if 0 <= index < len(nav_icons) else ""

    @classmethod
    def get_nav_label(cls, index: int) -> str:
        """根据索引获取导航标签"""
        nav_labels = [
            "知识学习",
            "题库练习",
            "模拟考试",
            "代码编辑",
            "学习进度",
            "错题本",
            "成绩统计",
            "个人主页",
        ]
        return nav_labels[index] if 0 <= index < len(nav_labels) else ""
