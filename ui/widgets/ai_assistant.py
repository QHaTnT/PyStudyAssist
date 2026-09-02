# -*- coding: utf-8 -*-
"""
AI 助手模块
采用与 FloatingAssistant 相同的动态尺寸架构
支持 SSE 流式输出、上下文注入、考试禁用
"""
import json
import requests
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QTextBrowser, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QPoint, QSize, QTimer, QEvent,
    QPropertyAnimation, QEasingCurve, QRect
)
from PyQt5.QtGui import QColor, QFont
from config import config, MIMO_CONFIG
from ui.styles.theme import COLORS, FONTS


class MimoStreamThread(QThread):
    """mimo API 流式请求线程（SSE）"""
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, messages, api_key=None, context=None):
        super().__init__()
        self.messages = messages
        self.api_key = api_key or config.ai.api_key
        self.context = context  # 当前上下文
        self._is_running = True

    def run(self):
        try:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }

            # 构建系统提示词（包含上下文）
            system_content = """你是一个专业的计算机二级Python教学助手。
请专注于Python相关问题的回答，包括：
1. Python基础语法和数据类型
2. 列表、字典、元组、集合操作
3. 流程控制（if、for、while）
4. 函数定义与调用
5. 文件操作、异常处理
6. 代码调试和问题诊断

回答要简洁、准确、易懂，适合初学者理解。
格式要求：使用Markdown语法，适当使用代码块示例。"""

            # 如果有上下文，注入到系统提示词中
            if self.context:
                system_content += f"\n\n【当前用户上下文】\n{self.context}\n\n请根据用户的上下文提供更有针对性的帮助。"

            system_prompt = {
                "role": "system",
                "content": system_content
            }

            all_messages = [system_prompt] + self.messages

            data = {
                "model": config.ai.model,
                "messages": all_messages,
                "stream": True,
                "temperature": config.ai.temperature,
                "max_tokens": config.ai.max_tokens
            }

            response = requests.post(
                config.ai.api_url,
                headers=headers,
                json=data,
                stream=True,
                timeout=config.ai.timeout
            )

            if response.status_code == 200:
                for line in response.iter_lines():
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
                error_msg = f"API请求失败: {response.status_code}"
                try:
                    error_detail = response.json().get("error", {}).get("message", "")
                    if error_detail:
                        error_msg += f"\n{error_detail}"
                except:
                    pass
                self.error_occurred.emit(error_msg)

        except requests.exceptions.Timeout:
            self.error_occurred.emit("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("网络连接失败，请检查网络")
        except Exception as e:
            self.error_occurred.emit(f"错误: {str(e)}")

    def stop(self):
        self._is_running = False


class AIAssistant(QWidget):
    """
    AI 助手（采用 FloatingAssistant 的动态尺寸架构）

    展开时控件尺寸从 BUTTON_SIZE x BUTTON_SIZE 变为 PANEL_WIDTH x PANEL_HEIGHT
    面板始终在控件内部，按钮在控件右下角
    """

    BUTTON_SIZE = 60
    PANEL_WIDTH = 450
    PANEL_HEIGHT = 550
    EDGE_MARGIN = 30
    ANIM_MS = 300

    # 模块类型
    MODULE_HOME = 0
    MODULE_KNOWLEDGE = 1
    MODULE_PRACTICE = 2
    MODULE_EXAM = 3
    MODULE_EDITOR = 4
    MODULE_OTHER = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setMouseTracking(True)

        self.expanded = False
        self.user_dragged = False
        self.drag_offset = None
        self.anchor_pos = None
        self.current_module = self.MODULE_HOME
        self.current_response = ""
        self.mimo_thread = None
        self._editor_widget = None
        self._messages = []  # 统一的消息列表（用于UI和API）

        # 字体自适应
        self._base_font_size = 15
        self._current_font_size = 15

        # 缩放状态
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self._RESIZE_MARGIN = 8

        # 节流定时器
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update_display)
        self._pending_update = False

        self._build_ui()
        self._apply_palette()

        self.resize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self._place_bottom_right()
        self.raise_()

    def _build_ui(self):
        # 主按钮
        self.main_button = QPushButton("💬", self)
        self.main_button.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self.main_button.setToolTip("AI 助手")
        self.main_button.setCursor(Qt.OpenHandCursor)
        self.main_button.installEventFilter(self)
        self.main_button.clicked.connect(self.toggle)
        self.main_button.setStyleSheet(f"""
            QPushButton {{
                background: #E0F2FE;
                border: 2px solid #7DD3FC;
                border-radius: {self.BUTTON_SIZE // 2}px;
                font-size: 24px;
            }}
            QPushButton:hover {{
                background: #BAE6FD;
                border-color: #38BDF8;
            }}
        """)

        # 面板
        self.panel = QFrame(self)
        self.panel.setMinimumSize(300, 400)  # 最小尺寸
        self.panel.resize(self.PANEL_WIDTH, self.PANEL_HEIGHT)  # 初始尺寸
        self.panel.setVisible(False)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        # ===== 顶部栏 =====
        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 12)
        header.setSpacing(10)

        title = QLabel("AI 助手")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))

        clear_btn = QPushButton("清空")
        clear_btn.setFixedSize(50, 36)
        clear_btn.setToolTip("清空对话")
        clear_btn.clicked.connect(self._clear_conversation)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.clicked.connect(self.toggle)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        header.addWidget(close_btn)

        header_frame = QFrame()
        header_frame.setLayout(header)
        header_frame.setMinimumHeight(60)
        header_frame.setMaximumHeight(65)
        panel_layout.addWidget(header_frame)

        # ===== 聊天区 =====
        self.chat_area = QTextBrowser()
        self.chat_area.setOpenExternalLinks(True)
        self.chat_area.setPlaceholderText("开始聊天...")
        panel_layout.addWidget(self.chat_area, 1)

        # ===== 加载指示 =====
        self.loading_label = QLabel("")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setVisible(False)
        panel_layout.addWidget(self.loading_label)

        # ===== 快捷按钮区 =====
        quick_frame = QFrame()
        quick_layout = QHBoxLayout(quick_frame)
        quick_layout.setContentsMargins(12, 6, 12, 6)
        quick_layout.setSpacing(8)

        diagnose_btn = QPushButton("诊断代码")
        diagnose_btn.setFixedHeight(32)
        diagnose_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #DC2626; }}
        """)
        diagnose_btn.clicked.connect(self._diagnose_code)
        quick_layout.addWidget(diagnose_btn)

        quick_layout.addStretch()

        # 添加"加入屏幕内容"复选框
        from PyQt5.QtWidgets import QCheckBox
        self.context_checkbox = QCheckBox("加入屏幕内容")
        self.context_checkbox.setToolTip("勾选后，AI会自动识别你当前学习的知识点或练习的题目")
        self.context_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                color: {COLORS['text_secondary']};
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
            }}
        """)
        quick_layout.addWidget(self.context_checkbox)

        panel_layout.addWidget(quick_frame)

        # ===== 输入区 =====
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(10)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入问题...")
        self.input_box.setFixedHeight(45)
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(60, 45)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
        """)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        input_frame.setMaximumHeight(70)
        panel_layout.addWidget(input_frame)

    def _apply_palette(self):
        border_blue = COLORS['border']
        text_dark = COLORS['text_primary']

        self.setStyleSheet(f"""
            QWidget {{ font-family: 'Microsoft YaHei', 'PingFang SC'; color: {text_dark}; }}
            QPushButton {{
                background: {COLORS['glass_bg']};
                border: 1px solid {border_blue};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_alpha_hover']}; }}
            QFrame {{ background: {COLORS['glass_bg']}; border-radius: 16px; border: 1px solid {border_blue}; }}
            QTextBrowser {{
                background: white;
                border-radius: 0px;
                padding: 12px;
                border: none;
                font-size: 15px;
                line-height: 1.6;
            }}
            QTextEdit {{
                background: white;
                border-radius: 8px;
                border: 1px solid {border_blue};
                font-size: 15px;
                padding: 8px;
            }}
            QLabel {{ color: {text_dark}; }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(0, 6)
        shadow.setBlurRadius(22)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.main_button.setGraphicsEffect(shadow)

    def toggle(self):
        """展开/收起面板（带动画）"""
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

    def _get_resize_edge(self, pos):
        """检测鼠标位置 - 只在右上角返回缩放"""
        if not self.expanded:
            return None

        margin = self._RESIZE_MARGIN
        w = self.width()
        x = pos.x()
        y = pos.y()

        # 只有右上角可以缩放
        if x > w - margin and y < margin:
            return 'top-right'

        return None

    def _is_top_edge(self, pos):
        """检测是否在上边框（用于拖拽移动）"""
        if not self.expanded:
            return False
        margin = self._RESIZE_MARGIN
        return pos.y() < margin

    def _get_cursor_for_edge(self, edge):
        """根据边缘类型返回光标形状"""
        cursors = {
            'top-right': Qt.SizeBDiagCursor,
        }
        return cursors.get(edge, Qt.ArrowCursor)

    def _target_geometry(self, expanded):
        if self.anchor_pos is None:
            self._place_bottom_right()
        anchor = self.anchor_pos
        if expanded:
            # 使用面板的实际尺寸
            size = QSize(self.panel.width(), self.panel.height())
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
        # 面板填满整个控件
        self.panel.setGeometry(0, 0, self.width(), self.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_children_geometry()
        self.anchor_pos = self.geometry().bottomRight()

        # 根据面板宽度计算字体大小
        if self.expanded and self.width() > 100:
            scale = self.width() / self.PANEL_WIDTH
            new_size = max(13, int(self._base_font_size * scale))
            if new_size != self._current_font_size:
                self._current_font_size = new_size
                self._rebuild_chat()

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理输入框回车、按钮拖拽"""
        if hasattr(self, 'input_box') and obj == self.input_box:
            if event.type() == QEvent.KeyPress:
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    if not (event.modifiers() & Qt.ShiftModifier):
                        self._send_message()
                        return True

        if obj == self.main_button:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
                self.user_dragged = True
                self.main_button.setCursor(Qt.ClosedHandCursor)
                return False  # 不拦截点击
            if event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton and self.drag_offset is not None:
                if self.parent():
                    new_pos = self.parent().mapFromGlobal(event.globalPos() - self.drag_offset)
                    max_x = self.parent().width() - self.width()
                    max_y = self.parent().height() - self.height()
                    new_pos.setX(max(0, min(new_pos.x(), max_x)))
                    new_pos.setY(max(0, min(new_pos.y(), max_y)))
                    self.move(new_pos)
                    self.anchor_pos = self.geometry().bottomRight()
                return True
            if event.type() == QEvent.MouseButtonRelease:
                self.main_button.setCursor(Qt.OpenHandCursor)
                self.drag_offset = None
                return False
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        """鼠标按下 - 开始拖拽或缩放"""
        if event.button() == Qt.LeftButton:
            # 检查是否在右上角（缩放模式）
            edge = self._get_resize_edge(event.pos())
            if edge and self.expanded:
                self._resize_edge = edge
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return

            # 检查是否在上边框（拖拽移动模式）
            if self._is_top_edge(event.pos()) and self.expanded:
                self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
                self.user_dragged = True
                event.accept()
                return

            # 其他区域 - 允许拖拽移动
            self.drag_offset = event.pos()
            self.user_dragged = True
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动 - 拖拽或缩放"""
        # 缩放模式
        if self._resize_edge and event.buttons() & Qt.LeftButton:
            delta = event.globalPos() - self._resize_start_pos
            geo = self._resize_start_geometry
            min_w, min_h = 300, 400

            new_x = geo.x()
            new_y = geo.y()
            new_w = geo.width()
            new_h = geo.height()

            if 'right' in self._resize_edge:
                new_w = max(min_w, geo.width() + delta.x())
            if 'left' in self._resize_edge:
                new_w = max(min_w, geo.width() - delta.x())
                new_x = geo.x() + geo.width() - new_w
            if 'bottom' in self._resize_edge:
                new_h = max(min_h, geo.height() + delta.y())
            if 'top' in self._resize_edge:
                new_h = max(min_h, geo.height() - delta.y())
                new_y = geo.y() + geo.height() - new_h

            self.setGeometry(new_x, new_y, new_w, new_h)
            self.anchor_pos = self.geometry().bottomRight()
            event.accept()
            return

        # 普通拖拽
        if self.drag_offset is not None and event.buttons() & Qt.LeftButton:
            if self.parent():
                new_pos = self.parent().mapFromGlobal(event.globalPos() - self.drag_offset)
                max_x = self.parent().width() - self.width()
                max_y = self.parent().height() - self.height()
                new_pos.setX(max(0, min(new_pos.x(), max_x)))
                new_pos.setY(max(0, min(new_pos.y(), max_y)))
                self.move(new_pos)
                self.anchor_pos = self.geometry().bottomRight()
            else:
                self.move(event.globalPos() - self.drag_offset)
            event.accept()
            return

        # 非拖拽状态 - 更新光标
        if self.expanded:
            edge = self._get_resize_edge(event.pos())
            if edge:
                # 右上角显示对角线双箭头
                self.setCursor(Qt.SizeBDiagCursor)
            else:
                # 其他区域恢复默认箭头
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 结束拖拽或缩放"""
        self.drag_offset = None
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        if self.expanded:
            self.setCursor(Qt.ArrowCursor)

    # ==================== 上下文感知 ====================

    def _get_editor(self):
        if self._editor_widget is None:
            main_window = self.window()
            if hasattr(main_window, 'editor_widget'):
                self._editor_widget = main_window.editor_widget
        return self._editor_widget

    def _get_current_context(self):
        main_window = self.window()
        if not hasattr(main_window, 'stack'):
            return ""

        current_index = main_window.stack.currentIndex()
        if current_index == 0:
            self.current_module = self.MODULE_HOME
            return ""

        page = main_window.stack.widget(current_index)
        if not page:
            return ""

        if hasattr(page, 'content_widget'):
            widget = page.content_widget
            class_name = widget.__class__.__name__

            if class_name == 'KnowledgeWidget':
                self.current_module = self.MODULE_KNOWLEDGE
                if hasattr(widget, 'current_knowledge') and widget.current_knowledge:
                    kp = widget.current_knowledge
                    return f"当前学习知识点：{kp.title}\n内容：{kp.content[:200]}..."
                return "用户正在学习知识点"

            elif class_name == 'PracticeWidget':
                self.current_module = self.MODULE_PRACTICE
                if hasattr(widget, 'current_question') and widget.current_question:
                    q = widget.current_question
                    return f"当前题目：{q.question}\n类型：{q.type}"
                return "用户正在练习题目"

            elif class_name == 'EditorWidget':
                self.current_module = self.MODULE_EDITOR
                code = ""
                if hasattr(widget, 'code_editor'):
                    code = widget.code_editor.toPlainText().strip()
                if code:
                    return f"用户正在编写代码：\n```python\n{code[:500]}\n```"
                return "用户正在代码编辑器中"

            elif class_name == 'ExamWidget':
                self.current_module = self.MODULE_EXAM
                return None

            else:
                self.current_module = self.MODULE_OTHER
                return ""

        return ""

    def update_module_visibility(self):
        self._get_current_context()
        if self.current_module == self.MODULE_EXAM:
            self.hide()
            if self.panel.isVisible():
                self.panel.setVisible(False)
                self.expanded = False
        else:
            self.show()
            self.raise_()

    # ==================== 诊断代码 ====================

    def _diagnose_code(self):
        context = self._get_current_context()
        if self.current_module == self.MODULE_EXAM:
            self._append_message("assistant", "考试期间不能使用 AI 助手！")
            return

        editor = self._get_editor()
        if not editor:
            self._append_message("assistant", "未找到代码编辑器，请先打开代码编辑模块。")
            return

        code = ""
        output = ""
        if hasattr(editor, 'get_code_and_output'):
            code, output = editor.get_code_and_output()
        elif hasattr(editor, 'code_editor'):
            code = editor.code_editor.toPlainText().strip()
            if hasattr(editor, 'output_text'):
                output = editor.output_text.toPlainText().strip()

        if not code:
            self._append_message("assistant", "编辑器中没有代码，请先编写代码再进行诊断。")
            return

        prompt = f"""请分析以下 Python 代码的问题：

【代码内容】
```python
{code}
```

【运行输出/错误信息】
{output if output else "无输出"}

请提供：
1. 代码问题分析
2. 错误原因
3. 修复建议
4. 改进后的代码"""

        self._append_message("user", "请求诊断代码")
        self._stream_response([{"role": "user", "content": prompt}])

    # ==================== 快速提问 ====================

    def _show_quick_questions(self):
        questions = [
            "Python中列表和元组的区别是什么？",
            "如何在Python中读写文件？",
            "解释try-except异常处理机制",
            "Python函数的参数类型有哪些？",
            "什么是列表推导式？举个例子",
        ]
        menu_html = "<b>快速提问：</b><br><br>"
        for i, q in enumerate(questions, 1):
            menu_html += f"{i}. {q}<br>"
        self._append_message("assistant", menu_html)

    # ==================== 发送消息 ====================

    def _send_message(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            return

        self.input_box.clear()

        # 检查是否在考试模式
        self._get_current_context()
        if self.current_module == self.MODULE_EXAM:
            self._append_message("assistant", "考试期间不能使用 AI 助手！")
            return

        # 获取上下文（如果复选框勾选）
        context = None
        if self.context_checkbox.isChecked():
            context = self._get_current_context()
            if context:
                self._append_message("user", f"{text}\n\n[已识别上下文]")
            else:
                self._append_message("user", text)
        else:
            self._append_message("user", text)

        # 构建 API 消息（从 _messages 提取）
        api_messages = [{"role": msg['role'], "content": msg['content']} for msg in self._messages]
        if len(api_messages) > 20:
            api_messages = api_messages[-20:]

        self._stream_response(api_messages, context)

    # ==================== 流式响应 ====================

    def _stream_response(self, messages, context=None):
        if self.mimo_thread and self.mimo_thread.isRunning():
            self.mimo_thread.stop()
            self.mimo_thread.wait(2000)  # 最多等待2秒

        self._set_loading(True)
        self.current_response = ""
        self._append_message("assistant", "思考中...")

        self.mimo_thread = MimoStreamThread(messages, context=context)
        self.mimo_thread.chunk_received.connect(self._on_chunk)
        self.mimo_thread.finished.connect(self._on_finished)
        self.mimo_thread.error_occurred.connect(self._on_error)
        self.mimo_thread.start()

    def _on_chunk(self, chunk):
        self.current_response += chunk
        self._pending_update = True
        if not self._update_timer.isActive():
            self._update_timer.start(50)

    def _do_update_display(self):
        if self._pending_update and self.current_response:
            self._update_last_message(self.current_response)
            self._pending_update = False

    def _on_finished(self):
        self._set_loading(False)
        if self.current_response:
            # _messages 已经在 _append_message 中添加了，这里只更新内容
            self._update_last_message(self.current_response)
        else:
            self._replace_last_message("未收到有效回复，请重试。")

    def _on_error(self, error):
        self._set_loading(False)
        # 直接追加错误消息（不依赖正则匹配）
        self._remove_last_message()
        self._append_message("assistant", f"⚠️ {error}")

    def _set_loading(self, loading):
        self.loading_label.setVisible(loading)
        if loading:
            self.loading_label.setText("思考中...")

    # ==================== 消息显示 ====================

    def _append_message(self, role, content):
        """追加消息并重建聊天区"""
        self._messages.append({'role': role, 'content': content})
        self._rebuild_chat()

    def _update_last_message(self, content):
        """更新最后一条 AI 消息（仅更新最后一条，不重建全部）"""
        if not self._messages or self._messages[-1]['role'] != 'assistant':
            return

        self._messages[-1]['content'] = content

        # 保存滚动位置
        scrollbar = self.chat_area.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 10

        # 使用光标定位到最后一条消息并替换
        cursor = self.chat_area.textCursor()
        cursor.movePosition(cursor.End)

        # 选中最后一个 block（最后一条消息）
        cursor.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        cursor.movePosition(cursor.End, cursor.KeepAnchor)

        # 删除旧内容，插入新内容
        cursor.removeSelectedText()
        fs = self._current_font_size
        formatted = self._markdown_to_html(content)
        html = f"<div style='margin:8px 0;'><span style='background:#F1F5F9; padding:10px 14px; border-radius:12px 12px 12px 2px; display:inline-block; max-width:85%; font-size:{fs}px; line-height:1.5;'>{formatted}</span></div>"
        cursor.insertHtml(html)

        # 滚动到底部
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def _replace_last_message(self, content):
        """替换最后一条消息"""
        if self._messages:
            self._messages[-1] = {'role': 'assistant', 'content': content}
            self._update_last_message(content)

    def _remove_last_message(self):
        """删除最后一条消息"""
        if self._messages:
            self._messages.pop()
            # 重建聊天区（只在删除时重建）
            self._rebuild_chat()

    def _rebuild_chat(self):
        """重建整个聊天区（仅在消息列表变化时调用）"""
        scrollbar = self.chat_area.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 10

        self.chat_area.clear()
        for msg in self._messages:
            self._render_message(msg['role'], msg['content'])

        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def _render_message(self, role, content):
        """渲染单条消息到聊天区（不更新列表）"""
        fs = self._current_font_size
        if role == "user":
            html = f"<div style='text-align:right; margin:8px 0;'><span style='background:#2563EB; color:white; padding:10px 14px; border-radius:12px 12px 2px 12px; display:inline-block; max-width:80%; font-size:{fs}px; line-height:1.5;'>{content}</span></div>"
        else:
            formatted = self._markdown_to_html(content)
            html = f"<div style='margin:8px 0;'><span style='background:#F1F5F9; padding:10px 14px; border-radius:12px 12px 12px 2px; display:inline-block; max-width:85%; font-size:{fs}px; line-height:1.5;'>{formatted}</span></div>"
        self.chat_area.append(html)

    def _clear_conversation(self):
        self.current_response = ""
        self._messages = []
        self.chat_area.clear()
        self._append_message("assistant", "对话已清空，请问有什么可以帮助你的？")

    def _markdown_to_html(self, text):
        import re
        html = text

        def replace_code_block(match):
            code = match.group(2)
            code = code.replace('<', '&lt;').replace('>', '&gt;')
            return f'<pre style="background:#1E293B; color:#E2E8F0; padding:12px; border-radius:8px; margin:8px 0; overflow-x:auto;"><code>{code}</code></pre>'

        html = re.sub(r'```(\w*)\n(.*?)\n```', replace_code_block, html, flags=re.DOTALL)
        html = re.sub(r'`([^`]+)`', r'<code style="background:#E2E8F0; padding:2px 6px; border-radius:4px; font-family:Consolas,monospace;">\1</code>', html)
        html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
        html = re.sub(r'^###\s+(.+)$', r'<h4 style="margin:12px 0 6px 0;">\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^##\s+(.+)$', r'<h3 style="margin:14px 0 7px 0;">\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#\s+(.+)$', r'<h2 style="margin:16px 0 8px 0;">\1</h2>', html, flags=re.MULTILINE)

        lines = html.split('\n')
        in_list = False
        result_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    result_lines.append('<ul style="margin:8px 0; padding-left:20px;">')
                    in_list = True
                result_lines.append(f'<li style="margin:4px 0;">{stripped[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        if in_list:
            result_lines.append('</ul>')
        html = '\n'.join(result_lines)
        html = html.replace('\n', '<br>')
        return html

    def closeEvent(self, event):
        if self.mimo_thread and self.mimo_thread.isRunning():
            self.mimo_thread.stop()
            self.mimo_thread.wait(1000)
        super().closeEvent(event)
