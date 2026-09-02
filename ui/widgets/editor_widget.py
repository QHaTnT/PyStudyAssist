# -*- coding: utf-8 -*-
"""
代码编辑器模块
支持 QThread 异步执行、5秒超时保护
"""
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QFrame, QMessageBox, QFileDialog, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from utils.code_executor import CodeExecutor, CodeExecutionThread
from ui.styles.theme import COLORS, FONTS, SIZES
from config import config
import os


class EditorWidget(QWidget):
    """代码编辑器"""

    # 信号：代码执行完成（用于 AI 助手获取结果）
    code_executed = pyqtSignal(str, bool, str, str)  # code, success, output, error

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.executor = CodeExecutor()
        self.exec_thread = None
        self.current_file = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 工具栏
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['glass_bg']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius']}px;
            }}
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)

        for text, callback in [
            ("📄 新建", self._new_file),
            ("📂 打开", self._open_file),
            ("💾 保存", self._save_file),
        ]:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{ background: {COLORS['primary_alpha_hover']}; }}
            """)
            btn.clicked.connect(callback)
            toolbar_layout.addWidget(btn)

        toolbar_layout.addSpacing(20)

        run_btn = QPushButton("▶ 运行代码")
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        run_btn.clicked.connect(self._run_code)
        toolbar_layout.addWidget(run_btn)

        toolbar_layout.addStretch()

        self.file_label = QLabel("未命名文件")
        self.file_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        toolbar_layout.addWidget(self.file_label)

        layout.addWidget(toolbar)

        # 编辑器
        splitter = QSplitter(Qt.Vertical)

        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 15))
        self.code_editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['code_bg']};
                color: {COLORS['code_text']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
                font-family: 'Consolas', monospace;
            }}
        """)
        self.code_editor.setPlaceholderText("# 在此编写 Python 代码\nprint('Hello, World!')")
        splitter.addWidget(self.code_editor)

        # 输出区
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }}
        """)
        splitter.addWidget(self.output_text)

        splitter.setSizes([600, 300])
        layout.addWidget(splitter, 1)

    def _new_file(self):
        if self.code_editor.toPlainText().strip():
            reply = QMessageBox.question(
                self, '确认', '当前文件未保存，是否继续？',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.code_editor.clear()
        self.output_text.clear()
        self.current_file = None
        self.file_label.setText("未命名文件")

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, '打开 Python 文件', '', 'Python Files (*.py);;All Files (*.*)'
        )
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.code_editor.setPlainText(f.read())
            self.current_file = path
            self.file_label.setText(os.path.basename(path))

    def _save_file(self):
        if self.current_file:
            path = self.current_file
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, '保存 Python 文件', '', 'Python Files (*.py);;All Files (*.*)'
            )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.code_editor.toPlainText())
            self.current_file = path
            self.file_label.setText(os.path.basename(path))
            QMessageBox.information(self, '成功', '文件保存成功')

    def _run_code(self):
        """使用 QThread 异步执行代码"""
        code = self.code_editor.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, '提示', '请先输入代码')
            return

        # 停止之前的执行
        if self.exec_thread and self.exec_thread.isRunning():
            self.exec_thread.stop()

        self.output_text.clear()
        self.output_text.append("⏳ 正在执行...")

        # 使用线程异步执行
        self.exec_thread = CodeExecutionThread(code, config.security.code_timeout)
        self.exec_thread.finished.connect(self._on_code_finished)
        self.exec_thread.start()

    def _on_code_finished(self, success, output, error):
        """代码执行完成回调"""
        code = self.code_editor.toPlainText().strip()

        self.output_text.clear()
        if success:
            self.output_text.append(f"✅ 执行成功:\n{output or '(无输出)'}")
        else:
            self.output_text.append(f"❌ 执行失败:\n{error}")

        # 发送信号（供 AI 助手使用）
        self.code_executed.emit(code, success, output, error)

    def get_code_and_output(self):
        """获取当前代码和输出（供 AI 助手调用）"""
        code = self.code_editor.toPlainText().strip()
        output = self.output_text.toPlainText().strip()
        return code, output

    def refresh(self):
        pass
