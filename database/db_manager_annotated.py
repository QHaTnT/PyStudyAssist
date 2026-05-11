# -*- coding: utf-8 -*-
"""
数据库管理模块 - PyPalPrep Python学习教辅系统

【文件功能说明】
这个文件负责所有数据库相关的操作，包括：
1. 创建数据库和表
2. 连接/断开数据库
3. 执行SQL查询
4. 管理用户数据

【为什么需要这个模块】
- 数据库是存储用户数据的地方（学习记录、练习成绩等）
- 这个模块封装了所有数据库操作，其他模块不需要直接写SQL语句
- 使用单例模式，确保整个程序只有一个数据库连接

【SQLite数据库】
SQLite是一种轻量级的数据库，数据存储在一个文件中。
适合桌面应用程序，不需要安装单独的数据库服务器。

【数据表说明】
1. users - 用户表：存储用户账号信息
2. knowledge_points - 知识点表：存储Python知识点
3. questions - 题目表：存储练习题
4. learning_records - 学习记录表：记录用户学习了哪些知识点
5. practice_records - 练习记录表：记录用户做过的题目
6. wrong_questions - 错题本表：记录用户做错的题目
7. study_statistics - 学习统计表：记录每日学习统计
"""
import sqlite3  # SQLite数据库模块
import os  # 操作系统模块，用于文件操作
import hashlib  # 哈希模块，用于密码加密
from datetime import datetime  # 日期时间模块
from config import DATABASE_PATH, DEFAULT_USER  # 从配置文件导入数据库路径和默认用户


