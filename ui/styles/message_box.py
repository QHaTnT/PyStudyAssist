# -*- coding: utf-8 -*-
"""
统一的 QMessageBox 样式工具
确保所有模块使用一致的弹窗样式
"""
from PyQt5.QtWidgets import QMessageBox, QWidget


_MSG_STYLE = """
QMessageBox {
    background-color: white;
    font-size: 16px;
}
QMessageBox QLabel {
    color: #1E293B;
    font-size: 16px;
    min-width: 300px;
}
QMessageBox QPushButton {
    background: #2563EB;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 14px;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background: #1D4ED8;
}
"""

_DANGER_STYLE = """
QMessageBox {
    background-color: white;
    font-size: 16px;
}
QMessageBox QLabel {
    color: #1E293B;
    font-size: 16px;
    min-width: 300px;
}
QMessageBox QPushButton {
    background: #EF4444;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 14px;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background: #DC2626;
}
"""


def show_info(parent: QWidget, title: str, text: str):
    """显示提示弹窗"""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QMessageBox.Information)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet(_MSG_STYLE)
    msg.exec_()


def show_warning(parent: QWidget, title: str, text: str):
    """显示警告弹窗"""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QMessageBox.Warning)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet(_MSG_STYLE)
    msg.exec_()


def show_error(parent: QWidget, title: str, text: str):
    """显示错误弹窗"""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QMessageBox.Critical)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet(_DANGER_STYLE)
    msg.exec_()


def ask_question(parent: QWidget, title: str, text: str) -> bool:
    """显示确认弹窗，返回是否点击了 Yes"""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QMessageBox.Question)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    msg.setStyleSheet(_MSG_STYLE)
    return msg.exec_() == QMessageBox.Yes
