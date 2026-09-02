# -*- coding: utf-8 -*-
"""
多线程沙箱代码执行器

特性：
- QThread 异步执行（UI 不卡顿）
- 5秒超时保护（可配置）
- 全局异常捕获
- PTA 风格测试点并发验证
- 资源限制保护
"""
import sys
import io
import subprocess
import tempfile
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import QThread, pyqtSignal
from config import config

# 配置日志
logger = logging.getLogger(__name__)


class CodeExecutionThread(QThread):
    """
    代码执行线程（带超时保护）

    特性：
    - 子进程隔离执行
    - 超时强制终止
    - 全局异常捕获
    - 资源清理
    """
    finished = pyqtSignal(bool, str, str)  # success, output, error

    def __init__(self, code, timeout=None):
        super().__init__()
        self.code = code
        self.timeout = timeout or config.security.code_timeout
        self.process = None
        self._is_running = True

    def run(self):
        """
        执行代码（带超时保护）

        执行流程：
        1. 创建临时文件
        2. 启动子进程执行
        3. 等待完成或超时
        4. 清理资源
        """
        temp_path = None
        try:
            # 创建临时文件执行代码
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as f:
                f.write(self.code)
                temp_path = f.name

            # 使用 subprocess 执行，隔离环境
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                [sys.executable, temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creation_flags
            )

            # 超时等待
            stdout, stderr = self.process.communicate(timeout=self.timeout)

            # 检查是否已被停止
            if not self._is_running:
                self.finished.emit(False, "", "执行已被用户取消")
                return

            if self.process.returncode == 0:
                self.finished.emit(True, stdout, "")
            else:
                self.finished.emit(False, stdout, stderr)

        except subprocess.TimeoutExpired:
            # 超时处理
            if self.process:
                self.process.kill()
                self.process.wait()
            self.finished.emit(False, "", f"执行超时（超过 {self.timeout} 秒）")
            logger.warning(f"代码执行超时: {self.timeout}秒")

        except Exception as e:
            # 全局异常捕获
            self.finished.emit(False, "", f"执行异常: {str(e)}")
            logger.error(f"代码执行异常: {e}")

        finally:
            # 清理临时文件
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    def stop(self):
        """强制停止执行"""
        self._is_running = False
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
                self.process.wait(timeout=1)
            except Exception as e:
                logger.warning(f"停止进程失败: {e}")


