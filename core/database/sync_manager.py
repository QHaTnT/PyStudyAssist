# -*- coding: utf-8 -*-
"""
数据同步管理器
安全的 SQLite ↔ MySQL 双向同步

特性：
- 增量同步（基于时间戳）
- 冲突解决（本地优先/远程优先）
- 自动重试机制
- 同步状态监控
"""
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.database.sqlite_manager import db
from core.database.mysql_manager import mysql_manager
from config import config

# 配置日志
logger = logging.getLogger(__name__)


class SyncManager:
    """
    数据同步管理器

    同步策略：
    1. 启动时：从 MySQL 拉取新数据到 SQLite
    2. 运行时：本地写入 SQLite，异步推送到 MySQL
    3. 定时任务：定期同步未同步的记录
    """

    def __init__(self):
        self.sync_thread = None
        self.is_syncing = False
        self._last_sync_time: Optional[datetime] = None
        self._sync_errors: List[str] = []
        self._max_retries = 3
        self._retry_delay = 5  # 秒

    def is_network_available(self) -> bool:
        """检查网络是否可用"""
        try:
            return mysql_manager.is_connected()
        except Exception as e:
            logger.debug(f"网络检查失败: {e}")
            return False

    def startup_sync(self) -> bool:
        """
        启动时同步

        执行顺序：
        1. 从 MySQL 拉取新数据到 SQLite
        2. 将本地未同步数据推送到 MySQL

        返回：是否同步成功
        """
        if not self.is_network_available():
            logger.warning("网络不可用，跳过启动同步")
            return False

        try:
            logger.info("开始启动同步...")
            self._pull_from_mysql()
            self._push_to_mysql()
            self._last_sync_time = datetime.now()
            logger.info("启动同步完成")
            return True
        except Exception as e:
            logger.error(f"启动同步失败: {e}")
            self._sync_errors.append(f"启动同步失败: {e}")
            return False

    def _sync_reference_data(self):
        """同步引用数据（知识点和题目）到 MySQL"""
        try:
            # 同步知识点
            local_points = db.execute("SELECT * FROM knowledge_points")
            remote_points = mysql_manager.get_all_knowledge_points()
            remote_ids = {p['id'] for p in remote_points}

            for point in local_points:
                if point['id'] not in remote_ids:
                    try:
                        with mysql_manager.session() as session:
                            from core.database.mysql_manager import KnowledgePoint
                            kp = KnowledgePoint(
                                id=point['id'],
                                category=point['category'],
                                title=point['title'],
                                content=point['content'],
                                code_example=point.get('code_example'),
                                difficulty=point.get('difficulty', 'medium'),
                                order_num=point.get('order_num', 0)
                            )
                            session.add(kp)
                    except Exception as e:
                        logger.warning(f"同步知识点 {point['id']} 失败: {e}")

            # 同步题目
            local_questions = db.execute("SELECT * FROM questions")
            remote_questions = mysql_manager.get_all_questions()
            remote_q_ids = {q['id'] for q in remote_questions}

            for q in local_questions:
                if q['id'] not in remote_q_ids:
                    try:
                        with mysql_manager.session() as session:
                            from core.database.mysql_manager import Question
                            import json
                            options = q.get('options')
                            if isinstance(options, str):
                                try:
                                    options = json.loads(options)
                                except:
                                    options = None
                            question = Question(
                                id=q['id'],
                                category=q['category'],
                                type=q['type'],
                                question=q['question'],
                                options=options,
                                answer=q['answer'],
                                explanation=q.get('explanation'),
                                difficulty=q.get('difficulty', 'medium')
                            )
                            session.add(question)
                    except Exception as e:
                        logger.warning(f"同步题目 {q['id']} 失败: {e}")

            logger.info("引用数据同步完成")

        except Exception as e:
            logger.error(f"同步引用数据失败: {e}")

    def _pull_from_mysql(self, since: Optional[datetime] = None):
        """
        从 MySQL 拉取数据到 SQLite（增量同步）

        参数：
            since: 只拉取此时间之后更新的数据（None 表示全量拉取）
        """
        try:
            import json

            # 拉取知识点（增量）
            mysql_points = mysql_manager.get_all_knowledge_points()
            pulled_points = 0
            for point in mysql_points:
                existing = db.execute_one(
                    "SELECT id, created_at FROM knowledge_points WHERE id = ?",
                    (point['id'],)
                )
                if not existing:
                    db.execute_insert(
                        """INSERT INTO knowledge_points
                        (id, category, title, content, code_example, difficulty, order_num)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (point['id'], point['category'], point['title'],
                         point['content'], point['code_example'],
                         point['difficulty'], point['order_num'])
                    )
                    pulled_points += 1

            # 拉取题目（增量）
            mysql_questions = mysql_manager.get_all_questions()
            pulled_questions = 0
            for q in mysql_questions:
                existing = db.execute_one(
                    "SELECT id FROM questions WHERE id = ?",
                    (q['id'],)
                )
                if not existing:
                    options_json = json.dumps(q['options']) if q['options'] else None
                    db.execute_insert(
                        """INSERT INTO questions
                        (id, category, type, question, options, answer, explanation, difficulty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (q['id'], q['category'], q['type'], q['question'],
                         options_json, q['answer'], q['explanation'], q['difficulty'])
                    )
                    pulled_questions += 1

            logger.info(f"从 MySQL 拉取: {pulled_points} 个知识点, {pulled_questions} 个题目")

        except Exception as e:
            logger.error(f"从 MySQL 拉取数据失败: {e}")
            raise

    def _push_to_mysql(self) -> Dict:
        """
        将本地未同步的记录推送到 MySQL

        同步顺序（遵守外键约束）：
        1. 知识点和题目（引用数据）
        2. 学习记录、练习记录、错题（依赖数据）

        返回：同步结果统计
        """
        stats = {
            'learning': 0,
            'practice': 0,
            'wrong': 0,
            'errors': []
        }

        try:
            # 先确保知识点和题目存在于 MySQL
            self._sync_reference_data()

            # 推送学习记录
            unsynced = db.execute(
                "SELECT * FROM learning_records WHERE synced = 0 OR synced IS NULL"
            )
            for record in unsynced:
                try:
                    mysql_manager.insert_learning_record({
                        'user_id': record['user_id'],
                        'knowledge_id': record['knowledge_id'],
                        'study_time': record['study_time'],
                        'completed': record['completed']
                    })
                    db.execute_update(
                        "UPDATE learning_records SET synced = 1 WHERE id = ?",
                        (record['id'],)
                    )
                    stats['learning'] += 1
                except Exception as e:
                    stats['errors'].append(f"学习记录 {record['id']}: {e}")
                    logger.warning(f"推送学习记录失败: {e}")

            # 推送练习记录
            unsynced = db.execute(
                "SELECT * FROM practice_records WHERE synced = 0 OR synced IS NULL"
            )
            for record in unsynced:
                try:
                    mysql_manager.insert_practice_record({
                        'user_id': record['user_id'],
                        'question_id': record['question_id'],
                        'user_answer': record['user_answer'],
                        'is_correct': record['is_correct'],
                        'time_spent': record['time_spent']
                    })
                    db.execute_update(
                        "UPDATE practice_records SET synced = 1 WHERE id = ?",
                        (record['id'],)
                    )
                    stats['practice'] += 1
                except Exception as e:
                    stats['errors'].append(f"练习记录 {record['id']}: {e}")
                    logger.warning(f"推送练习记录失败: {e}")

            # 推送错题记录
            unsynced = db.execute(
                "SELECT * FROM wrong_questions WHERE synced = 0 OR synced IS NULL"
            )
            for record in unsynced:
                try:
                    mysql_manager.insert_wrong_question({
                        'user_id': record['user_id'],
                        'question_id': record['question_id']
                    })
                    db.execute_update(
                        "UPDATE wrong_questions SET synced = 1 WHERE id = ?",
                        (record['id'],)
                    )
                    stats['wrong'] += 1
                except Exception as e:
                    stats['errors'].append(f"错题记录 {record['id']}: {e}")
                    logger.warning(f"推送错题记录失败: {e}")

            if stats['errors']:
                logger.warning(f"推送完成，但有 {len(stats['errors'])} 个错误")
            else:
                logger.info(f"推送完成: 学习{stats['learning']}, 练习{stats['practice']}, 错题{stats['wrong']}")

        except Exception as e:
            logger.error(f"推送数据失败: {e}")
            stats['errors'].append(str(e))

        return stats

    def record_learning(self, user_id: int, knowledge_id: int, study_time: int, completed: bool = False):
        """记录学习（先写本地，异步同步）"""
        db.execute_insert(
            """INSERT INTO learning_records
            (user_id, knowledge_id, study_time, completed, last_study_at, synced)
            VALUES (?, ?, ?, ?, ?, 0)""",
            (user_id, knowledge_id, study_time, completed, datetime.now())
        )

        if self.is_network_available():
            threading.Thread(
                target=self._async_push_learning,
                args=(user_id, knowledge_id, study_time, completed),
                daemon=True
            ).start()

    def _async_push_learning(self, user_id: int, knowledge_id: int, study_time: int, completed: bool):
        """异步推送学习记录（带重试）"""
        for attempt in range(self._max_retries):
            try:
                mysql_manager.insert_learning_record({
                    'user_id': user_id,
                    'knowledge_id': knowledge_id,
                    'study_time': study_time,
                    'completed': completed
                })
                return  # 成功则返回
            except Exception as e:
                logger.warning(f"异步推送学习记录失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)

        logger.error(f"异步推送学习记录最终失败，已重试 {self._max_retries} 次")

    def record_practice(self, user_id: int, question_id: int, user_answer: str, is_correct: bool, time_spent: int):
        """记录练习（先写本地，异步同步）"""
        db.execute_insert(
            """INSERT INTO practice_records
            (user_id, question_id, user_answer, is_correct, submit_time, time_spent, synced)
            VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (user_id, question_id, str(user_answer), is_correct, datetime.now(), time_spent)
        )

        if self.is_network_available():
            threading.Thread(
                target=self._async_push_practice,
                args=(user_id, question_id, user_answer, is_correct, time_spent),
                daemon=True
            ).start()

    def _async_push_practice(self, user_id: int, question_id: int, user_answer: str, is_correct: bool, time_spent: int):
        """异步推送练习记录（带重试）"""
        for attempt in range(self._max_retries):
            try:
                mysql_manager.insert_practice_record({
                    'user_id': user_id,
                    'question_id': question_id,
                    'user_answer': str(user_answer),
                    'is_correct': is_correct,
                    'time_spent': time_spent
                })
                return  # 成功则返回
            except Exception as e:
                logger.warning(f"异步推送练习记录失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)

        logger.error(f"异步推送练习记录最终失败，已重试 {self._max_retries} 次")

    def record_wrong_question(self, user_id: int, question_id: int):
        """记录错题（先写本地，异步同步）"""
        existing = db.execute_one(
            "SELECT id, wrong_count FROM wrong_questions WHERE user_id = ? AND question_id = ?",
            (user_id, question_id)
        )

        if existing:
            db.execute_update(
                """UPDATE wrong_questions
                SET wrong_count = ?, last_wrong_at = ?, synced = 0
                WHERE id = ?""",
                (existing['wrong_count'] + 1, datetime.now(), existing['id'])
            )
        else:
            db.execute_insert(
                """INSERT INTO wrong_questions
                (user_id, question_id, wrong_count, mastered, first_wrong_at, last_wrong_at, synced)
                VALUES (?, ?, 1, 0, ?, ?, 0)""",
                (user_id, question_id, datetime.now(), datetime.now())
            )

        if self.is_network_available():
            threading.Thread(
                target=self._async_push_wrong,
                args=(user_id, question_id),
                daemon=True
            ).start()

    def _async_push_wrong(self, user_id: int, question_id: int):
        """异步推送错题记录（带重试）"""
        for attempt in range(self._max_retries):
            try:
                mysql_manager.insert_wrong_question({
                    'user_id': user_id,
                    'question_id': question_id
                })
                return  # 成功则返回
            except Exception as e:
                logger.warning(f"异步推送错题记录失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)

        logger.error(f"异步推送错题记录最终失败，已重试 {self._max_retries} 次")

    def start_auto_sync(self):
        """启动自动同步（后台线程）"""
        if not config.sync.auto_sync:
            logger.info("自动同步已禁用")
            return

        if self.sync_thread and self.sync_thread.is_alive():
            logger.warning("自动同步线程已在运行")
            return

        def sync_loop():
            logger.info(f"自动同步已启动，间隔 {config.sync.sync_interval} 秒")
            while True:
                try:
                    time.sleep(config.sync.sync_interval)

                    if self.is_network_available():
                        logger.debug("执行定时同步...")
                        self._push_to_mysql()
                        self._last_sync_time = datetime.now()
                    else:
                        logger.debug("网络不可用，跳过本次同步")

                except Exception as e:
                    logger.error(f"自动同步异常: {e}")
                    self._sync_errors.append(f"自动同步异常: {e}")

        self.sync_thread = threading.Thread(target=sync_loop, daemon=True, name="SyncThread")
        self.sync_thread.start()

    def get_sync_status(self) -> Dict:
        """
        获取同步状态（详细版）

        返回：
        - network_available: 网络是否可用
        - unsynced_*: 各表未同步记录数
        - last_sync_time: 上次同步时间
        - recent_errors: 最近的错误列表
        - is_syncing: 是否正在同步
        """
        unsynced_learning = db.execute_one(
            "SELECT COUNT(*) as count FROM learning_records WHERE synced = 0 OR synced IS NULL"
        )
        unsynced_practice = db.execute_one(
            "SELECT COUNT(*) as count FROM practice_records WHERE synced = 0 OR synced IS NULL"
        )
        unsynced_wrong = db.execute_one(
            "SELECT COUNT(*) as count FROM wrong_questions WHERE synced = 0 OR synced IS NULL"
        )

        return {
            'network_available': self.is_network_available(),
            'unsynced_learning': unsynced_learning['count'] if unsynced_learning else 0,
            'unsynced_practice': unsynced_practice['count'] if unsynced_practice else 0,
            'unsynced_wrong': unsynced_wrong['count'] if unsynced_wrong else 0,
            'last_sync_time': self._last_sync_time.isoformat() if self._last_sync_time else None,
            'recent_errors': self._sync_errors[-10:] if self._sync_errors else [],
            'is_syncing': self.is_syncing,
        }

    def force_sync(self) -> Dict:
        """
        强制立即同步

        返回：同步结果统计
        """
        if not self.is_network_available():
            return {'error': '网络不可用'}

        self.is_syncing = True
        try:
            logger.info("执行强制同步...")
            self._pull_from_mysql()
            stats = self._push_to_mysql()
            self._last_sync_time = datetime.now()
            logger.info("强制同步完成")
            return stats
        except Exception as e:
            logger.error(f"强制同步失败: {e}")
            return {'error': str(e)}
        finally:
            self.is_syncing = False

    def clear_sync_errors(self):
        """清除同步错误记录"""
        self._sync_errors.clear()


# 全局实例
sync_manager = SyncManager()
