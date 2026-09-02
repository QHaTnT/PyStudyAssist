# -*- coding: utf-8 -*-
"""
业务服务层
提供认证、数据、考试等服务
"""
from core.services.auth_service import auth_service
from core.services.data_service import data_service
from core.services.exam_service import exam_service

__all__ = ['auth_service', 'data_service', 'exam_service']