class DatabaseManager:
    """
    数据库管理器类

    【类的作用】
    封装所有数据库操作，提供统一的接口供其他模块调用。

    【设计模式】
    使用单例模式，确保整个程序只有一个数据库管理器实例。
    这样可以避免多个实例同时操作数据库导致的问题。
    """

    def __init__(self, db_path=DATABASE_PATH):
        """
        初始化数据库管理器

        【参数说明】
        - db_path: 数据库文件路径，默认使用配置文件中的路径

        【初始化时做了什么】
        1. 保存数据库路径
        2. 初始化连接和游标为None
        3. 检查数据库文件是否存在
        4. 如果不存在，创建数据库和表
        """
        self.db_path = db_path  # 数据库文件路径
        self.connection = None  # 数据库连接对象
        self.cursor = None  # 数据库游标对象（用于执行SQL）

        # 如果数据库文件不存在，创建数据库和表
        if not os.path.exists(db_path):
            # os.makedirs() 创建目录，exist_ok=True 表示目录已存在时不报错
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.create_database()

    def connect(self):
        """
        连接数据库

        【为什么需要连接】
        就像打电话需要先拨号一样，操作数据库需要先建立连接。

        【连接后做了什么】
        1. 创建sqlite3连接对象
        2. 创建游标对象（用于执行SQL语句）
        3. 设置返回字典格式的行（方便按列名访问数据）

        【返回值】
        - True: 连接成功
        - False: 连接失败
        """
        try:
            # 创建数据库连接
            self.connection = sqlite3.connect(self.db_path)

            # 创建游标对象
            self.cursor = self.connection.cursor()

            # 设置row_factory为sqlite3.Row
            # 这样查询结果可以像字典一样按列名访问
            # 例如: result['username'] 而不是 result[0]
            self.connection.row_factory = sqlite3.Row

            # 重新创建游标（因为修改了row_factory）
            self.cursor = self.connection.cursor()

            return True
        except sqlite3.Error as e:
            # 捕获数据库错误并打印
            print(f"数据库连接失败: {e}")
            return False

    def disconnect(self):
        """
        断开数据库连接

        【为什么需要断开】
        就像打电话结束后要挂断一样，数据库操作完成后应该断开连接。
        这样可以释放资源，避免连接泄露。
        """
        if self.connection:
            self.connection.close()  # 关闭连接
            self.connection = None  # 清空连接对象
            self.cursor = None  # 清空游标对象

    def commit(self):
        """
        提交事务

        【什么是事务】
        事务是一组数据库操作，要么全部成功，要么全部失败。
        例如：转账操作，A账户扣钱和B账户加钱必须同时成功或同时失败。

        【什么时候需要提交】
        执行INSERT、UPDATE、DELETE等修改数据的操作后，需要调用commit()保存。
        """
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """
        回滚事务

        【什么是回滚】
        如果事务执行过程中出现错误，可以撤销所有操作，回到事务开始前的状态。

        【什么时候需要回滚】
        当数据库操作失败时，调用rollback()撤销已执行的操作。
        """
        if self.connection:
            self.connection.rollback()

    def create_database(self):
        """
        创建数据库和所有表

        【表结构说明】
        这个方法创建了系统需要的所有数据表：
        1. users - 用户表
        2. knowledge_points - 知识点表
        3. questions - 题目表
        4. learning_records - 学习记录表
        5. practice_records - 练习记录表
        6. wrong_questions - 错题本表
        7. study_statistics - 学习统计表
        """
        self.connect()  # 连接数据库

        # ==================== 创建用户表 ====================
        # users表存储用户账号信息
        # id: 用户ID（主键，自动递增）
        # username: 用户名（唯一，不能为空）
        # password: 密码（存储加密后的哈希值）
        # nickname: 昵称
        # created_at: 创建时间
        # last_login: 最后登录时间
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nickname TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        # 为用户表增加头像和背景字段（向后兼容）
        # ALTER TABLE ADD COLUMN 用于给已存在的表添加新字段
        # try-except 用于处理字段已存在的情况
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN avatar_path TEXT")
        except Exception:
            pass  # 字段已存在，忽略错误
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN bg_path TEXT")
        except Exception:
            pass  # 字段已存在，忽略错误

        # ==================== 创建知识点表 ====================
        # knowledge_points表存储Python知识点内容
        # id: 知识点ID
        # category: 分类（如"Python基础"、"数据类型"等）
        # title: 标题
        # content: 内容详情
        # code_example: 代码示例
        # difficulty: 难度等级（easy/medium/hard）
        # order_num: 排序号（用于控制显示顺序）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                code_example TEXT,
                difficulty TEXT DEFAULT 'medium',
                order_num INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ==================== 创建题目表 ====================
        # questions表存储练习题
        # id: 题目ID
        # category: 所属分类
        # type: 题目类型（choice/judge/fill/code）
        # question: 题目内容
        # options: 选项（JSON格式，仅选择题有）
        # answer: 正确答案
        # explanation: 题目解析
        # difficulty: 难度等级
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT,
                answer TEXT NOT NULL,
                explanation TEXT,
                difficulty TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ==================== 创建学习记录表 ====================
        # learning_records表记录用户学习知识点的情况
        # user_id: 用户ID（外键，关联users表）
        # knowledge_id: 知识点ID（外键，关联knowledge_points表）
        # study_time: 学习时长（秒）
        # completed: 是否完成（0=未完成，1=已完成）
        # last_study_at: 最后学习时间
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                knowledge_id INTEGER NOT NULL,
                study_time INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                last_study_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (knowledge_id) REFERENCES knowledge_points(id)
            )
        ''')

        # ==================== 创建练习记录表 ====================
        # practice_records表记录用户做题的情况
        # user_id: 用户ID
        # question_id: 题目ID
        # user_answer: 用户的答案
        # is_correct: 是否正确（0=错误，1=正确）
        # submit_time: 提交时间
        # time_spent: 用时（秒）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS practice_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                user_answer TEXT,
                is_correct BOOLEAN,
                submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_spent INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        ''')

        # ==================== 创建错题本表 ====================
        # wrong_questions表记录用户做错的题目
        # user_id: 用户ID
        # question_id: 题目ID
        # wrong_count: 错误次数
        # mastered: 是否已掌握（0=未掌握，1=已掌握）
        # first_wrong_at: 首次错误时间
        # last_wrong_at: 最后错误时间
        # UNIQUE(user_id, question_id): 联合唯一约束，同一用户同一题目只能有一条记录
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wrong_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                wrong_count INTEGER DEFAULT 1,
                mastered BOOLEAN DEFAULT 0,
                first_wrong_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_wrong_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (question_id) REFERENCES questions(id),
                UNIQUE(user_id, question_id)
            )
        ''')

        # ==================== 创建学习统计表 ====================
        # study_statistics表记录每日学习统计
        # user_id: 用户ID
        # study_date: 学习日期
        # total_time: 总学习时长（秒）
        # questions_completed: 完成的题目数
        # questions_correct: 正确的题目数
        # knowledge_learned: 学习的知识点数
        # UNIQUE(user_id, study_date): 联合唯一约束，同一用户同一日期只能有一条记录
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                study_date DATE NOT NULL,
                total_time INTEGER DEFAULT 0,
                questions_completed INTEGER DEFAULT 0,
                questions_correct INTEGER DEFAULT 0,
                knowledge_learned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, study_date)
            )
        ''')

        self.commit()  # 提交所有表的创建操作

        # 初始化默认数据（创建默认用户）
        self.initialize_default_data()

        self.disconnect()  # 断开连接

    def initialize_default_data(self):
        """
        初始化默认数据

        【为什么需要默认数据】
        首次运行程序时，需要有一个默认用户供测试使用。

        【做了什么】
        1. 对默认密码进行MD5加密
        2. 插入默认用户记录
        3. 如果用户已存在，忽略错误
        """
        # 对密码进行MD5加密
        # hashlib.md5() 创建MD5哈希对象
        # .encode() 将字符串转换为字节
        # .hexdigest() 获取16进制的哈希值
        password_hash = hashlib.md5(DEFAULT_USER['password'].encode()).hexdigest()

        try:
            # 插入默认用户
            self.cursor.execute(
                "INSERT INTO users (username, password, nickname) VALUES (?, ?, ?)",
                (DEFAULT_USER['username'], password_hash, DEFAULT_USER['nickname'])
            )
            self.commit()
        except sqlite3.IntegrityError:
            # 用户已存在，忽略错误
            # IntegrityError: 违反唯一约束错误
            pass

    def execute_query(self, query, params=None):
        """
        执行查询语句（SELECT）

        【参数说明】
        - query: SQL查询语句
        - params: 查询参数（可选），用于防止SQL注入

        【返回值】
        - 查询结果列表（每行是一个sqlite3.Row对象）

        【什么是SQL注入】
        SQL注入是一种攻击方式，攻击者通过在输入中插入恶意SQL代码来操纵数据库。
        使用参数化查询（?占位符）可以防止SQL注入。

        【示例】
        result = db_manager.execute_query(
            "SELECT * FROM users WHERE username = ?",
            ("admin",)
        )
        """
        if not self.connection:
            self.connect()

        try:
            if params:
                # 使用参数化查询
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()  # 返回所有查询结果
        except sqlite3.Error as e:
            print(f"查询执行失败: {e}")
            return []

    def execute_update(self, query, params=None):
        """
        执行更新语句（UPDATE/DELETE/INSERT）

        【参数说明】
        - query: SQL更新语句
        - params: 更新参数（可选）

        【返回值】
        - 受影响的行数（0表示没有数据被修改）

        【示例】
        rows = db_manager.execute_update(
            "UPDATE users SET nickname = ? WHERE id = ?",
            ("新昵称", 1)
        )
        """
        if not self.connection:
            self.connect()

        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.commit()  # 自动提交
            return self.cursor.rowcount  # 返回受影响的行数
        except sqlite3.Error as e:
            print(f"更新执行失败: {e}")
            self.rollback()  # 失败时回滚
            return 0

    def insert(self, query, params=None):
        """
        插入数据

        【参数说明】
        - query: SQL插入语句
        - params: 插入参数（可选）

        【返回值】
        - 插入的记录ID（lastrowid）

        【示例】
        user_id = db_manager.insert(
            "INSERT INTO users (username, password, nickname) VALUES (?, ?, ?)",
            ("newuser", "password123", "新用户")
        )
        """
        if not self.connection:
            self.connect()

        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.commit()
            return self.cursor.lastrowid  # 返回新插入记录的ID
        except sqlite3.Error as e:
            print(f"插入执行失败: {e}")
            self.rollback()
            return None

    def get_user_by_username(self, username):
        """
        根据用户名获取用户信息

        【参数说明】
        - username: 用户名

        【返回值】
        - 用户信息字典（如果找到）
        - None（如果未找到）

        【示例】
        user = db_manager.get_user_by_username("admin")
        if user:
            print(user['nickname'])
        """
        query = "SELECT * FROM users WHERE username = ?"
        result = self.execute_query(query, (username,))
        # dict(result[0]) 将sqlite3.Row对象转换为字典
        return dict(result[0]) if result else None

    def verify_user(self, username, password):
        """
        验证用户登录

        【参数说明】
        - username: 用户名
        - password: 密码（明文）

        【返回值】
        - 用户信息字典（如果验证成功）
        - None（如果验证失败）

        【验证流程】
        1. 根据用户名查找用户
        2. 对输入的密码进行MD5加密
        3. 比较加密后的密码是否与数据库中的一致
        4. 如果一致，更新最后登录时间
        """
        # 查找用户
        user = self.get_user_by_username(username)

        if user:
            # 对输入的密码进行MD5加密
            password_hash = hashlib.md5(password.encode()).hexdigest()

            # 比较密码
            if user['password'] == password_hash:
                # 密码正确，更新最后登录时间
                self.execute_update(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.now(), user['id'])
                )
                return user

        return None  # 验证失败

    def update_user_last_login(self, user_id):
        """
        更新用户最后登录时间

        【参数说明】
        - user_id: 用户ID
        """
        self.execute_update(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now(), user_id)
        )


# 全局数据库管理器实例
# 这是单例模式的实现：整个程序只有一个db_manager实例
# 其他模块导入这个实例就可以直接使用数据库功能
db_manager = DatabaseManager()
