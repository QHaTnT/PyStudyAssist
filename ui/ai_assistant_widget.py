# -*- coding: utf-8 -*-
"""
悬浮式 AI 助手模块（计算机二级 Python 专用）
- 默认圆形悬浮按钮，点击 0.3s 展开/收起
- iOS 极简风格配色与动效
- 内置考点/真题/代码解释导览与问答守则
- 接入 mimo API 提供智能问答服务
- 支持代码诊断功能（上下文注入）
- SSE 流式输出，打字机效果
"""
import json
import requests
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize, QTimer, QEvent, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QTextBrowser, QTextEdit, QSizePolicy, QGraphicsDropShadowEffect, QMessageBox
)
from config import MIMO_CONFIG


class MimoStreamThread(QThread):
    """
    mimo API 流式请求线程（SSE）

    特性：
    - SSE 流式输出
    - 自动重连机制
    - 超时保护
    """
    chunk_received = pyqtSignal(str)      # 收到文本块
    finished = pyqtSignal()               # 完成
    error_occurred = pyqtSignal(str)      # 错误

    def __init__(self, messages, api_key=None):
        super().__init__()
        self.messages = messages
        self.api_key = api_key or MIMO_CONFIG.get('api_key', '')
        self._is_running = True

    def run(self):
        """SSE 流式请求"""
        try:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }

            # 构建系统提示词
            system_prompt = {
                "role": "system",
                "content": """你是一个专业的计算机二级Python教学助手，专门解答Python相关问题。
请专注于以下范围：
1. Python基础语法和数据类型
2. 列表、字典、元组、集合操作
3. 流程控制（if、for、while）
4. 函数定义与调用
5. 文件操作（读写、编码）
6. 异常处理
7. 常用内置模块（random、datetime、math等）
8. 简单的算法和数据处理
9. 代码调试和问题诊断

如果问题超出二级Python范围，请礼貌地引导回相关知识点。
回答要简洁、准确、易懂，适合初学者理解。
格式要求：使用Markdown语法，适当使用代码块示例。"""
            }

            all_messages = [system_prompt] + self.messages

            data = {
                "model": MIMO_CONFIG.get('model', 'mimo-v2.5'),
                "messages": all_messages,
                "stream": True,
                "temperature": MIMO_CONFIG.get('temperature', 0.6),
                "max_tokens": MIMO_CONFIG.get('max_tokens', 4096)
            }

            response = requests.post(
                MIMO_CONFIG.get('api_url', 'https://api.xiaomimimo.com/v1/chat/completions'),
                headers=headers,
                json=data,
                stream=True,
                timeout=MIMO_CONFIG.get('timeout', 30)
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    # 检查是否应该停止
                    if not self._is_running:
                        break

                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            json_str = line[6:]
                            if json_str == '[DONE]':
                                break
                            try:
                                chunk = json.loads(json_str)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        self.chunk_received.emit(content)
                            except json.JSONDecodeError:
                                pass
                self.finished.emit()
            else:
                error_msg = f"API请求失败: {response.status_code}\n"
                try:
                    error_detail = response.json().get("error", {}).get("message", "未知错误")
                    error_msg += error_detail
                except:
                    error_msg += response.text[:100]
                self.error_occurred.emit(error_msg)

        except requests.exceptions.Timeout:
            self.error_occurred.emit("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("网络连接失败，请检查网络")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"请求异常: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"未知错误: {str(e)}")

    def stop(self):
        """停止线程"""
        self._is_running = False


class FloatingAssistant(QWidget):
    BUTTON_SIZE = 100
    PANEL_WIDTH = 900
    PANEL_HEIGHT = 1000
    EDGE_MARGIN = 18
    ANIM_MS = 300

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setMouseTracking(True)

        # 获取用户信息
        self.user = getattr(parent, 'user', None) if parent else None
        self.user_avatar_path = None
        if self.user and hasattr(self.user, 'avatar_path'):
            self.user_avatar_path = self.user.avatar_path

        # mimo API 配置
        self.api_key = MIMO_CONFIG.get('api_key', '')
        self.conversation_history = []  # 对话历史
        self.max_history = 10  # 最大历史记录数

        self.expanded = False
        self.user_dragged = False
        self.drag_offset = None
        self.anchor_pos = None

        self._loading_frames = ["⠁", "⠃", "⠇", "⠧", "⠷", "⠿", "⠿", "⠷", "⠧", "⠇", "⠃"]
        self._loading_index = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._tick_loading)

        self.mimo_thread = None  # mimo 线程实例
        self.current_response = ""  # 当前流式响应内容
        self._update_timer = QTimer(self)  # 节流定时器
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update_display)
        self._pending_update = False  # 是否有待处理的更新

        self._build_ui()
        self._apply_palette()

        self.resize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self._place_bottom_right()
        self.raise_()

    def _build_ui(self):
        self.main_button = QPushButton("P", self)
        self.main_button.setObjectName("mainBtn")
        self.main_button.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self.main_button.setToolTip("PyStudyAssist")
        self.main_button.setCursor(Qt.OpenHandCursor)
        self.main_button.installEventFilter(self)
        self.main_button.clicked.connect(self.toggle)

        self.panel = QFrame(self)
        self.panel.setFixedSize(self.PANEL_WIDTH, self.PANEL_HEIGHT)
        self.panel.setVisible(False)
        self.panel_layout = QVBoxLayout(self.panel)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(0)

        # ===== 顶部栏 =====
        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 12)
        header.setSpacing(10)

        back_btn = QPushButton("←")
        back_btn.setFixedSize(40, 40)
        back_btn.setFont(QFont("SF Pro Display", 20, QFont.Bold))
        back_btn.clicked.connect(self.toggle)
        back_btn.setObjectName("backBtn")

        title = QLabel("PyStudyAssist AI")
        title.setFont(QFont("SF Pro Display", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        clear_btn = QPushButton("🗑")
        clear_btn.setFixedSize(40, 40)
        clear_btn.setFont(QFont("Arial", 18))
        clear_btn.setToolTip("清除对话历史")
        clear_btn.clicked.connect(self._clear_conversation)
        clear_btn.setObjectName("clearBtn")

        header.addWidget(back_btn)
        header.addStretch()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)

        header_frame = QFrame()
        header_frame.setLayout(header)
        header_frame.setStyleSheet("background-color: #FAFAFA; border-bottom: 1px solid #E0E0E0;")
        header_frame.setMinimumHeight(90)
        header_frame.setMaximumHeight(95)
        self.panel_layout.addWidget(header_frame)

        # ===== 聊天区 =====
        self.response_view = QTextBrowser()
        self.response_view.setObjectName("responseView")
        self.response_view.setOpenExternalLinks(True)
        self.response_view.setStyleSheet("QTextBrowser { border: none; background-color: #FFFFFF; }")
        self.response_view.setPlaceholderText("开始聊天...")
        self.response_view.setReadOnly(True)
        self.panel_layout.addWidget(self.response_view, 1)

        # ===== 加载指示 =====
        self.loading_label = QLabel("")
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.setVisible(False)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.panel_layout.addWidget(self.loading_label)

        # ===== 输入区 =====
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #FAFAFA; border-top: 1px solid #E0E0E0;")
        input_frame.setMaximumHeight(120)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(6)

        # 第一行：快速问题 + 诊断按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        attach_btn = QPushButton("📎 快速问题")
        attach_btn.setFont(QFont("Microsoft YaHei", 9))
        attach_btn.setFixedHeight(28)
        attach_btn.setObjectName("attachBtn")
        attach_btn.clicked.connect(self._show_quick_questions)
        btn_row.addWidget(attach_btn)

        diagnose_btn = QPushButton("🔍 诊断代码")
        diagnose_btn.setFont(QFont("Microsoft YaHei", 9))
        diagnose_btn.setFixedHeight(28)
        diagnose_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
        """)
        diagnose_btn.clicked.connect(self._diagnose_code)
        btn_row.addWidget(diagnose_btn)

        btn_row.addStretch()
        input_layout.addLayout(btn_row)

        # 第二行：输入框 + 发送按钮
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入二级Python问题/代码...")
        self.input_box.setFixedHeight(45)
        self.input_box.setObjectName("inputBox")
        self.input_box.installEventFilter(self)
        input_row.addWidget(self.input_box)

        self.send_btn = QPushButton("✈")
        self.send_btn.setFixedSize(45, 45)
        self.send_btn.setFont(QFont("Arial", 20))
        self.send_btn.clicked.connect(self._on_send)
        self.send_btn.setObjectName("sendBtn")
        input_row.addWidget(self.send_btn)

        input_layout.addLayout(input_row)

        self.panel_layout.addWidget(input_frame)

    def _apply_palette(self):
        soft_blue = "#F2F2F2"
        softer_blue = "#F7F7F7"
        border_blue = "#E0E0E0"
        text_dark = "#333"

        self.setStyleSheet(f"""
            QWidget {{ font-family: 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', 'Segoe UI'; color: {text_dark}; }}
            QPushButton {{
                background: {soft_blue};
                border: 1px solid {border_blue};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 18px;
            }}
            QPushButton#mainBtn {{
                font-size: 44px;
                font-weight: bold;
                color: #999;
                border-radius: 50px;
                background: #FFD700;
                border: none;
            }}
            QPushButton#mainBtn:hover {{ background: #FFC700; }}
            QPushButton#backBtn {{ border: none; background: transparent; font-size: 20px; }}
            QPushButton#clearBtn {{ border: none; background: transparent; font-size: 18px; }}
            QPushButton#clearBtn:hover {{ color: #FF4444; }}
            QPushButton#attachBtn {{ border: none; background: transparent; font-size: 12px; }}
            QPushButton#sendBtn {{
                background-color: #FFD700;
                border: none;
                border-radius: 22px;
                color: #000;
                font-weight: bold;
            }}
            QPushButton#sendBtn:hover {{ background-color: #FFC700; }}
            QPushButton#sendBtn:pressed {{ background-color: #FFB700; }}
            QPushButton#sendBtn:disabled {{ background-color: #E0E0E0; color: #999; }}
            QPushButton:hover {{ background: {softer_blue}; }}
            QPushButton:pressed {{ background: rgba(0,0,0,0.04); }}
            QFrame {{ background: #FAFAFA; border-radius: 16px; border: 1px solid {border_blue}; }}
            QTextBrowser#responseView {{
                background: white;
                border-radius: 0px;
                padding: 12px;
                border: none;
                font-size: 24px;
                line-height: 1.6;
            }}
            QTextEdit#inputBox {{
                background: white;
                border-radius: 8px;
                border: 1px solid {border_blue};
                font-size: 16px;
                padding: 8px;
            }}
            QLabel#loadingLabel {{ color: #666; font-size: 17px; }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(0, 6)
        shadow.setBlurRadius(22)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.main_button.setGraphicsEffect(shadow)

    def toggle(self):
        self.raise_()
        self.expanded = not self.expanded
        self.panel.setVisible(True)
        start_rect = self.geometry()
        end_rect = self._target_geometry(expanded=self.expanded)

        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(self.ANIM_MS)
        anim.setStartValue(start_rect)
        anim.setEndValue(end_rect)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: self._on_anim_finished(self.expanded))
        anim.stateChanged.connect(lambda _, __: self._sync_children_geometry())
        anim.start()
        self._anim = anim

    def _on_anim_finished(self, expanded):
        if not expanded:
            self.panel.setVisible(False)
        self._sync_children_geometry()

    def _target_geometry(self, expanded):
        if self.anchor_pos is None:
            self._place_bottom_right()
        anchor = self.anchor_pos
        if expanded:
            size = QSize(self.PANEL_WIDTH, self.PANEL_HEIGHT)
        else:
            size = QSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        top_left = QPoint(anchor.x() - size.width(), anchor.y() - size.height())
        if self.parent():
            parent_rect = self.parent().rect()
            max_x = parent_rect.width() - size.width()
            max_y = parent_rect.height() - size.height()
            top_left.setX(max(0, min(top_left.x(), max_x)))
            top_left.setY(max(0, min(top_left.y(), max_y)))
        return QRect(top_left, size)

    def _place_bottom_right(self):
        if self.parent():
            parent_rect = self.parent().rect()
            w = parent_rect.width() if parent_rect.width() > 0 else 1200
            h = parent_rect.height() if parent_rect.height() > 0 else 800
            anchor = QPoint(w - self.EDGE_MARGIN, h - self.EDGE_MARGIN)
        else:
            anchor = QPoint(self.PANEL_WIDTH + self.EDGE_MARGIN, self.PANEL_HEIGHT + self.EDGE_MARGIN)
        self.anchor_pos = anchor
        self.setGeometry(self._target_geometry(expanded=False))
        self.show()
        self._sync_children_geometry()

    def _sync_children_geometry(self):
        btn_x = self.width() - self.BUTTON_SIZE
        btn_y = self.height() - self.BUTTON_SIZE
        self.main_button.setGeometry(btn_x, btn_y, self.BUTTON_SIZE, self.BUTTON_SIZE)
        self.main_button.setStyleSheet(self.main_button.styleSheet() + f"border-radius: {self.BUTTON_SIZE // 2}px;")
        self.panel.setGeometry(0, 0, self.PANEL_WIDTH, self.PANEL_HEIGHT)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_children_geometry()
        self.anchor_pos = self.geometry().bottomRight()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.pos()
            self.user_dragged = True
            self._loading_timer.stop()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.LeftButton:
            if self.parent():
                new_pos = self.parent().mapFromGlobal(event.globalPos() - self.drag_offset)
                new_pos.setX(max(0, min(new_pos.x(), self.parent().width() - self.width())))
                new_pos.setY(max(0, min(new_pos.y(), self.parent().height() - self.height())))
                self.move(new_pos)
                self.anchor_pos = self.geometry().bottomRight()
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        super().mouseReleaseEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.input_box:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    if event.modifiers() & Qt.ShiftModifier:
                        return False
                    else:
                        self._on_send()
                        return True

        if obj == self.main_button:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.main_button.setCursor(Qt.ClosedHandCursor)
                self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
                return False
            if event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton and self.drag_offset is not None:
                new_pos = event.globalPos() - self.drag_offset
                if self.parent():
                    max_x = self.parent().width() - self.width()
                    max_y = self.parent().height() - self.height()
                    new_x = max(0, min(new_pos.x(), max_x))
                    new_y = max(0, min(new_pos.y(), max_y))
                    self.move(new_x, new_y)
                    self.anchor_pos = self.geometry().bottomRight()
                else:
                    self.move(new_pos)
                return True
            if event.type() == QEvent.MouseButtonRelease:
                self.main_button.setCursor(Qt.OpenHandCursor)
                self.drag_offset = None
                return False
        return super().eventFilter(obj, event)

    def _show_quick_questions(self):
        """显示快速问题模板"""
        quick_questions = [
            "解释Python中的列表和元组的区别",
            "如何在Python中读写文件？",
            "解释try-except异常处理机制",
            "Python函数的参数类型有哪些？",
            "解释for循环和while循环的区别",
            "什么是列表推导式？举个例子",
            "Python中如何导入和使用模块？",
            "解释字符串的常用操作方法",
            "什么是字典？如何遍历字典？",
            "Python中的lambda函数是什么？"
        ]

        menu_text = "<b>快速提问模板：</b><br><br>"
        for i, question in enumerate(quick_questions, 1):
            menu_text += f"{i}. {question}<br>"
        menu_text += "<br>点击上方问题可直接提问"

        self._append_chat("assistant", menu_text)

    def _diagnose_code(self):
        """提取编辑器代码并诊断"""
        main_window = self.window()
        if hasattr(main_window, 'editor_widget'):
            code = main_window.editor_widget.code_editor.toPlainText()
            output = main_window.editor_widget.output_text.toPlainText()

            if not code.strip():
                self._append_chat("assistant", "⚠️ 编辑器中没有代码内容。请先在代码编辑器中编写代码，然后再点击诊断按钮。")
                return

            # 构建诊断 Prompt
            prompt = f"""请分析以下 Python 代码的问题：

【代码内容】
```python
{code}
```

【运行输出/错误信息】
{output if output else "无"}

请提供：
1. 代码问题分析
2. 错误原因
3. 修复建议
4. 改进后的代码"""

            self._append_chat("user", "🔍 请求诊断代码")
            self._stream_mimo_response([{"role": "user", "content": prompt}])
        else:
            self._append_chat("assistant", "⚠️ 无法访问代码编辑器。请确保主窗口已打开。")

    def _on_send(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            self._append_chat("assistant", "请输入问题或代码，我会为你解答计算机二级Python相关问题。")
            return

        self.send_btn.setEnabled(False)
        self._append_chat("user", text)
        self.input_box.clear()

        self.conversation_history.append({"role": "user", "content": text})

        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        self._stream_mimo_response(self.conversation_history)

    def _stream_mimo_response(self, messages):
        """流式调用 mimo API"""
        self._set_loading(True)
        self.current_response = ""

        # 添加临时占位符
        self._append_chat("assistant", "⏳ 正在思考...")

        self.mimo_thread = MimoStreamThread(messages, self.api_key)
        self.mimo_thread.chunk_received.connect(self._on_chunk_received)
        self.mimo_thread.finished.connect(self._on_stream_finished)
        self.mimo_thread.error_occurred.connect(self._on_stream_error)
        self.mimo_thread.start()

    def _on_chunk_received(self, chunk):
        """
        处理流式文本块（带节流）

        使用节流机制避免频繁更新 UI，提高性能
        """
        self.current_response += chunk

        # 标记有待处理的更新
        self._pending_update = True

        # 如果定时器未运行，启动它（50ms 节流）
        if not self._update_timer.isActive():
            self._update_timer.start(50)

    def _do_update_display(self):
        """实际更新显示（由节流定时器触发）"""
        if self._pending_update and self.current_response:
            self._update_last_ai_message(self.current_response)
            self._pending_update = False

    def _on_stream_finished(self):
        """流式响应完成"""
        self._set_loading(False)
        self.send_btn.setEnabled(True)

        if self.current_response:
            self.conversation_history.append({"role": "assistant", "content": self.current_response})
            # 最终更新
            self._update_last_ai_message(self.current_response)

    def _on_stream_error(self, error_msg):
        """处理 API 错误"""
        self._set_loading(False)
        self.send_btn.setEnabled(True)

        error_html = f"<span style='color: #FF4444;'>⚠️ {error_msg}</span><br><br>"
        error_html += "建议：<br>"
        error_html += "1. 检查网络连接<br>"
        error_html += "2. 确认API密钥有效<br>"
        error_html += "3. 稍后重试或联系管理员"

        # 移除最后一个占位符，显示错误
        self._replace_last_ai_message(error_html)

    def _update_last_ai_message(self, text):
        """
        更新最后一个 AI 消息（实现流式打字机效果）

        工作原理：
        1. 获取当前 HTML 内容
        2. 找到最后一个 AI 消息块
        3. 替换其内容为新的格式化文本
        4. 滚动到底部
        """
        # 格式化 Markdown 文本
        formatted = self._markdown_to_html(text)

        # 获取当前 HTML
        html = self.response_view.toHtml()

        # 构建新的 AI 消息气泡
        avatar_html = "<div style='width:50px; height:50px; background:#4A90E2; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:26px; font-weight:bold;'>AI</div>"

        new_bubble = (
            f"<table width='100%' style='margin:12px 0;'><tr>"
            f"<td style='vertical-align:bottom; padding-right:10px;'>{avatar_html}</td>"
            f"<td width='100%'></td></tr>"
            f"<tr><td colspan='2' style='text-align:left;'>"
            f"<div style='display:inline-block; max-width:70%; background:#F5F5F5; color:#111; padding:14px 18px; "
            f"border-radius:15px 15px 15px 4px; border:1px solid #E0E0E0; font-size:26px; line-height:1.7; word-wrap: break-word;'>"
            f"{formatted}</div></td></tr></table>"
        )

        # 查找并替换最后一个 AI 消息块
        # 使用正则表达式找到最后一个 AI 气泡的位置
        import re

        # 匹配 AI 气泡的模式（蓝色背景 #F5F5F5）
        pattern = r'(<table width=\'100%\' style=\'margin:12px 0;\'><tr>\s*<td[^>]*>.*?AI.*?</td>.*?</table>)'

        # 找到最后一个匹配
        matches = list(re.finditer(pattern, html, re.DOTALL))

        if matches:
            last_match = matches[-1]
            # 替换最后一个 AI 消息
            new_html = html[:last_match.start()] + new_bubble + html[last_match.end():]
            self.response_view.setHtml(new_html)
        else:
            # 如果没有找到现有的 AI 消息，直接追加
            self._append_chat("assistant", formatted)

        # 滚动到底部
        scrollbar = self.response_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _replace_last_ai_message(self, html_content):
        """替换最后一个 AI 消息（用于错误显示）"""
        # 获取当前 HTML
        html = self.response_view.toHtml()

        # 构建错误消息气泡
        avatar_html = "<div style='width:50px; height:50px; background:#4A90E2; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:26px; font-weight:bold;'>AI</div>"

        error_bubble = (
            f"<table width='100%' style='margin:12px 0;'><tr>"
            f"<td style='vertical-align:bottom; padding-right:10px;'>{avatar_html}</td>"
            f"<td width='100%'></td></tr>"
            f"<tr><td colspan='2' style='text-align:left;'>"
            f"<div style='display:inline-block; max-width:70%; background:#FFF5F5; color:#111; padding:14px 18px; "
            f"border-radius:15px 15px 15px 4px; border:1px solid #FFD7D7; font-size:26px; line-height:1.7; word-wrap: break-word;'>"
            f"{html_content}</div></td></tr></table>"
        )

        # 查找并替换最后一个 AI 消息块
        import re

        # 匹配 AI 气泡的模式
        pattern = r'(<table width=\'100%\' style=\'margin:12px 0;\'><tr>\s*<td[^>]*>.*?AI.*?</td>.*?</table>)'

        # 找到最后一个匹配
        matches = list(re.finditer(pattern, html, re.DOTALL))

        if matches:
            last_match = matches[-1]
            # 替换最后一个 AI 消息
            new_html = html[:last_match.start()] + error_bubble + html[last_match.end():]
            self.response_view.setHtml(new_html)
        else:
            # 如果没有找到现有的 AI 消息，直接追加
            self._append_chat("assistant", html_content)

        # 滚动到底部
        scrollbar = self.response_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _clear_conversation(self):
        """清除对话历史"""
        self.conversation_history = []
        self.response_view.clear()
        self._append_chat("assistant", "对话历史已清除。请问我任何计算机二级Python相关问题！")

    def _set_loading(self, loading):
        if loading:
            self.loading_label.setVisible(True)
            self.loading_label.setText("思考中～ ⠁")
            self._loading_index = 0
            self._loading_timer.start(90)
        else:
            self.loading_label.setVisible(False)
            self._loading_timer.stop()

    def _tick_loading(self):
        self._loading_index = (self._loading_index + 1) % len(self._loading_frames)
        self.loading_label.setText(f"思考中～ {self._loading_frames[self._loading_index]}")

    def _append_chat(self, role, body_html):
        if role == "user":
            if self.user_avatar_path:
                avatar_html = f"<img src='{self.user_avatar_path}' style='width:50px; height:50px; border-radius:50%; object-fit:cover;' />"
            else:
                avatar_html = "<div style='width:50px; height:50px; background:#EDEDED; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#999; font-size:26px;'>👤</div>"

            bubble = (
                f"<table width='100%' style='margin:12px 0;'><tr><td width='100%'></td>"
                f"<td style='vertical-align:bottom; padding-left:10px;'>{avatar_html}</td></tr>"
                f"<tr><td colspan='2' style='text-align:right;'>"
                f"<div style='display:inline-block; max-width:70%; background:#FFD700; color:#111; padding:14px 18px; "
                f"border-radius:15px 15px 4px 15px; border:none; font-size:26px; line-height:1.7; word-wrap: break-word;'>"
                f"{body_html}</div></td></tr></table>"
            )
        else:
            avatar_html = "<div style='width:50px; height:50px; background:#4A90E2; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:26px; font-weight:bold;'>AI</div>"

            formatted_content = self._markdown_to_html(body_html)

            bubble = (
                f"<table width='100%' style='margin:12px 0;'><tr>"
                f"<td style='vertical-align:bottom; padding-right:10px;'>{avatar_html}</td>"
                f"<td width='100%'></td></tr>"
                f"<tr><td colspan='2' style='text-align:left;'>"
                f"<div style='display:inline-block; max-width:70%; background:#F5F5F5; color:#111; padding:14px 18px; "
                f"border-radius:15px 15px 15px 4px; border:1px solid #E0E0E0; font-size:26px; line-height:1.7; word-wrap: break-word;'>"
                f"{formatted_content}</div></td></tr></table>"
            )

        self.response_view.append(bubble)
        self.response_view.verticalScrollBar().setValue(self.response_view.verticalScrollBar().maximum())

    def _markdown_to_html(self, markdown_text):
        """将Markdown格式转换为HTML"""
        import re

        html = markdown_text

        def replace_code_block(match):
            lang = match.group(1) if match.group(1) else ""
            code = match.group(2)
            code = code.replace('<', '&lt;').replace('>', '&gt;')
            return f"<pre style='background:#F5F5F5; padding:10px; margin:8px 0; border-radius:5px; border:1px solid #E0E0E0; overflow-x:auto;'><code>{code}</code></pre>"

        html = re.sub(r'```(\w*)\n(.*?)\n```', replace_code_block, html, flags=re.DOTALL)
        html = re.sub(r'`([^`]+)`', r'<code style="background:#F0F0F0; padding:2px 6px; border-radius:3px; font-family:Consolas,monospace;">\1</code>', html)
        html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
        html = re.sub(r'__(.+?)__', r'<b>\1</b>', html)
        html = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', html)
        html = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'<i>\1</i>', html)

        html = re.sub(r'^######\s+(.+)$', r'<h6 style="margin:10px 0 5px 0;">\1</h6>', html, flags=re.MULTILINE)
        html = re.sub(r'^#####\s+(.+)$', r'<h5 style="margin:10px 0 5px 0;">\1</h5>', html, flags=re.MULTILINE)
        html = re.sub(r'^####\s+(.+)$', r'<h4 style="margin:12px 0 6px 0;">\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^###\s+(.+)$', r'<h3 style="margin:14px 0 7px 0;">\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^##\s+(.+)$', r'<h2 style="margin:16px 0 8px 0;">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^#\s+(.+)$', r'<h1 style="margin:18px 0 9px 0;">\1</h1>', html, flags=re.MULTILINE)

        lines = html.split('\n')
        in_list = False
        result_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    result_lines.append('<ul style="margin:8px 0; padding-left:25px;">')
                    in_list = True
                content = stripped[2:]
                result_lines.append(f'<li style="margin:3px 0;">{content}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)

        if in_list:
            result_lines.append('</ul>')

        html = '\n'.join(result_lines)

        lines = html.split('\n')
        in_ol = False
        result_lines = []

        for line in lines:
            stripped = line.strip()
            if re.match(r'^\d+\.\s+', stripped):
                if not in_ol:
                    result_lines.append('<ol style="margin:8px 0; padding-left:25px;">')
                    in_ol = True
                content = re.sub(r'^\d+\.\s+', '', stripped)
                result_lines.append(f'<li style="margin:3px 0;">{content}</li>')
            else:
                if in_ol:
                    result_lines.append('</ol>')
                    in_ol = False
                result_lines.append(line)

        if in_ol:
            result_lines.append('</ol>')

        html = '\n'.join(result_lines)
        html = html.replace('\n', '<br>')
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color:#2196F3; text-decoration:none;">\1</a>', html)

        return html

    def ensure_inside_parent(self):
        if not self.parent():
            return
        parent_rect = self.parent().rect()
        geo = self.geometry()
        new_x = min(max(0, geo.x()), max(0, parent_rect.width() - geo.width()))
        new_y = min(max(0, geo.y()), max(0, parent_rect.height() - geo.height()))
        self.setGeometry(new_x, new_y, geo.width(), geo.height())
        self.anchor_pos = self.geometry().bottomRight()

    def reposition_on_parent_resize(self):
        if not self.user_dragged:
            self._place_bottom_right()
        else:
            self.ensure_inside_parent()

    def closeEvent(self, event):
        """关闭窗口时确保线程结束"""
        # 停止更新定时器
        self._update_timer.stop()

        # 停止 mimo 线程
        if self.mimo_thread and self.mimo_thread.isRunning():
            self.mimo_thread.stop()
            self.mimo_thread.wait(1000)  # 等待最多 1 秒
            if self.mimo_thread.isRunning():
                self.mimo_thread.terminate()  # 强制终止

        super().closeEvent(event)
