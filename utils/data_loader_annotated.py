# -*- coding: utf-8 -*-
"""
数据加载器 - PyPalPrep Python学习教辅系统

【文件功能说明】
这个文件提供了从数据库加载各种数据的功能。

【为什么需要数据加载器】
1. 封装数据库查询逻辑，其他模块不需要直接写SQL
2. 提供统一的数据访问接口
3. 处理数据转换（从数据库记录到Python对象）

【数据加载器的职责】
1. 加载知识点数据
2. 加载题目数据
3. 加载用户学习记录
4. 加载用户练习记录
5. 加载用户错题
6. 获取用户统计信息

【设计模式】
使用静态方法（@staticmethod），不需要创建实例就可以调用。
这样使用起来更简单：DataLoader.load_all_questions()
"""
from database.db_manager import db_manager  # 导入数据库管理器
from models.knowledge import KnowledgePoint  # 导入知识点模型
from models.question import Question  # 导入题目模型
from models.record import LearningRecord, PracticeRecord, WrongQuestion  # 导入记录模型
import json  # 导入JSON模块


class DataLoader:
    """
    数据加载器类

    【类的作用】
    提供从数据库加载各种数据的方法。

    【使用示例】
    # 加载所有知识点
    knowledge_points = DataLoader.load_all_knowledge_points()

    # 加载指定分类的题目
    questions = DataLoader.load_questions_by_category("Python基础")

    # 获取用户统计信息
    stats = DataLoader.get_user_statistics(user_id=1)
    """

    @staticmethod
    def load_all_knowledge_points():
        """
        加载所有知识点

        【返回值】
        - 知识点列表（KnowledgePoint对象列表）

        【示例】
        knowledge_points = DataLoader.load_all_knowledge_points()
        for kp in knowledge_points:
            print(f"{kp.category} - {kp.title}")
        """
        db_manager.connect()
        # 查询所有知识点，按分类和排序号排序
        query = "SELECT * FROM knowledge_points ORDER BY category, order_num"
        results = db_manager.execute_query(query)
        db_manager.disconnect()

        # 将查询结果转换为KnowledgePoint对象列表
        knowledge_points = []
        for row in results:
            kp = KnowledgePoint.from_dict(dict(row))
            knowledge_points.append(kp)

        return knowledge_points

    @staticmethod
    def load_knowledge_by_category(category):
        """
        根据分类加载知识点

        【参数说明】
        - category: 分类名称（如"Python基础"）

        【返回值】
        - 该分类的知识点列表

        【示例】
        python_basics = DataLoader.load_knowledge_by_category("Python基础")
        """
        db_manager.connect()
        # 查询指定分类的知识点
        query = "SELECT * FROM knowledge_points WHERE category = ? ORDER BY order_num"
        results = db_manager.execute_query(query, (category,))
        db_manager.disconnect()

        knowledge_points = []
        for row in results:
            kp = KnowledgePoint.from_dict(dict(row))
            knowledge_points.append(kp)

        return knowledge_points

    @staticmethod
    def load_knowledge_by_id(knowledge_id):
        """
        根据ID加载知识点

        【参数说明】
        - knowledge_id: 知识点ID

        【返回值】
        - KnowledgePoint对象（如果找到）
        - None（如果未找到）
        """
        db_manager.connect()
        query = "SELECT * FROM knowledge_points WHERE id = ?"
        results = db_manager.execute_query(query, (knowledge_id,))
        db_manager.disconnect()

        if results:
            return KnowledgePoint.from_dict(dict(results[0]))
        return None

    @staticmethod
    def load_all_questions():
        """
        加载所有题目

        【返回值】
        - 题目列表（Question对象列表）
        """
        db_manager.connect()
        query = "SELECT * FROM questions ORDER BY category, type"
        results = db_manager.execute_query(query)
        db_manager.disconnect()

        questions = []
        for row in results:
            q = Question.from_dict(dict(row))
            questions.append(q)

        return questions

    @staticmethod
    def load_questions_by_category(category):
        """
        根据分类加载题目

        【参数说明】
        - category: 分类名称

        【返回值】
        - 该分类的题目列表
        """
        db_manager.connect()
        query = "SELECT * FROM questions WHERE category = ? ORDER BY type"
        results = db_manager.execute_query(query, (category,))
        db_manager.disconnect()

        questions = []
        for row in results:
            q = Question.from_dict(dict(row))
            questions.append(q)

        return questions

    @staticmethod
    def load_questions_by_type(q_type):
        """
        根据类型加载题目

        【参数说明】
        - q_type: 题目类型（choice/judge/fill/code）

        【返回值】
        - 该类型的题目列表
        """
        db_manager.connect()
        query = "SELECT * FROM questions WHERE type = ?"
        results = db_manager.execute_query(query, (q_type,))
        db_manager.disconnect()

        questions = []
        for row in results:
            q = Question.from_dict(dict(row))
            questions.append(q)

        return questions

    @staticmethod
    def load_question_by_id(question_id):
        """
        根据ID加载题目

        【参数说明】
        - question_id: 题目ID

        【返回值】
        - Question对象（如果找到）
        - None（如果未找到）
        """
        db_manager.connect()
        query = "SELECT * FROM questions WHERE id = ?"
        results = db_manager.execute_query(query, (question_id,))
        db_manager.disconnect()

        if results:
            return Question.from_dict(dict(results[0]))
        return None

    @staticmethod
    def load_user_learning_records(user_id):
        """
        加载用户的学习记录

        【参数说明】
        - user_id: 用户ID

        【返回值】
        - 学习记录列表

        【示例】
        records = DataLoader.load_user_learning_records(user_id=1)
        for record in records:
            print(f"学习了 {record['title']}，用时 {record['study_time']} 秒")
        """
        db_manager.connect()
        # 使用LEFT JOIN关联知识点表，获取知识点标题和分类
        query = """
            SELECT lr.*, kp.title, kp.category
            FROM learning_records lr
            LEFT JOIN knowledge_points kp ON lr.knowledge_id = kp.id
            WHERE lr.user_id = ?
            ORDER BY lr.last_study_at DESC
        """
        results = db_manager.execute_query(query, (user_id,))
        db_manager.disconnect()

        records = []
        for row in results:
            record_dict = dict(row)
            records.append(record_dict)

        return records

    @staticmethod
    def load_user_practice_records(user_id, limit=None):
        """
        加载用户的练习记录

        【参数说明】
        - user_id: 用户ID
        - limit: 限制数量（可选）

        【返回值】
        - 练习记录列表
        """
        db_manager.connect()
        if limit:
            # 限制返回数量
            query = """
                SELECT pr.*, q.question, q.type, q.category
                FROM practice_records pr
                LEFT JOIN questions q ON pr.question_id = q.id
                WHERE pr.user_id = ?
                ORDER BY pr.submit_time DESC
                LIMIT ?
            """
            results = db_manager.execute_query(query, (user_id, limit))
        else:
            query = """
                SELECT pr.*, q.question, q.type, q.category
                FROM practice_records pr
                LEFT JOIN questions q ON pr.question_id = q.id
                WHERE pr.user_id = ?
                ORDER BY pr.submit_time DESC
            """
            results = db_manager.execute_query(query, (user_id,))
        db_manager.disconnect()

        records = []
        for row in results:
            records.append(dict(row))

        return records

    @staticmethod
    def load_user_wrong_questions(user_id):
        """
        加载用户的错题

        【参数说明】
        - user_id: 用户ID

        【返回值】
        - 错题列表（未掌握的）

        【示例】
        wrong_questions = DataLoader.load_user_wrong_questions(user_id=1)
        print(f"你有 {len(wrong_questions)} 道错题")
        """
        db_manager.connect()
        # 查询未掌握的错题
        query = """
            SELECT wq.*, q.question, q.type, q.answer, q.explanation, q.options, q.category
            FROM wrong_questions wq
            LEFT JOIN questions q ON wq.question_id = q.id
            WHERE wq.user_id = ? AND wq.mastered = 0
            ORDER BY wq.last_wrong_at DESC
        """
        results = db_manager.execute_query(query, (user_id,))
        db_manager.disconnect()

        wrong_questions = []
        for row in results:
            wrong_questions.append(dict(row))

        return wrong_questions

    @staticmethod
    def get_user_statistics(user_id):
        """
        获取用户统计信息

        【参数说明】
        - user_id: 用户ID

        【返回值】
        - 统计信息字典，包含：
          - total_study_time: 总学习时长（秒）
          - completed_knowledge: 完成的知识点数
          - total_questions: 总练习题数
          - correct_questions: 正确题数
          - wrong_questions_count: 错题数
          - accuracy: 正确率（百分比）

        【示例】
        stats = DataLoader.get_user_statistics(user_id=1)
        print(f"总学习时长: {stats['total_study_time'] // 60} 分钟")
        print(f"正确率: {stats['accuracy']}%")
        """
        db_manager.connect()

        # 总学习时长
        query = "SELECT SUM(study_time) as total_time FROM learning_records WHERE user_id = ?"
        result = db_manager.execute_query(query, (user_id,))
        total_study_time = dict(result[0])['total_time'] if result and result[0][0] else 0

        # 完成的知识点数
        query = "SELECT COUNT(*) as count FROM learning_records WHERE user_id = ? AND completed = 1"
        result = db_manager.execute_query(query, (user_id,))
        completed_knowledge = dict(result[0])['count'] if result else 0

        # 总练习题数
        query = "SELECT COUNT(*) as count FROM practice_records WHERE user_id = ?"
        result = db_manager.execute_query(query, (user_id,))
        total_questions = dict(result[0])['count'] if result else 0

        # 正确题数
        query = "SELECT COUNT(*) as count FROM practice_records WHERE user_id = ? AND is_correct = 1"
        result = db_manager.execute_query(query, (user_id,))
        correct_questions = dict(result[0])['count'] if result else 0

        # 错题数
        query = "SELECT COUNT(*) as count FROM wrong_questions WHERE user_id = ? AND mastered = 0"
        result = db_manager.execute_query(query, (user_id,))
        wrong_questions_count = dict(result[0])['count'] if result else 0

        db_manager.disconnect()

        # 计算正确率
        accuracy = (correct_questions / total_questions * 100) if total_questions > 0 else 0

        return {
            'total_study_time': total_study_time or 0,
            'completed_knowledge': completed_knowledge,
            'total_questions': total_questions,
            'correct_questions': correct_questions,
            'wrong_questions_count': wrong_questions_count,
            'accuracy': round(accuracy, 2)  # 保留2位小数
        }