class PTATestRunner(QThread):
    """
    PTA 风格测试点并发验证

    特性：
    - 并发执行多个测试点
    - 单个测试点超时保护
    - 实时进度反馈
    - 自动评分计算
    """
    test_completed = pyqtSignal(int, bool, str)  # test_index, passed, output
    all_completed = pyqtSignal(float)  # score (0-100)
    progress_updated = pyqtSignal(int, int)  # current, total

    def __init__(self, code, test_cases, timeout=None):
        super().__init__()
        self.code = code
        self.test_cases = test_cases  # [{input: ..., expected: ..., score: ...}]
        self.timeout = timeout or config.security.code_timeout
        self.results = []
        self._is_running = True

    def run(self):
        """
        并发执行所有测试点

        执行流程：
        1. 使用线程池并发执行测试点
        2. 收集结果并发送进度信号
        3. 计算总分并发送完成信号
        """
        self.results = []
        total_tests = len(self.test_cases)
        completed_tests = 0

        # 限制并发数，避免资源耗尽
        max_workers = min(total_tests, 5)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, test in enumerate(self.test_cases):
                # 检查是否应该停止
                if not self._is_running:
                    break

                future = executor.submit(self._run_single_test, self.code, test)
                futures[future] = i

            for future in as_completed(futures):
                # 检查是否应该停止
                if not self._is_running:
                    break

                idx = futures[future]
                try:
                    passed, output = future.result(timeout=self.timeout + 1)
                except Exception as e:
                    passed, output = False, str(e)

                self.results.append((idx, passed, output))
                self.test_completed.emit(idx, passed, output)

                # 更新进度
                completed_tests += 1
                self.progress_updated.emit(completed_tests, total_tests)

            # 计算总分
            if self.test_cases:
                total_score = sum(test.get('score', 1) for test in self.test_cases)
                earned_score = sum(
                    self.test_cases[idx].get('score', 1)
                    for idx, passed, _ in self.results
                    if passed
                )
                score = (earned_score / total_score * 100) if total_score > 0 else 0
            else:
                score = 0

            self.all_completed.emit(score)
            logger.info(f"PTA 测试完成: {len(self.results)}/{total_tests} 通过, 得分: {score:.1f}")

    def stop(self):
        """停止测试执行"""
        self._is_running = False

    def _run_single_test(self, code, test_case):
        """
        执行单个测试点

        参数：
            code: 用户代码
            test_case: 测试用例 {input: ..., expected: ..., score: ...}

        返回：
            (passed, output): 是否通过，实际输出
        """
        temp_path = None
        try:
            # 构建测试代码
            input_data = test_case.get('input', '')
            test_code = f"""
import sys
from io import StringIO

# 重定向输入
sys.stdin = StringIO('''{input_data}''')

# 用户代码
{code}
"""
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as f:
                f.write(test_code)
                temp_path = f.name

            # 使用 subprocess 执行，隔离环境
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(
                [sys.executable, temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creation_flags
            )

            # 超时等待
            stdout, stderr = process.communicate(timeout=self.timeout)
            actual = stdout.strip()
            expected = test_case.get('expected', '').strip()

            # 比较输出（支持多行输出的比较）
            passed = self._compare_output(actual, expected)

            return passed, actual

        except subprocess.TimeoutExpired:
            # 超时处理
            if process:
                process.kill()
                process.wait()
            return False, "执行超时"

        except Exception as e:
            # 全局异常捕获
            logger.error(f"测试点执行异常: {e}")
            return False, str(e)

        finally:
            # 清理临时文件
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    def _compare_output(self, actual: str, expected: str) -> bool:
        """
        比较实际输出和预期输出

        支持：
        - 忽略首尾空白
        - 忽略行尾空白
        - 统一换行符
        """
        # 标准化输出
        def normalize(text):
            # 统一换行符
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            # 分割成行，去除每行首尾空白
            lines = [line.strip() for line in text.split('\n')]
            # 去除空行
            lines = [line for line in lines if line]
            return '\n'.join(lines)

        return normalize(actual) == normalize(expected)


class CodeExecutor:
    """
    代码执行器类

    提供同步和异步两种执行方式：
    - execute(): 同步执行（阻塞）
    - execute_with_thread(): 异步执行（非阻塞）
    - run_pta_tests(): PTA 风格测试
    """

    def __init__(self, timeout=None):
        """
        初始化代码执行器

        参数：
            timeout: 超时时间（秒），默认使用配置值
        """
        self.timeout = timeout or config.security.code_timeout
        self._current_thread = None
        self._current_runner = None

    def execute(self, code: str) -> tuple:
        """
        执行 Python 代码（同步方式）

        参数：
            code: 要执行的代码字符串

        返回：
            (success, output, error): 是否成功，输出内容，错误信息
        """
        if not code or not code.strip():
            return False, '', '代码不能为空'

        temp_path = None
        try:
            # 创建临时文件执行代码
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as f:
                f.write(code)
                temp_path = f.name

            # 使用 subprocess 执行，隔离环境
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(
                [sys.executable, temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creation_flags
            )

            # 超时等待
            stdout, stderr = process.communicate(timeout=self.timeout)

            if process.returncode == 0:
                return True, stdout, ""
            else:
                return False, stdout, stderr

        except subprocess.TimeoutExpired:
            # 超时处理
            if process:
                process.kill()
                process.wait()
            return False, '', f'代码执行超时（超过{self.timeout}秒）'

        except Exception as e:
            # 全局异常捕获
            return False, '', f'执行错误: {str(e)}'

        finally:
            # 清理临时文件
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

    def validate_code(self, code: str) -> tuple:
        """
        验证代码语法

        参数：
            code: 要验证的代码

        返回：
            (is_valid, error): 是否有效，错误信息
        """
        if not code or not code.strip():
            return False, '代码不能为空'

        try:
            compile(code, '<string>', 'exec')
            return True, ''
        except SyntaxError as e:
            return False, f'语法错误（第{e.lineno}行）: {e.msg}'
        except Exception as e:
            return False, f'编译错误: {str(e)}'

    def execute_with_thread(self, code: str, callback=None) -> CodeExecutionThread:
        """
        使用线程异步执行代码

        参数：
            code: 要执行的代码
            callback: 完成回调函数 (success, output, error)

        返回：
            CodeExecutionThread 实例
        """
        # 停止之前的执行
        self.stop_current()

        thread = CodeExecutionThread(code, self.timeout)
        if callback:
            thread.finished.connect(callback)

        # 保存引用，便于后续停止
        self._current_thread = thread

        # 线程完成后清理引用
        thread.finished.connect(lambda: self._cleanup_thread())

        thread.start()
        return thread

    def _cleanup_thread(self):
        """清理线程引用"""
        self._current_thread = None

    def stop_current(self):
        """停止当前正在执行的代码"""
        if self._current_thread and self._current_thread.isRunning():
            self._current_thread.stop()
            self._current_thread.wait(1000)

        if self._current_runner and self._current_runner.isRunning():
            self._current_runner.stop()
            self._current_runner.wait(1000)

    def run_pta_tests(self, code: str, test_cases: list, callback=None, progress_callback=None) -> PTATestRunner:
        """
        运行 PTA 风格测试点验证

        参数：
            code: 用户代码
            test_cases: 测试用例列表 [{input: ..., expected: ..., score: ...}]
            callback: 完成回调函数 (score)
            progress_callback: 进度回调函数 (current, total)

        返回：
            PTATestRunner 实例
        """
        # 停止之前的执行
        self.stop_current()

        runner = PTATestRunner(code, test_cases, self.timeout)
        if callback:
            runner.all_completed.connect(callback)
        if progress_callback:
            runner.progress_updated.connect(progress_callback)

        # 保存引用，便于后续停止
        self._current_runner = runner

        # 完成后清理引用
        runner.all_completed.connect(lambda: self._cleanup_runner())

        runner.start()
        return runner

    def _cleanup_runner(self):
        """清理运行器引用"""
        self._current_runner = None

    def get_timeout(self) -> int:
        """获取当前超时设置"""
        return self.timeout

    def set_timeout(self, timeout: int):
        """设置超时时间"""
        self.timeout = timeout
