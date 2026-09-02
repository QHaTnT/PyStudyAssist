# -*- coding: utf-8 -*-
"""
考试服务
处理考试流程、评分、记录
"""
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.database.sqlite_manager import db
from utils.code_executor import CodeExecutor
from config import config


class ExamService:
    """考试服务"""

    def __init__(self):
        self.code_executor = CodeExecutor()

    def get_all_exams(self) -> List[Dict]:
        """获取所有考试"""
        return db.get_all_exams()

    def get_exam_questions(self, exam_id: int) -> List[Dict]:
        """获取考试题目"""
        return db.get_exam_questions(exam_id)

    def get_user_exam_records(self, user_id: int) -> List[Dict]:
        """获取用户考试记录"""
        return db.get_user_exam_records(user_id)

    def start_exam(self, user_id: int, exam_id: int) -> int:
        """开始考试，返回考试记录 ID"""
        exam = db.execute_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
        if not exam:
            raise ValueError("考试不存在")

        return db.insert_exam_record({
            'user_id': user_id,
            'exam_id': exam_id,
            'total_score': exam['total_score'],
            'status': 'in_progress'
        })

    def grade_question(self, exam_record_id: int, question: Dict, user_answer: str) -> int:
        """
        评分单个题目
        :return: 得分
        """
        question_id = question['id']
        score = question['score']

        if question['type'] == 'code':
            # 编程题使用测试点评分
            obtained_score = self._grade_coding_question(question, user_answer)
        else:
            # 其他题型直接比对答案
            if question['type'] == 'fill':
                is_correct = user_answer.strip() == question['answer'].strip()
            else:
                is_correct = user_answer == question['answer']
            obtained_score = score if is_correct else 0

        # 记录答题详情
        db.insert_exam_answer({
            'exam_record_id': exam_record_id,
            'question_id': question_id,
            'user_answer': user_answer,
            'is_correct': obtained_score > 0,
            'obtained_score': obtained_score
        })

        return obtained_score

    def _grade_coding_question(self, question: Dict, user_code: str) -> int:
        """编程题评分（PTA 风格）"""
        test_cases = db.get_test_cases(question['id'])

        if not test_cases:
            # 没有测试点，使用标准答案比对
            return question['score'] if user_code.strip() == question['answer'].strip() else 0

        # 并发执行测试点
        passed_count = 0
        total_score = 0

        with ThreadPoolExecutor(max_workers=min(len(test_cases), 5)) as executor:
            futures = {}
            for i, tc in enumerate(test_cases):
                future = executor.submit(
                    self._run_test_case,
                    user_code,
                    tc.get('input_data', ''),
                    tc.get('expected_output', '')
                )
                futures[future] = i

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    passed = future.result()
                except:
                    passed = False

                if passed:
                    passed_count += 1
                    total_score += test_cases[idx].get('score', 1)

        return total_score

    def _run_test_case(self, code: str, input_data: str, expected_output: str) -> bool:
        """运行单个测试点"""
        test_code = f"""
import sys
from io import StringIO
sys.stdin = StringIO('''{input_data}''')
{code}
"""
        success, output, error = self.code_executor.execute(test_code)
        if success:
            return output.strip() == expected_output.strip()
        return False

    def submit_exam(self, exam_record_id: int, answers: Dict[int, str],
                   questions: List[Dict], start_time: float) -> Dict:
        """
        提交考试
        :return: 考试结果
        """
        total_score = 0
        for question in questions:
            question_id = question['id']
            user_answer = answers.get(question_id, '')
            score = self.grade_question(exam_record_id, question, user_answer)
            total_score += score

        # 计算用时
        time_spent = int((datetime.now().timestamp() - start_time) / 60)

        # 获取考试信息
        exam_record = db.execute_one("SELECT * FROM exam_records WHERE id = ?", (exam_record_id,))
        exam = db.execute_one("SELECT * FROM exams WHERE id = ?", (exam_record['exam_id'],))

        # 更新考试记录
        db.update_exam_record(
            exam_record_id,
            end_time=datetime.now(),
            obtained_score=total_score,
            status='completed',
            time_spent=time_spent
        )

        return {
            'total_score': exam['total_score'],
            'obtained_score': total_score,
            'time_spent': time_spent,
            'passed': total_score >= exam['pass_score']
        }


# 全局实例
exam_service = ExamService()
