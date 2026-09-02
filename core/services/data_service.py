# -*- coding: utf-8 -*-
"""
数据服务
处理知识点、题目、记录等数据操作
"""
from typing import List, Dict, Optional
from core.database.sqlite_manager import db
from core.database.sync_manager import sync_manager
from models.knowledge import KnowledgePoint
from models.question import Question


class DataService:
    """数据服务"""

    # ==================== 知识点操作 ====================

    def get_all_knowledge_points(self) -> List[KnowledgePoint]:
        """获取所有知识点"""
        records = db.get_all_knowledge_points()
        return [KnowledgePoint.from_dict(r) for r in records]

    def get_knowledge_by_category(self, category: str) -> List[KnowledgePoint]:
        """根据分类获取知识点"""
        records = db.get_knowledge_by_category(category)
        return [KnowledgePoint.from_dict(r) for r in records]

    def get_knowledge_by_id(self, knowledge_id: int) -> Optional[KnowledgePoint]:
        """根据 ID 获取知识点"""
        record = db.execute_one(
            "SELECT * FROM knowledge_points WHERE id = ?",
            (knowledge_id,)
        )
        return KnowledgePoint.from_dict(record) if record else None

    # ==================== 题目操作 ====================

    def get_all_questions(self) -> List[Question]:
        """获取所有题目"""
        records = db.get_all_questions()
        return [Question.from_dict(r) for r in records]

    def get_questions_by_category(self, category: str) -> List[Question]:
        """根据分类获取题目"""
        records = db.get_questions_by_category(category)
        return [Question.from_dict(r) for r in records]

    def get_questions_by_type(self, q_type: str) -> List[Question]:
        """根据类型获取题目"""
        records = db.execute(
            "SELECT * FROM questions WHERE type = ?",
            (q_type,)
        )
        return [Question.from_dict(r) for r in records]

    def get_random_questions(self, category: str = None, q_type: str = None,
                            exclude_done: bool = False, user_id: int = None,
                            limit: int = None) -> List[Question]:
        """获取随机题目"""
        query = "SELECT * FROM questions WHERE 1=1"
        params = []

        if category and category != '全部':
            query += " AND category = ?"
            params.append(category)

        if q_type:
            query += " AND type = ?"
            params.append(q_type)

        if exclude_done and user_id:
            query += " AND id NOT IN (SELECT question_id FROM practice_records WHERE user_id = ?)"
            params.append(user_id)

        query += " ORDER BY RANDOM()"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        records = db.execute(query, tuple(params))
        return [Question.from_dict(r) for r in records]

    # ==================== 学习记录操作 ====================

    def record_learning(self, user_id: int, knowledge_id: int, study_time: int, completed: bool = False):
        """记录学习"""
        sync_manager.record_learning(user_id, knowledge_id, study_time, completed)

    def get_user_learning_records(self, user_id: int) -> List[Dict]:
        """获取用户学习记录"""
        return db.get_user_learning_records(user_id)

    def mark_knowledge_completed(self, user_id: int, knowledge_id: int, study_time: int):
        """标记知识点为已完成"""
        from datetime import datetime
        existing = db.execute_one(
            "SELECT id, study_time FROM learning_records WHERE user_id = ? AND knowledge_id = ?",
            (user_id, knowledge_id)
        )

        if existing:
            total_time = existing['study_time'] + study_time
            db.execute_update(
                "UPDATE learning_records SET study_time = ?, completed = 1, last_study_at = ? WHERE id = ?",
                (total_time, datetime.now(), existing['id'])
            )
        else:
            db.execute_insert(
                """INSERT INTO learning_records
                (user_id, knowledge_id, study_time, completed, last_study_at)
                VALUES (?, ?, ?, 1, ?)""",
                (user_id, knowledge_id, study_time, datetime.now())
            )

    # ==================== 练习记录操作 ====================

    def record_practice(self, user_id: int, question_id: int, user_answer: str,
                       is_correct: bool, time_spent: int):
        """记录练习"""
        sync_manager.record_practice(user_id, question_id, user_answer, is_correct, time_spent)

        # 如果答错，自动加入错题本
        if not is_correct:
            self.record_wrong_question(user_id, question_id)

    def get_user_practice_records(self, user_id: int, limit: int = None) -> List[Dict]:
        """获取用户练习记录"""
        return db.get_user_practice_records(user_id, limit)

    # ==================== 错题本操作 ====================

    def record_wrong_question(self, user_id: int, question_id: int):
        """记录错题"""
        sync_manager.record_wrong_question(user_id, question_id)

    def get_user_wrong_questions(self, user_id: int) -> List[Dict]:
        """获取用户错题"""
        return db.get_user_wrong_questions(user_id)

    def mark_wrong_question_mastered(self, user_id: int, question_id: int):
        """标记错题为已掌握"""
        db.update_wrong_question(user_id, question_id, mastered=1)

    # ==================== 统计操作 ====================

    def get_user_statistics(self, user_id: int) -> Dict:
        """获取用户统计信息"""
        return db.get_user_statistics(user_id)

    def get_category_statistics(self, user_id: int) -> List[Dict]:
        """获取分类统计"""
        from config import config
        categories = config.knowledge.categories
        stats = []

        for category in categories:
            # 该分类的总知识点数
            total_result = db.execute_one(
                "SELECT COUNT(*) as count FROM knowledge_points WHERE category = ?",
                (category,)
            )
            total_count = total_result['count'] if total_result else 0

            # 已完成的知识点数
            completed_result = db.execute_one(
                """SELECT COUNT(DISTINCT lr.knowledge_id) as count
                FROM learning_records lr
                JOIN knowledge_points kp ON lr.knowledge_id = kp.id
                WHERE lr.user_id = ? AND kp.category = ? AND lr.completed = 1""",
                (user_id, category)
            )
            completed_count = completed_result['count'] if completed_result else 0

            # 该分类的练习正确率
            accuracy_result = db.execute_one(
                """SELECT
                    COUNT(CASE WHEN pr.is_correct = 1 THEN 1 END) as correct,
                    COUNT(*) as total
                FROM practice_records pr
                JOIN questions q ON pr.question_id = q.id
                WHERE pr.user_id = ? AND q.category = ?""",
                (user_id, category)
            )

            if accuracy_result and accuracy_result['total'] > 0:
                accuracy = round(accuracy_result['correct'] / accuracy_result['total'] * 100, 1)
            else:
                accuracy = None

            progress = int((completed_count / total_count) * 100) if total_count > 0 else 0

            stats.append({
                'category': category,
                'total': total_count,
                'completed': completed_count,
                'progress': progress,
                'accuracy': accuracy
            })

        return stats


# 全局实例
data_service = DataService()
