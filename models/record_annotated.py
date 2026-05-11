# -*- coding: utf-8 -*-
"""
学习记录模型 - PyPalPrep Python学习教辅系统

【文件功能说明】
这个文件定义了三种记录类：
1. LearningRecord - 学习记录（记录用户学习知识点的情况）
2. PracticeRecord - 练习记录（记录用户做题的情况）
3. WrongQuestion - 错题记录（记录用户做错的题目）

【为什么需要记录类】
1. 数据封装：将数据库中的记录封装成Python对象
2. 便于操作：可以在对象上调用方法，而不仅仅是操作字典
3. 类型安全：明确知道对象有哪些属性

【三种记录的关系】
- LearningRecord: 记录用户学习了哪些知识点，学了多久
- PracticeRecord: 记录用户做了哪些题目，答案是什么
- WrongQuestion: 记录用户做错的题目，错误次数等
"""


class LearningRecord:
    """
    学习记录类

    【属性说明】
    - id: 记录ID
    - user_id: 用户ID
    - knowledge_id: 知识点ID
    - study_time: 学习时长（秒）
    - completed: 是否完成（True/False）
    - last_study_at: 最后学习时间
    """

    def __init__(self, record_id=None, user_id=None, knowledge_id=None,
                 study_time=0, completed=False, last_study_at=None):
        """
        初始化学习记录对象

        【参数说明】
        - record_id: 记录ID
        - user_id: 用户ID
        - knowledge_id: 知识点ID
        - study_time: 学习时长（秒），默认为0
        - completed: 是否完成，默认为False
        - last_study_at: 最后学习时间
        """
        self.id = record_id
        self.user_id = user_id
        self.knowledge_id = knowledge_id
        self.study_time = study_time
        self.completed = completed
        self.last_study_at = last_study_at

    @classmethod
    def from_dict(cls, data):
        """
        从字典创建学习记录对象

        【参数说明】
        - data: 学习记录数据字典

        【返回值】
        - LearningRecord对象
        """
        if not data:
            return None

        return cls(
            record_id=data.get('id'),
            user_id=data.get('user_id'),
            knowledge_id=data.get('knowledge_id'),
            study_time=data.get('study_time', 0),
            completed=bool(data.get('completed', 0)),  # 转换为布尔值
            last_study_at=data.get('last_study_at')
        )

    def to_dict(self):
        """
        将学习记录对象转换为字典

        【返回值】
        - 学习记录数据字典
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'knowledge_id': self.knowledge_id,
            'study_time': self.study_time,
            'completed': self.completed,
            'last_study_at': self.last_study_at
        }


class PracticeRecord:
    """
    练习记录类

    【属性说明】
    - id: 记录ID
    - user_id: 用户ID
    - question_id: 题目ID
    - user_answer: 用户的答案
    - is_correct: 是否正确（True/False/None）
    - submit_time: 提交时间
    - time_spent: 用时（秒）
    """

    def __init__(self, record_id=None, user_id=None, question_id=None,
                 user_answer=None, is_correct=None, submit_time=None, time_spent=0):
        """
        初始化练习记录对象

        【参数说明】
        - record_id: 记录ID
        - user_id: 用户ID
        - question_id: 题目ID
        - user_answer: 用户的答案
        - is_correct: 是否正确
        - submit_time: 提交时间
        - time_spent: 用时（秒），默认为0
        """
        self.id = record_id
        self.user_id = user_id
        self.question_id = question_id
        self.user_answer = user_answer
        self.is_correct = is_correct
        self.submit_time = submit_time
        self.time_spent = time_spent

    @classmethod
    def from_dict(cls, data):
        """
        从字典创建练习记录对象

        【参数说明】
        - data: 练习记录数据字典

        【返回值】
        - PracticeRecord对象
        """
        if not data:
            return None

        return cls(
            record_id=data.get('id'),
            user_id=data.get('user_id'),
            question_id=data.get('question_id'),
            user_answer=data.get('user_answer'),
            is_correct=bool(data.get('is_correct')) if data.get('is_correct') is not None else None,
            submit_time=data.get('submit_time'),
            time_spent=data.get('time_spent', 0)
        )

    def to_dict(self):
        """
        将练习记录对象转换为字典

        【返回值】
        - 练习记录数据字典
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'submit_time': self.submit_time,
            'time_spent': self.time_spent
        }


class WrongQuestion:
    """
    错题记录类

    【属性说明】
    - id: 记录ID
    - user_id: 用户ID
    - question_id: 题目ID
    - wrong_count: 错误次数
    - mastered: 是否已掌握（True/False）
    - first_wrong_at: 首次错误时间
    - last_wrong_at: 最后错误时间
    """

    def __init__(self, record_id=None, user_id=None, question_id=None,
                 wrong_count=1, mastered=False, first_wrong_at=None, last_wrong_at=None):
        """
        初始化错题记录对象

        【参数说明】
        - record_id: 记录ID
        - user_id: 用户ID
        - question_id: 题目ID
        - wrong_count: 错误次数，默认为1
        - mastered: 是否已掌握，默认为False
        - first_wrong_at: 首次错误时间
        - last_wrong_at: 最后错误时间
        """
        self.id = record_id
        self.user_id = user_id
        self.question_id = question_id
        self.wrong_count = wrong_count
        self.mastered = mastered
        self.first_wrong_at = first_wrong_at
        self.last_wrong_at = last_wrong_at

    @classmethod
    def from_dict(cls, data):
        """
        从字典创建错题记录对象

        【参数说明】
        - data: 错题记录数据字典

        【返回值】
        - WrongQuestion对象
        """
        if not data:
            return None

        return cls(
            record_id=data.get('id'),
            user_id=data.get('user_id'),
            question_id=data.get('question_id'),
            wrong_count=data.get('wrong_count', 1),
            mastered=bool(data.get('mastered', 0)),  # 转换为布尔值
            first_wrong_at=data.get('first_wrong_at'),
            last_wrong_at=data.get('last_wrong_at')
        )

    def to_dict(self):
        """
        将错题记录对象转换为字典

        【返回值】
        - 错题记录数据字典
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'wrong_count': self.wrong_count,
            'mastered': self.mastered,
            'first_wrong_at': self.first_wrong_at,
            'last_wrong_at': self.last_wrong_at
        }
