# -*- coding: utf-8 -*-
"""
UI 组件模块
"""
from ui.widgets.knowledge_widget import KnowledgeWidget
from ui.widgets.practice_widget import PracticeWidget
from ui.widgets.exam_widget import ExamWidget
from ui.widgets.editor_widget import EditorWidget
from ui.widgets.progress_widget import ProgressWidget
from ui.widgets.mistakes_widget import MistakesWidget
from ui.widgets.statistics_widget import StatisticsWidget
from ui.widgets.profile_widget import ProfileWidget
from ui.widgets.ai_assistant import AIAssistant

__all__ = [
    'KnowledgeWidget', 'PracticeWidget', 'ExamWidget',
    'EditorWidget', 'ProgressWidget', 'MistakesWidget',
    'StatisticsWidget', 'ProfileWidget', 'AIAssistant'
]
