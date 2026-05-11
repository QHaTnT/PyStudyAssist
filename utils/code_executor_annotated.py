# -*- coding: utf-8 -*-
"""
代码执行器 - PyPalPrep Python学习教辅系统

【文件功能说明】
这个文件提供了安全执行用户输入Python代码的功能。

【为什么需要代码执行器】
1. 用户需要在程序中运行Python代码（编程题、代码编辑器）
2. 直接执行用户代码有安全风险
3. 需要捕获代码的输出结果
4. 需要限制执行时间，防止无限循环

【安全考虑】
- 使用独立的线程执行代码
- 设置超时时间限制
- 捕获所有异常，防止程序崩溃
- 不限制代码功能（因为是学习环境）

【技术实现】
- 使用Thread创建独立线程执行代码
- 使用StringIO捕获标准输出和错误输出
- 使用队列在线程间传递结果
"""
import sys  # 系统模块
import io  # IO模块，用于内存文件操作
import contextlib  # 上下文管理器模块
import signal  # 信号模块（备用）
from threading import Thread  # 线程模块
import queue  # 队列模块，用于线程间通信


class CodeExecutor:
    """
    代码执行器类

    【类的作用】
    提供安全执行Python代码的功能。

    【属性说明】
    - timeout: 超时时间（秒）
    """

    def __init__(self, timeout=5):
        """
        初始化代码执行器

        【参数说明】
        - timeout: 超时时间（秒），默认为5秒

        【为什么需要超时】
        如果用户代码中有无限循环，程序会卡死。
        设置超时可以自动终止执行。
        """
        self.timeout = timeout

    def execute(self, code):
        """
        执行Python代码

        【参数说明】
        - code: 要执行的代码字符串

        【返回值】
        - (是否成功, 输出内容, 错误信息)
        - 成功: (True, "Hello", "")
        - 失败: (False, "", "NameError: name 'x' is not defined")

        【执行流程】
        1. 创建输出缓冲区
        2. 创建结果队列
        3. 在新线程中执行代码
        4. 等待执行完成或超时
        5. 返回结果

        【示例】
        executor = CodeExecutor()
        success, output, error = executor.execute("print('Hello')")
        print(success)  # True
        print(output)   # Hello
        """
        if not code or not code.strip():
            return False, '', '代码不能为空'

        # 创建输出缓冲区
        # StringIO是一个内存中的文件对象，可以捕获print输出
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()

        # 创建结果队列
        # 队列用于在主线程和执行线程之间传递结果
        result_queue = queue.Queue()

        def run_code():
            """
            在单独线程中运行代码

            【为什么使用线程】
            1. 可以设置超时时间
            2. 不会阻塞主线程（UI不会卡死）
            3. 可以捕获代码中的无限循环
            """
            try:
                # 重定向标准输出和标准错误
                # 这样代码中的print输出会被捕获到output_buffer
                with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
                    # 创建执行环境
                    exec_globals = {
                        '__builtins__': __builtins__,
                        # 可以添加一些安全的内置函数
                    }
                    exec_locals = {}

                    # 执行代码
                    # exec()函数执行动态创建的Python代码
                    exec(code, exec_globals, exec_locals)

                # 获取输出
                output = output_buffer.getvalue()
                error = error_buffer.getvalue()

                if error:
                    result_queue.put((False, output, error))
                else:
                    result_queue.put((True, output, ''))

            except Exception as e:
                # 捕获所有异常
                error_msg = f'{type(e).__name__}: {str(e)}'
                result_queue.put((False, output_buffer.getvalue(), error_msg))

        # 创建并启动执行线程
        exec_thread = Thread(target=run_code)
        exec_thread.daemon = True  # 设置为守护线程（主线程退出时自动结束）
        exec_thread.start()

        # 等待执行完成或超时
        exec_thread.join(timeout=self.timeout)

        if exec_thread.is_alive():
            # 执行超时
            return False, '', f'代码执行超时（超过{self.timeout}秒）'

        # 获取执行结果
        try:
            success, output, error = result_queue.get_nowait()
            return success, output, error
        except queue.Empty:
            return False, '', '执行出现未知错误'

    def validate_code(self, code):
        """
        验证代码语法

        【参数说明】
        - code: 要验证的代码

        【返回值】
        - (是否有效, 错误信息)

        【示例】
        executor = CodeExecutor()
        is_valid, error = executor.validate_code("print('Hello')")
        print(is_valid)  # True

        is_valid, error = executor.validate_code("print('Hello'")
        print(is_valid)  # False
        print(error)     # 语法错误（第1行）: unexpected EOF while parsing
        """
        if not code or not code.strip():
            return False, '代码不能为空'

        try:
            # compile()函数编译代码为字节码
            # 如果语法错误，会抛出SyntaxError异常
            compile(code, '<string>', 'exec')
            return True, ''
        except SyntaxError as e:
            # 语法错误
            return False, f'语法错误（第{e.lineno}行）: {e.msg}'
        except Exception as e:
            # 其他编译错误
            return False, f'编译错误: {str(e)}'
