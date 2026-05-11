# -*- coding: utf-8 -*-
"""
知识点模型 - PyPalPrep Python学习教辅系统

【文件功能说明】
这个文件定义了知识点类（KnowledgePoint），用于表示和操作Python知识点。

【KnowledgePoint类的职责】
1. 存储知识点信息（标题、内容、代码示例等）
2. 提供创建知识点对象的方法
3. 提供转换为字典的方法

【知识点结构】
每个知识点包含：
- 分类：属于哪个知识领域
- 标题：知识点的名称
- 详细内容：知识点的详细说明
- 代码示例：相关的Python代码示例
- 难度等级：简单/中等/困难
- 排序号：用于控制显示顺序
"""


class KnowledgePoint:
    """
    知识点类

    【属性说明】
    - id: 知识点ID
    - category: 分类（如"Python基础"）
    - title: 标题
    - content: 内容详情
    - code_example: 代码示例
    - difficulty: 难度等级
    - order_num: 排序号
    - created_at: 创建时间
    """

    def __init__(self, knowledge_id=None, category=None, title=None, content=None,
                 code_example=None, difficulty='medium', order_num=0, created_at=None):
        """
        初始化知识点对象

        【参数说明】
        - knowledge_id: 知识点ID
        - category: 分类
        - title: 标题
        - content: 内容详情
        - code_example: 代码示例
        - difficulty: 难度等级，默认为'medium'
        - order_num: 排序号，默认为0
        - created_at: 创建时间
        """
        self.id = knowledge_id
        self.category = category
        self.title = title
        self.content = content
        self.code_example = code_example
        self.difficulty = difficulty
        self.order_num = order_num
        self.created_at = created_at

    @classmethod
    def from_dict(cls, data):
        """
        从字典创建知识点对象

        【参数说明】
        - data: 知识点数据字典（通常从数据库查询结果转换而来）

        【返回值】
        - KnowledgePoint对象

        【示例】
        kp_data = {
            'id': 1,
            'category': 'Python基础',
            'title': 'Python简介',
            'content': 'Python是一种解释型语言...',
            'code_example': 'print("Hello")'
        }
        kp = KnowledgePoint.from_dict(kp_data)
        """
        if not data:
            return None

        return cls(
            knowledge_id=data.get('id'),
            category=data.get('category'),
            title=data.get('title'),
            content=data.get('content'),
            code_example=data.get('code_example'),
            difficulty=data.get('difficulty', 'medium'),
            order_num=data.get('order_num', 0),
            created_at=data.get('created_at')
        )

    def to_dict(self):
        """
        将知识点对象转换为字典

        【返回值】
        - 知识点数据字典
        """
        return {
            'id': self.id,
            'category': self.category,
            'title': self.title,
            'content': self.content,
            'code_example': self.code_example,
            'difficulty': self.difficulty,
            'order_num': self.order_num,
            'created_at': self.created_at
        }

    def __repr__(self):
        """
        对象的字符串表示

        【示例】
        kp = KnowledgePoint(category='Python基础', title='Python简介')
        print(kp)  # 输出: <KnowledgePoint Python基础 - Python简介>
        """
        return f"<KnowledgePoint {self.category} - {self.title}>"
