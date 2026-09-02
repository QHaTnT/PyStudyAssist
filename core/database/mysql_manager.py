# -*- coding: utf-8 -*-
"""
MySQL 数据库管理器
使用 SQLAlchemy ORM + 连接池，统一 bcrypt 密码加密
支持健康检查、自动重连、连接池监控
"""
import bcrypt
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, Dict, List
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from config import config

# 配置日志
logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    """用户表模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(60), nullable=False)  # bcrypt hash
    nickname = Column(String(100))
    avatar_path = Column(String(255))
    bg_path = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.now)
    last_login = Column(TIMESTAMP)


class KnowledgePoint(Base):
    """知识点表模型"""
    __tablename__ = 'knowledge_points'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    code_example = Column(Text)
    difficulty = Column(String(10), default='medium')
    order_num = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.now)


class Question(Base):
    """题目表模型"""
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON)
    answer = Column(Text, nullable=False)
    explanation = Column(Text)
    difficulty = Column(String(10), default='medium')
    created_at = Column(TIMESTAMP, default=datetime.now)


class LearningRecord(Base):
    """学习记录表模型"""
    __tablename__ = 'learning_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    knowledge_id = Column(Integer, ForeignKey('knowledge_points.id'), nullable=False)
    study_time = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    last_study_at = Column(TIMESTAMP, default=datetime.now)
    synced = Column(Boolean, default=False)


class PracticeRecord(Base):
    """练习记录表模型"""
    __tablename__ = 'practice_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    submit_time = Column(TIMESTAMP, default=datetime.now)
    time_spent = Column(Integer, default=0)
    synced = Column(Boolean, default=False)


class WrongQuestion(Base):
    """错题本表模型"""
    __tablename__ = 'wrong_questions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    wrong_count = Column(Integer, default=1)
    mastered = Column(Boolean, default=False)
    first_wrong_at = Column(TIMESTAMP, default=datetime.now)
    last_wrong_at = Column(TIMESTAMP, default=datetime.now)
    synced = Column(Boolean, default=False)


class MySQLManager:
    """
    MySQL 数据库管理器

    连接池配置说明：
    - pool_size: 核心连接数（默认5）
    - max_overflow: 超出核心连接数的临时连接（默认10）
    - pool_timeout: 获取连接的超时时间（秒）
    - pool_recycle: 连接回收时间（秒），防止MySQL主动断开
    - pool_pre_ping: 使用前检测连接是否有效
    """

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._is_connected = False
        self._init_engine()

    def _init_engine(self):
        """初始化数据库引擎（带连接池优化）"""
        try:
            db_url = (
                f"mysql+pymysql://{config.database.mysql_user}:{config.database.mysql_password}"
                f"@{config.database.mysql_host}:{config.database.mysql_port}"
                f"/{config.database.mysql_database}?charset={config.database.mysql_charset}"
            )

            # 连接池配置
            pool_options = {
                'pool_size': 5,           # 核心连接数
                'max_overflow': 10,       # 最大溢出连接数
                'pool_timeout': 30,       # 获取连接超时（秒）
                'pool_recycle': 1800,     # 连接回收时间（秒），防止MySQL超时断开
                'pool_pre_ping': True,    # 使用前ping检测连接有效性
                'poolclass': QueuePool,   # 使用队列池
                'echo': False,            # 不打印SQL语句（生产环境）
            }

            self.engine = create_engine(db_url, **pool_options)
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )

            # 测试连接
            self._test_connection()
            logger.info(f"MySQL 连接池初始化成功: {config.database.mysql_host}:{config.database.mysql_port}")

        except Exception as e:
            logger.error(f"MySQL 连接池初始化失败: {e}")
            self._is_connected = False

    def _test_connection(self):
        """测试数据库连接"""
        # 如果没有配置密码，跳过连接测试
        if not config.database.mysql_password:
            logger.info("MySQL 密码未配置，跳过连接")
            self._is_connected = False
            return

        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._is_connected = True
        except Exception as e:
            # 静默处理连接失败，不打印警告
            self._is_connected = False

    @contextmanager
    def session(self):
        """
        获取数据库会话（上下文管理器）

        自动处理事务提交、回滚和连接释放
        """
        if self.SessionLocal is None:
            raise RuntimeError("MySQL 连接未初始化")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"数据库操作失败，已回滚: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"未知错误，已回滚: {e}")
            raise
        finally:
            session.close()

    def is_connected(self) -> bool:
        """检查是否连接成功"""
        if self.engine is None:
            return False

        # 如果之前测试过且成功，直接返回
        if self._is_connected:
            return True

        # 重新测试连接
        try:
            self._test_connection()
            return self._is_connected
        except Exception:
            return False

    def get_pool_status(self) -> Dict:
        """
        获取连接池状态（用于监控和调试）

        返回：
        - pool_size: 当前池大小
        - checked_in: 空闲连接数
        - checked_out: 已借出连接数
        - overflow: 溢出连接数
        """
        if self.engine is None:
            return {'error': '引擎未初始化'}

        pool = self.engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
        }

    def reconnect(self):
        """重新连接数据库"""
        logger.info("尝试重新连接 MySQL...")
        self._init_engine()

    # ==================== 用户操作 ====================

    def create_user(self, username: str, password: str, nickname: str = None) -> int:
        """创建用户"""
        with self.session() as session:
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt(rounds=config.security.bcrypt_rounds)
            ).decode('utf-8')

            user = User(
                username=username,
                password_hash=password_hash,
                nickname=nickname or username
            )
            session.add(user)
            session.flush()
            return user.id

    def get_user_by_username(self, username: str):
        """根据用户名获取用户"""
        with self.session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'password': user.password_hash,
                    'nickname': user.nickname,
                    'avatar_path': user.avatar_path,
                    'bg_path': user.bg_path
                }
            return None

    def verify_user(self, username: str, password: str):
        """验证用户登录"""
        with self.session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                user.last_login = datetime.now()
                return {
                    'id': user.id,
                    'username': user.username,
                    'password': user.password_hash,
                    'nickname': user.nickname
                }
            return None

    # ==================== 知识点操作 ====================

    def get_all_knowledge_points(self) -> list:
        """获取所有知识点"""
        with self.session() as session:
            points = session.query(KnowledgePoint).all()
            return [
                {
                    'id': p.id,
                    'category': p.category,
                    'title': p.title,
                    'content': p.content,
                    'code_example': p.code_example,
                    'difficulty': p.difficulty,
                    'order_num': p.order_num
                }
                for p in points
            ]

    # ==================== 题目操作 ====================

    def get_all_questions(self) -> list:
        """获取所有题目"""
        with self.session() as session:
            questions = session.query(Question).all()
            return [
                {
                    'id': q.id,
                    'category': q.category,
                    'type': q.type,
                    'question': q.question,
                    'options': q.options,
                    'answer': q.answer,
                    'explanation': q.explanation,
                    'difficulty': q.difficulty
                }
                for q in questions
            ]

    # ==================== 学习记录操作 ====================

    def insert_learning_record(self, data: dict) -> int:
        """插入学习记录"""
        with self.session() as session:
            record = LearningRecord(
                user_id=data['user_id'],
                knowledge_id=data['knowledge_id'],
                study_time=data.get('study_time', 0),
                completed=data.get('completed', False),
                synced=True
            )
            session.add(record)
            session.flush()
            return record.id

    # ==================== 练习记录操作 ====================

    def insert_practice_record(self, data: dict) -> int:
        """插入练习记录"""
        with self.session() as session:
            record = PracticeRecord(
                user_id=data['user_id'],
                question_id=data['question_id'],
                user_answer=str(data.get('user_answer', '')),
                is_correct=data.get('is_correct', False),
                time_spent=data.get('time_spent', 0),
                synced=True
            )
            session.add(record)
            session.flush()
            return record.id

    # ==================== 错题本操作 ====================

    def insert_wrong_question(self, data: dict) -> int:
        """插入错题记录"""
        with self.session() as session:
            # 检查是否已存在
            existing = session.query(WrongQuestion).filter(
                WrongQuestion.user_id == data['user_id'],
                WrongQuestion.question_id == data['question_id']
            ).first()

            if existing:
                existing.wrong_count += 1
                existing.last_wrong_at = datetime.now()
                existing.synced = True
                return existing.id
            else:
                record = WrongQuestion(
                    user_id=data['user_id'],
                    question_id=data['question_id'],
                    wrong_count=1,
                    synced=True
                )
                session.add(record)
                session.flush()
                return record.id


# 全局实例
mysql_manager = MySQLManager()
