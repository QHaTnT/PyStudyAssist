# -*- coding: utf-8 -*-
"""
数据加载器
"""
from typing import List, Optional
from core.database.sqlite_manager import db
from models.knowledge import KnowledgePoint
from models.question import Question


class DataLoader:
    """数据加载器"""

    @staticmethod
    def load_all_knowledge_points() -> List[KnowledgePoint]:
        """加载所有知识点"""
        records = db.execute("SELECT * FROM knowledge_points ORDER BY category, order_num")
        return [KnowledgePoint.from_dict(r) for r in records]

    @staticmethod
    def load_knowledge_by_category(category: str) -> List[KnowledgePoint]:
        """根据分类加载知识点"""
        records = db.execute(
            "SELECT * FROM knowledge_points WHERE category = ? ORDER BY order_num",
            (category,)
        )
        return [KnowledgePoint.from_dict(r) for r in records]

    @staticmethod
    def load_knowledge_by_id(knowledge_id: int) -> Optional[KnowledgePoint]:
        """根据ID加载知识点"""
        record = db.execute_one(
            "SELECT * FROM knowledge_points WHERE id = ?",
            (knowledge_id,)
        )
        return KnowledgePoint.from_dict(record) if record else None

    @staticmethod
    def load_all_questions() -> List[Question]:
        """加载所有题目"""
        records = db.execute("SELECT * FROM questions ORDER BY category, type")
        return [Question.from_dict(r) for r in records]

    @staticmethod
    def load_questions_by_category(category: str) -> List[Question]:
        """根据分类加载题目"""
        records = db.execute(
            "SELECT * FROM questions WHERE category = ?",
            (category,)
        )
        return [Question.from_dict(r) for r in records]

    @staticmethod
    def load_questions_by_type(q_type: str) -> List[Question]:
        """根据类型加载题目"""
        records = db.execute(
            "SELECT * FROM questions WHERE type = ?",
            (q_type,)
        )
        return [Question.from_dict(r) for r in records]

    @staticmethod
    def load_question_by_id(question_id: int) -> Optional[Question]:
        """根据ID加载题目"""
        record = db.execute_one(
            "SELECT * FROM questions WHERE id = ?",
            (question_id,)
        )
        return Question.from_dict(record) if record else None

    @staticmethod
    def load_user_wrong_questions(user_id: int) -> List[dict]:
        """加载用户错题"""
        return db.get_user_wrong_questions(user_id)

    @staticmethod
    def get_user_statistics(user_id: int) -> dict:
        """获取用户统计信息"""
        return db.get_user_statistics(user_id)
