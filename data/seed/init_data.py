# -*- coding: utf-8 -*-
"""
种子数据初始化
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.database.sqlite_manager import db
import json


def init_knowledge_points():
    """初始化知识点"""
    knowledge_data = [
        ("Python基础", "Python简介", "Python是一种解释型、面向对象、动态数据类型的高级程序设计语言。",
         "print('Hello, World!')", "easy", 1),
        ("Python基础", "Python的特点", "Python具有简单易学、免费开源、跨平台、面向对象等特点。",
         "import platform\nprint(platform.system())", "easy", 2),
        ("数据类型", "数字类型", "Python支持整数、浮点数、复数三种数字类型。",
         "a = 10\nb = 3.14\nc = 3+4j", "easy", 1),
        ("数据类型", "字符串类型", "字符串是由字符组成的序列，用引号括起来。",
         "s = 'Hello Python'", "easy", 2),
        ("数据类型", "列表类型", "列表是Python中最常用的数据类型，有序可变。",
         "lst = [1, 2, 3]", "medium", 3),
        ("数据类型", "字典类型", "字典是键值对的集合，无序可变。",
         "d = {'name': 'Python', 'version': 3}", "medium", 4),
        ("流程控制", "if语句", "if语句用于条件判断。",
         "x = 10\nif x > 0:\n    print('正数')", "easy", 1),
        ("流程控制", "for循环", "for循环用于遍历序列。",
         "for i in range(5):\n    print(i)", "easy", 2),
        ("流程控制", "while循环", "while循环用于重复执行代码。",
         "i = 0\nwhile i < 5:\n    print(i)\n    i += 1", "easy", 3),
        ("函数", "函数定义", "使用def关键字定义函数。",
         "def greet(name):\n    return f'Hello, {name}!'", "medium", 1),
    ]

    for cat, title, content, code, diff, order in knowledge_data:
        existing = db.execute_one(
            "SELECT id FROM knowledge_points WHERE title = ?", (title,)
        )
        if not existing:
            db.execute_insert(
                """INSERT INTO knowledge_points
                (category, title, content, code_example, difficulty, order_num)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (cat, title, content, code, diff, order)
            )
    print(f"初始化了 {len(knowledge_data)} 个知识点")


def init_questions():
    """初始化题目"""
    question_data = [
        ("Python基础", "choice", "Python是什么类型的语言？",
         json.dumps(["编译型", "解释型", "汇编型", "机器语言"]), "B", "Python是解释型语言", "easy"),
        ("Python基础", "judge", "Python是开源的。",
         None, "正确", "Python是开源软件", "easy"),
        ("数据类型", "choice", "以下哪个是Python的合法变量名？",
         json.dumps(["123name", "_private", "class", "my-var"]), "B", "变量名不能以数字开头，不能是关键字，不能有连字符", "easy"),
        ("流程控制", "choice", "for循环中使用什么函数生成数字序列？",
         json.dumps(["range()", "list()", "seq()", "num()"]), "A", "range()函数用于生成数字序列", "easy"),
        ("函数", "fill", "定义函数使用关键字____。",
         None, "def", "使用def关键字定义函数", "easy"),
    ]

    for cat, q_type, question, options, answer, explanation, diff in question_data:
        existing = db.execute_one(
            "SELECT id FROM questions WHERE question = ?", (question,)
        )
        if not existing:
            db.execute_insert(
                """INSERT INTO questions
                (category, type, question, options, answer, explanation, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (cat, q_type, question, options, answer, explanation, diff)
            )
    print(f"初始化了 {len(question_data)} 道题目")


if __name__ == '__main__':
    print("开始初始化数据...")
    init_knowledge_points()
    init_questions()
    print("数据初始化完成！")
