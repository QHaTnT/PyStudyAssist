# -*- coding: utf-8 -*-
"""
认证服务
处理用户登录、注册、会话管理
"""
from typing import Optional, Dict
from core.database.sqlite_manager import db
from models.user import User


class AuthService:
    """认证服务"""

    def __init__(self):
        self.current_user: Optional[User] = None

    def login(self, username: str, password: str) -> Optional[User]:
        """
        用户登录
        :param username: 用户名
        :param password: 密码
        :return: User 对象或 None
        """
        user_data = db.verify_user(username, password)
        if user_data:
            self.current_user = User.from_dict(user_data)
            return self.current_user
        return None

    def register(self, username: str, password: str, nickname: str = None) -> Optional[int]:
        """
        用户注册
        :param username: 用户名
        :param password: 密码
        :param nickname: 昵称
        :return: 用户 ID 或 None（如果用户名已存在）
        """
        return db.create_user(username, password, nickname)

    def logout(self):
        """用户登出"""
        self.current_user = None

    def get_current_user(self) -> Optional[User]:
        """获取当前登录用户"""
        return self.current_user

    def update_profile(self, **kwargs) -> bool:
        """
        更新用户资料
        :param kwargs: 要更新的字段
        :return: 是否成功
        """
        if not self.current_user:
            return False

        success = db.update_user(self.current_user.id, **kwargs)
        if success:
            for key, value in kwargs.items():
                if hasattr(self.current_user, key):
                    setattr(self.current_user, key, value)
        return success

    def get_user_stats(self) -> Dict:
        """获取用户统计信息"""
        if not self.current_user:
            return {}
        return db.get_user_statistics(self.current_user.id)


# 全局实例
auth_service = AuthService()
