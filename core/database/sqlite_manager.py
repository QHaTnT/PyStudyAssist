# -*- coding: utf-8 -*-
"""
SQLite 数据库管理器
使用上下文管理器，统一 bcrypt 密码加密
支持 WAL 模式、连接缓存、性能优化
"""
import sqlite3
import os
import bcrypt
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import config

# 配置日志
logger = logging.getLogger(__name__)


class SQLiteManager:
    """
    SQLite 数据库管理器

    性能优化：
    - WAL 模式：支持并发读写
    - 连接缓存：减少连接开销
    - 批量操作：提高写入性能
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.database.sqlite_path
        self._is_memory = self.db_path == ':memory:'
        self._persistent_conn = None  # 内存数据库的持久连接
        self._ensure_directory()
        self._init_database()
        self._optimize_pragma()

    def _ensure_directory(self):
        """确保数据库目录存在"""
        # 内存数据库不需要创建目录
        if self.db_path == ':memory:':
            return

        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _optimize_pragma(self):
        """优化 SQLite 性能参数"""
        with self.connection() as conn:
            cursor = conn.cursor()
            # 启用 WAL 模式（支持并发读写）
            cursor.execute("PRAGMA journal_mode=WAL")
            # 增加缓存大小（默认 2MB）
            cursor.execute("PRAGMA cache_size=-2000")
            # 启用外键约束
            cursor.execute("PRAGMA foreign_keys=ON")
            # 同步模式（NORMAL 在 WAL 模式下足够安全）
            cursor.execute("PRAGMA synchronous=NORMAL")
            # 临时存储在内存中
            cursor.execute("PRAGMA temp_store=MEMORY")
            logger.info(f"SQLite 性能优化完成: {self.db_path}")

    @contextmanager
    def connection(self):
        """
        数据库连接上下文管理器

        对于内存数据库，使用持久连接以保持数据
        对于文件数据库，每次创建新连接
        """
        if self._is_memory:
            # 内存数据库使用持久连接
            if self._persistent_conn is None:
                self._persistent_conn = sqlite3.connect(':memory:')
                self._persistent_conn.row_factory = sqlite3.Row
            conn = self._persistent_conn
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            # 不关闭持久连接
        else:
            # 文件数据库每次创建新连接
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def execute(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询并返回结果"""
        with self.connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """执行查询并返回单条结果"""
        results = self.execute(query, params)
        return results[0] if results else None

    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新并返回影响行数"""
        with self.connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount

    def execute_insert(self, query: str, params: tuple = None) -> int:
        """执行插入并返回新记录 ID"""
        with self.connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        批量执行操作（提高性能）

        参数：
            query: SQL 语句
            params_list: 参数列表

        返回：总影响行数
        """
        total_affected = 0
        with self.connection() as conn:
            cursor = conn.cursor()
            for params in params_list:
                cursor.execute(query, params)
                total_affected += cursor.rowcount
        return total_affected

    def execute_batch_insert(self, table: str, data_list: List[Dict]) -> int:
        """
        批量插入数据（自动构建 INSERT 语句）

        参数：
            table: 表名
            data_list: 数据列表 [{'col1': val1, 'col2': val2}, ...]

        返回：插入的记录数
        """
        if not data_list:
            return 0

        # 获取列名（从第一条数据）
        columns = list(data_list[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join(columns)

        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

        # 构建参数列表
        params_list = [tuple(row[col] for col in columns) for row in data_list]

        return self.execute_many(query, params_list)

    def _init_database(self):
        """初始化数据库表结构"""
        with self.connection() as conn:
            cursor = conn.cursor()

            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    nickname TEXT,
                    avatar_path TEXT,
                    bg_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')

            # 知识点表
            cursor.execute('''
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

            # 题目表
            cursor.execute('''
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

            # 学习记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    knowledge_id INTEGER NOT NULL,
                    study_time INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0,
                    last_study_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (knowledge_id) REFERENCES knowledge_points(id)
                )
            ''')

            # 练习记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS practice_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    user_answer TEXT,
                    is_correct BOOLEAN,
                    submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    time_spent INTEGER DEFAULT 0,
                    synced BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')

            # 错题本表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wrong_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    wrong_count INTEGER DEFAULT 1,
                    mastered BOOLEAN DEFAULT 0,
                    first_wrong_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_wrong_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced BOOLEAN DEFAULT 0,
                    UNIQUE(user_id, question_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')

            # 考试表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    difficulty TEXT,
                    duration INTEGER NOT NULL,
                    total_score INTEGER NOT NULL,
                    pass_score INTEGER NOT NULL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 考试题目关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    order_num INTEGER DEFAULT 0,
                    FOREIGN KEY (exam_id) REFERENCES exams(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')

            # 考试记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    exam_id INTEGER NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    total_score INTEGER,
                    obtained_score INTEGER,
                    status TEXT DEFAULT 'in_progress',
                    time_spent INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            ''')

            # 考试答题详情表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_record_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    user_answer TEXT,
                    is_correct BOOLEAN,
                    obtained_score INTEGER DEFAULT 0,
                    test_cases_passed INTEGER DEFAULT 0,
                    test_cases_total INTEGER DEFAULT 0,
                    FOREIGN KEY (exam_record_id) REFERENCES exam_records(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')

            # 测试用例表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    input_data TEXT,
                    expected_output TEXT,
                    score INTEGER DEFAULT 1,
                    order_num INTEGER DEFAULT 0,
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')

            # 同步队列表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced BOOLEAN DEFAULT 0
                )
            ''')

            # 迁移旧数据库（添加缺失的列）
            self._migrate_old_database(cursor)

            # 创建索引以优化查询性能
            self._create_indexes(cursor)

            # 初始化默认用户
            self._init_default_user(cursor)

    def _migrate_old_database(self, cursor):
        """迁移旧数据库（添加缺失的列、转换密码格式）"""
        # 为旧表添加 synced 列
        tables_needing_synced = ['learning_records', 'practice_records', 'wrong_questions']
        for table in tables_needing_synced:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN synced BOOLEAN DEFAULT 0")
                logger.info(f"为 {table} 表添加 synced 列")
            except Exception:
                pass  # 列已存在，忽略

        # 为 users 表添加缺失的列
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_path TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN bg_path TEXT")
        except Exception:
            pass

        # 转换旧的 MD5 密码为 bcrypt 格式
        try:
            cursor.execute("SELECT id, username, password FROM users")
            users = cursor.fetchall()
            for user in users:
                user_id, username, password = user
                # 检查是否是 MD5 格式（32位十六进制字符串）
                if len(password) == 32 and all(c in '0123456789abcdef' for c in password):
                    # 这是 MD5 格式，需要转换为 bcrypt
                    # 由于无法反向解密 MD5，我们重置密码为默认密码
                    default_password = '1'  # 默认密码
                    password_hash = bcrypt.hashpw(
                        default_password.encode('utf-8'),
                        bcrypt.gensalt(rounds=config.security.bcrypt_rounds)
                    ).decode('utf-8')
                    cursor.execute(
                        "UPDATE users SET password = ? WHERE id = ?",
                        (password_hash, user_id)
                    )
                    logger.info(f"用户 {username} 的密码已从 MD5 转换为 bcrypt（密码重置为 '1'）")
        except Exception as e:
            logger.warning(f"密码迁移失败: {e}")

    def _create_indexes(self, cursor):
        """创建数据库索引（优化查询性能）"""
        indexes = [
            # 用户表索引
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",

            # 知识点表索引
            "CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_points(category)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_difficulty ON knowledge_points(difficulty)",

            # 题目表索引
            "CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category)",
            "CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(type)",
            "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)",

            # 学习记录索引
            "CREATE INDEX IF NOT EXISTS idx_learning_user ON learning_records(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_knowledge ON learning_records(knowledge_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_synced ON learning_records(synced)",

            # 练习记录索引
            "CREATE INDEX IF NOT EXISTS idx_practice_user ON practice_records(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_practice_question ON practice_records(question_id)",
            "CREATE INDEX IF NOT EXISTS idx_practice_synced ON practice_records(synced)",

            # 错题本索引
            "CREATE INDEX IF NOT EXISTS idx_wrong_user ON wrong_questions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_wrong_question ON wrong_questions(question_id)",
            "CREATE INDEX IF NOT EXISTS idx_wrong_mastered ON wrong_questions(mastered)",
            "CREATE INDEX IF NOT EXISTS idx_wrong_synced ON wrong_questions(synced)",

            # 考试相关索引
            "CREATE INDEX IF NOT EXISTS idx_exam_questions_exam ON exam_questions(exam_id)",
            "CREATE INDEX IF NOT EXISTS idx_exam_questions_question ON exam_questions(question_id)",
            "CREATE INDEX IF NOT EXISTS idx_exam_records_user ON exam_records(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_exam_records_exam ON exam_records(exam_id)",
            "CREATE INDEX IF NOT EXISTS idx_exam_answers_record ON exam_answers(exam_record_id)",

            # 测试用例索引
            "CREATE INDEX IF NOT EXISTS idx_test_cases_question ON test_cases(question_id)",

            # 同步队列索引
            "CREATE INDEX IF NOT EXISTS idx_sync_queue_synced ON sync_queue(synced)",
            "CREATE INDEX IF NOT EXISTS idx_sync_queue_table ON sync_queue(table_name)",
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"创建索引失败: {e}")

        logger.info("数据库索引创建完成")

    def _init_default_user(self, cursor):
        """初始化默认用户"""
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (config.default_username,))
        if cursor.fetchone()[0] == 0:
            password_hash = bcrypt.hashpw(
                config.default_password.encode('utf-8'),
                bcrypt.gensalt(rounds=config.security.bcrypt_rounds)
            ).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, nickname) VALUES (?, ?, ?)",
                (config.default_username, password_hash, 'Python学习者')
            )

    # ==================== 用户操作 ====================

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        return self.execute_one("SELECT * FROM users WHERE username = ?", (username,))

    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """验证用户登录"""
        user = self.get_user_by_username(username)
        if user:
            stored_hash = user['password'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                self.execute_update(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.now(), user['id'])
                )
                return user
        return None

    def create_user(self, username: str, password: str, nickname: str = None) -> Optional[int]:
        """创建新用户"""
        existing = self.get_user_by_username(username)
        if existing:
            return None

        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=config.security.bcrypt_rounds)
        ).decode('utf-8')

        return self.execute_insert(
            "INSERT INTO users (username, password, nickname) VALUES (?, ?, ?)",
            (username, password_hash, nickname or username)
        )

    def update_user(self, user_id: int, **kwargs) -> bool:
        """更新用户信息"""
        allowed_fields = ['nickname', 'avatar_path', 'bg_path']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        set_clause = ', '.join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        return self.execute_update(f"UPDATE users SET {set_clause} WHERE id = ?", tuple(values)) > 0

    # ==================== 知识点操作 ====================

    def get_all_knowledge_points(self) -> List[Dict]:
        """获取所有知识点"""
        return self.execute("SELECT * FROM knowledge_points ORDER BY category, order_num")

    def get_knowledge_by_category(self, category: str) -> List[Dict]:
        """根据分类获取知识点"""
        return self.execute(
            "SELECT * FROM knowledge_points WHERE category = ? ORDER BY order_num",
            (category,)
        )

    def insert_knowledge_point(self, data: Dict) -> int:
        """插入知识点"""
        return self.execute_insert(
            """INSERT INTO knowledge_points (category, title, content, code_example, difficulty, order_num)
            VALUES (:category, :title, :content, :code_example, :difficulty, :order_num)""",
            data
        )

    # ==================== 题目操作 ====================

    def get_all_questions(self) -> List[Dict]:
        """获取所有题目"""
        return self.execute("SELECT * FROM questions ORDER BY category, type")

    def get_questions_by_category(self, category: str) -> List[Dict]:
        """根据分类获取题目"""
        return self.execute("SELECT * FROM questions WHERE category = ?", (category,))

    def insert_question(self, data: Dict) -> int:
        """插入题目"""
        return self.execute_insert(
            """INSERT INTO questions (category, type, question, options, answer, explanation, difficulty)
            VALUES (:category, :type, :question, :options, :answer, :explanation, :difficulty)""",
            data
        )

    # ==================== 学习记录操作 ====================

    def get_user_learning_records(self, user_id: int) -> List[Dict]:
        """获取用户学习记录"""
        return self.execute(
            """SELECT lr.*, kp.title, kp.category
            FROM learning_records lr
            LEFT JOIN knowledge_points kp ON lr.knowledge_id = kp.id
            WHERE lr.user_id = ?
            ORDER BY lr.last_study_at DESC""",
            (user_id,)
        )

    def insert_learning_record(self, data: Dict) -> int:
        """插入学习记录"""
        return self.execute_insert(
            """INSERT INTO learning_records (user_id, knowledge_id, study_time, completed, last_study_at)
            VALUES (:user_id, :knowledge_id, :study_time, :completed, :last_study_at)""",
            data
        )

    def update_learning_record(self, record_id: int, **kwargs) -> bool:
        """更新学习记录"""
        allowed_fields = ['study_time', 'completed', 'last_study_at', 'synced']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        set_clause = ', '.join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [record_id]
        return self.execute_update(f"UPDATE learning_records SET {set_clause} WHERE id = ?", tuple(values)) > 0

    # ==================== 练习记录操作 ====================

    def get_user_practice_records(self, user_id: int, limit: int = None) -> List[Dict]:
        """获取用户练习记录"""
        query = "SELECT * FROM practice_records WHERE user_id = ? ORDER BY submit_time DESC"
        params = [user_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        return self.execute(query, tuple(params))

    def insert_practice_record(self, data: Dict) -> int:
        """插入练习记录"""
        return self.execute_insert(
            """INSERT INTO practice_records (user_id, question_id, user_answer, is_correct, submit_time, time_spent)
            VALUES (:user_id, :question_id, :user_answer, :is_correct, :submit_time, :time_spent)""",
            data
        )

    # ==================== 错题本操作 ====================

    def get_user_wrong_questions(self, user_id: int) -> List[Dict]:
        """获取用户错题"""
        return self.execute(
            """SELECT wq.*, q.question, q.type, q.answer, q.explanation, q.options, q.category
            FROM wrong_questions wq
            LEFT JOIN questions q ON wq.question_id = q.id
            WHERE wq.user_id = ? AND wq.mastered = 0
            ORDER BY wq.last_wrong_at DESC""",
            (user_id,)
        )

    def insert_wrong_question(self, data: Dict) -> int:
        """插入错题记录"""
        return self.execute_insert(
            """INSERT OR REPLACE INTO wrong_questions
            (user_id, question_id, wrong_count, mastered, first_wrong_at, last_wrong_at, synced)
            VALUES (:user_id, :question_id,
                COALESCE((SELECT wrong_count + 1 FROM wrong_questions WHERE user_id = :user_id AND question_id = :question_id), 1),
                0, :first_wrong_at, :last_wrong_at, 0)""",
            data
        )

    def update_wrong_question(self, user_id: int, question_id: int, **kwargs) -> bool:
        """更新错题记录"""
        allowed_fields = ['wrong_count', 'mastered', 'synced']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        set_clause = ', '.join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id, question_id]
        return self.execute_update(
            f"UPDATE wrong_questions SET {set_clause} WHERE user_id = ? AND question_id = ?",
            tuple(values)
        ) > 0

    # ==================== 考试操作 ====================

    def get_all_exams(self) -> List[Dict]:
        """获取所有考试"""
        return self.execute("SELECT * FROM exams ORDER BY created_at DESC")

    def get_exam_questions(self, exam_id: int) -> List[Dict]:
        """获取考试题目"""
        return self.execute(
            """SELECT q.*, eq.score, eq.order_num
            FROM questions q
            JOIN exam_questions eq ON q.id = eq.question_id
            WHERE eq.exam_id = ?
            ORDER BY eq.order_num""",
            (exam_id,)
        )

    def get_user_exam_records(self, user_id: int) -> List[Dict]:
        """获取用户考试记录"""
        return self.execute(
            """SELECT er.*, e.name as exam_name
            FROM exam_records er
            JOIN exams e ON er.exam_id = e.id
            WHERE er.user_id = ?
            ORDER BY er.start_time DESC""",
            (user_id,)
        )

    def insert_exam_record(self, data: Dict) -> int:
        """插入考试记录"""
        return self.execute_insert(
            """INSERT INTO exam_records (user_id, exam_id, total_score, status)
            VALUES (:user_id, :exam_id, :total_score, :status)""",
            data
        )

    def update_exam_record(self, record_id: int, **kwargs) -> bool:
        """更新考试记录"""
        allowed_fields = ['end_time', 'obtained_score', 'status', 'time_spent']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        set_clause = ', '.join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [record_id]
        return self.execute_update(f"UPDATE exam_records SET {set_clause} WHERE id = ?", tuple(values)) > 0

    def insert_exam_answer(self, data: Dict) -> int:
        """插入考试答题详情"""
        return self.execute_insert(
            """INSERT INTO exam_answers (exam_record_id, question_id, user_answer, is_correct, obtained_score)
            VALUES (:exam_record_id, :question_id, :user_answer, :is_correct, :obtained_score)""",
            data
        )

    def get_test_cases(self, question_id: int) -> List[Dict]:
        """获取测试用例"""
        return self.execute(
            "SELECT * FROM test_cases WHERE question_id = ? ORDER BY order_num",
            (question_id,)
        )

    # ==================== 统计操作 ====================

    def get_user_statistics(self, user_id: int) -> Dict:
        """获取用户统计信息"""
        stats = {}

        # 总学习时长
        result = self.execute_one(
            "SELECT COALESCE(SUM(study_time), 0) as total FROM learning_records WHERE user_id = ?",
            (user_id,)
        )
        stats['total_study_time'] = result['total'] if result else 0

        # 完成的知识点数
        result = self.execute_one(
            "SELECT COUNT(*) as count FROM learning_records WHERE user_id = ? AND completed = 1",
            (user_id,)
        )
        stats['completed_knowledge'] = result['count'] if result else 0

        # 总练习题数
        result = self.execute_one(
            "SELECT COUNT(*) as count FROM practice_records WHERE user_id = ?",
            (user_id,)
        )
        stats['total_questions'] = result['count'] if result else 0

        # 正确题数
        result = self.execute_one(
            "SELECT COUNT(*) as count FROM practice_records WHERE user_id = ? AND is_correct = 1",
            (user_id,)
        )
        stats['correct_questions'] = result['count'] if result else 0

        # 错题数
        result = self.execute_one(
            "SELECT COUNT(*) as count FROM wrong_questions WHERE user_id = ? AND mastered = 0",
            (user_id,)
        )
        stats['wrong_questions_count'] = result['count'] if result else 0

        # 计算正确率
        if stats['total_questions'] > 0:
            stats['accuracy'] = round(stats['correct_questions'] / stats['total_questions'] * 100, 2)
        else:
            stats['accuracy'] = 0

        return stats


# 全局实例
db = SQLiteManager()
