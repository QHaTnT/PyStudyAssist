# -*- coding: utf-8 -*-
"""
考试数据初始化
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.database.sqlite_manager import db


def init_exams():
    """初始化考试数据"""
    exams = [
        ("Python基础测试", "测试Python基础知识掌握程度", "easy", 30, 100, 60, "Python基础"),
        ("Python进阶测试", "测试Python进阶知识掌握程度", "medium", 45, 100, 60, "数据类型"),
    ]

    for name, desc, diff, duration, total, pass_score, category in exams:
        existing = db.execute_one("SELECT id FROM exams WHERE name = ?", (name,))
        if not existing:
            db.execute_insert(
                """INSERT INTO exams (name, description, difficulty, duration, total_score, pass_score, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, desc, diff, duration, total, pass_score, category)
            )
    print(f"初始化了 {len(exams)} 场考试")


def init_exam_questions():
    """初始化考试题目关联"""
    # 获取考试和题目
    exams = db.execute("SELECT id FROM exams")
    questions = db.execute("SELECT id, category FROM questions")

    if not exams or not questions:
        print("没有考试或题目数据")
        return

    # 为每场考试分配题目
    for exam in exams:
        exam_id = exam['id']
        existing = db.execute_one(
            "SELECT COUNT(*) as count FROM exam_questions WHERE exam_id = ?",
            (exam_id,)
        )
        if existing['count'] == 0:
            # 分配该分类的题目
            exam_data = db.execute_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
            category = exam_data['category']

            category_questions = [q for q in questions if q['category'] == category]
            if not category_questions:
                category_questions = questions[:5]  # 如果没有匹配的，取前5题

            for i, q in enumerate(category_questions[:5]):  # 每场考试最多5题
                db.execute_insert(
                    "INSERT INTO exam_questions (exam_id, question_id, score, order_num) VALUES (?, ?, ?, ?)",
                    (exam_id, q['id'], 20, i + 1)  # 每题20分
                )
    print("初始化了考试题目关联")


if __name__ == '__main__':
    print("开始初始化考试数据...")
    init_exams()
    init_exam_questions()
    print("考试数据初始化完成！")
