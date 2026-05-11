# -*- coding: utf-8 -*-
"""
用户模型 - PyPalPrep Python学习教辅系统

【文件功能说明】
这个文件定义了用户类（User），用于表示和操作用户数据。

【什么是模型（Model）】
在软件开发中，模型是数据的抽象表示。
User类代表一个用户，包含用户的所有信息（ID、用户名、昵称等）。

【为什么需要模型类】
1. 封装数据：将用户数据封装成一个对象，便于传递和使用
2. 类型安全：明确知道对象有哪些属性
3. 代码清晰：使用user.nickname比user['nickname']更清晰
4. 便于扩展：可以在类中添加方法，方便数据操作

【User类的职责】
1. 存储用户信息
2. 提供创建用户的方法（from_dict）
3. 提供转换为字典的方法（to_dict）
"""
from datetime import datetime  # 导入日期时间类


class User:
    """
    用户类

    【类的作用】
    表示一个用户，包含用户的所有信息。

    【属性说明】
    - id: 用户ID（数据库主键）
    - username: 用户名（登录账号）
    - nickname: 昵称（显示名称）
    - created_at: 创建时间
    - last_login: 最后登录时间
    """

    def __init__(self, user_id=None, username=None, nickname=None, created_at=None, last_login=None):
        """
        初始化用户对象

        【参数说明】
        - user_id: 用户ID，默认为None
        - username: 用户名，默认为None
        - nickname: 昵称，默认为None
        - created_at: 创建时间，默认为None
        - last_login: 最后登录时间，默认为None

        【为什么参数都有默认值】
        这样可以灵活地创建用户对象，不一定需要提供所有信息。
        例如：user = User(user_id=1, username="admin")
        """
        self.id = user_id  # 用户ID
        self.username = username  # 用户名
        self.nickname = nickname  # 昵称
        self.created_at = created_at  # 创建时间
        self.last_login = last_login  # 最后登录时间

    @classmethod
    def from_dict(cls, data):
        """
        从字典创建用户对象（类方法）

        【什么是类方法】
        类方法不需要创建实例就可以调用，通过@classmethod装饰器定义。
        可以通过类名直接调用：User.from_dict(data)

        【参数说明】
        - data: 用户数据字典（通常从数据库查询结果转换而来）

        【返回值】
        - User对象

        【示例】
        user_data = {'id': 1, 'username': 'admin', 'nickname': '管理员'}
        user = User.from_dict(user_data)
        print(user.username)  # 输出: admin
        """
        if not data:
            return None

        # 使用字典的get()方法获取值，如果键不存在则返回None
        return cls(
            user_id=data.get('id'),
            username=data.get('username'),
            nickname=data.get('nickname'),
            created_at=data.get('created_at'),
            last_login=data.get('last_login')
        )

    def to_dict(self):
        """
        将用户对象转换为字典

        【为什么需要这个方法】
        有时需要将用户对象转换为字典格式，例如：
        1. 传递给其他模块
        2. 序列化为JSON
        3. 存储到数据库

        【返回值】
        - 用户数据字典
        """
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'created_at': self.created_at,
            'last_login': self.last_login
        }

    def __repr__(self):
        """
        对象的字符串表示

        【什么时候会用到】
        当使用print()打印User对象时，会调用这个方法。

        【示例】
        user = User(user_id=1, username="admin", nickname="管理员")
        print(user)  # 输出: <User admin (管理员)>
        """
        return f"<User {self.username} ({self.nickname})>"
