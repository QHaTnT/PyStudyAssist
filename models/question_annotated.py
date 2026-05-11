# -*- coding: utf-8 -*-
"""
题目模型 - PyPalPrep Python学习教辅系统

【文件功能说明】
这个文件定义了题目类（Question），用于表示和操作练习题。

【Question类的职责】
1. 存储题目信息（题干、选项、答案等）
2. 提供创建题目对象的方法
3. 提供检查答案的方法

【题目类型说明】
- choice: 选择题（单选）
- judge: 判断题（对/错）
- fill: 填空题
- code: 编程题

【选项格式】
选择题的选项存储为JSON格式的字符串，例如：
'["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"]'
"""
import json  # 导入JSON模块，用于解析选项字符串


class Question:
    """
    题目类

    【属性说明】
    - id: 题目ID
    - category: 所属分类（如"Python基础"）
    - type: 题目类型（choice/judge/fill/code）
    - question: 题目内容
    - options: 选项列表（仅选择题有）
    - answer: 正确答案
    - explanation: 题目解析
    - difficulty: 难度等级
    - created_at: 创建时间
    """

    def __init__(self, question_id=None, category=None, q_type=None, question=None,
                 options=None, answer=None, explanation=None, difficulty='medium', created_at=None):
        """
        初始化题目对象

        【参数说明】
        - question_id: 题目ID
        - category: 分类
        - q_type: 题目类型
        - question: 题目内容
        - options: 选项（字符串或列表）
        - answer: 正确答案
        - explanation: 解析
        - difficulty: 难度，默认为'medium'
        - created_at: 创建时间

        【选项处理】
        如果options是JSON字符串，会自动解析为列表。
        这样无论传入字符串还是列表，都能正常使用。
        """
        self.id = question_id
        self.category = category
        self.type = q_type
        self.question = question

        # 处理选项：如果options是字符串，解析为列表
        if isinstance(options, str) and options:
            try:
                self.options = json.loads(options)
            except json.JSONDecodeError:
                # JSON解析失败，使用空列表
                self.options = []
        else:
            self.options = options if options else []

        self.answer = answer
        self.explanation = explanation
        self.difficulty = difficulty
        self.created_at = created_at

    @classmethod
    def from_dict(cls, data):
        """
        从字典创建题目对象

        【参数说明】
        - data: 题目数据字典（通常从数据库查询结果转换而来）

        【返回值】
        - Question对象

        【示例】
        q_data = {
            'id': 1,
            'category': 'Python基础',
            'type': 'choice',
            'question': 'Python是什么类型的语言？',
            'options': '["A. 编译型", "B. 解释型"]',
            'answer': 'B'
        }
        q = Question.from_dict(q_data)
        """
        if not data:
            return None

        return cls(
            question_id=data.get('id'),
            category=data.get('category'),
            q_type=data.get('type'),
            question=data.get('question'),
            options=data.get('options'),
            answer=data.get('answer'),
            explanation=data.get('explanation'),
            difficulty=data.get('difficulty', 'medium'),
            created_at=data.get('created_at')
        )

    def to_dict(self):
        """
        将题目对象转换为字典

        【返回值】
        - 题目数据字典
        """
        return {
            'id': self.id,
            'category': self.category,
            'type': self.type,
            'question': self.question,
            'options': self.options,
            'answer': self.answer,
            'explanation': self.explanation,
            'difficulty': self.difficulty,
            'created_at': self.created_at
        }

    def get_options_json(self):
        """
        获取JSON格式的选项字符串

        【为什么需要这个方法】
        有时需要将选项转换为JSON字符串存储到数据库。

        【返回值】
        - JSON格式的选项字符串
        """
        return json.dumps(self.options, ensure_ascii=False)

    def check_answer(self, user_answer):
        """
        检查用户答案是否正确

        【参数说明】
        - user_answer: 用户的答案

        【返回值】
        - True: 答案正确
        - False: 答案错误

        【不同题型的判断逻辑】
        - 选择题/判断题：不区分大小写比较
        - 填空题：去除首尾空格后比较
        - 编程题：简单字符串比较（实际应该运行代码验证）

        【示例】
        q = Question(type='choice', answer='B')
        print(q.check_answer('b'))  # True
        print(q.check_answer('B'))  # True
        print(q.check_answer('A'))  # False
        """
        if self.type == 'choice' or self.type == 'judge':
            # 选择题/判断题：不区分大小写比较
            return str(user_answer).strip().upper() == str(self.answer).strip().upper()
        elif self.type == 'fill':
            # 填空题：去除首尾空格后比较
            return str(user_answer).strip() == str(self.answer).strip()
        elif self.type == 'code':
            # 编程题：简单字符串比较
            # 注意：实际应该运行代码并比较输出结果
            return str(user_answer).strip() == str(self.answer).strip()
        return False

    def __repr__(self):
        """
        对象的字符串表示

        【示例】
        q = Question(type='choice', category='Python基础', question='什么是Python？')
        print(q)  # 输出: <Question choice - Python基础 - 什么是Python？...>
        """
        return f"<Question {self.type} - {self.category} - {self.question[:20]}...>"
