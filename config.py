# -*- coding: utf-8 -*-
"""
PyStudyAssist 配置管理
使用环境变量 + 默认值，支持 .env 文件
"""
import os
from dataclasses import dataclass, field
from typing import List


def load_env_file():
    """加载 .env 文件（如果存在）"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


# 加载 .env 文件
load_env_file()


@dataclass
class DatabaseConfig:
    """数据库配置"""
    # SQLite
    sqlite_path: str = os.getenv('SQLITE_PATH', 'data/database/pystudyassist.db')

    # MySQL
    mysql_host: str = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port: int = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user: str = os.getenv('MYSQL_USER', 'root')
    mysql_password: str = os.getenv('MYSQL_PASSWORD', '')
    mysql_database: str = os.getenv('MYSQL_DATABASE', 'pystudyassist_cloud')
    mysql_charset: str = 'utf8mb4'


@dataclass
class AIConfig:
    """AI 助手配置"""
    api_url: str = 'https://api.xiaomimimo.com/v1/chat/completions'
    api_key: str = os.getenv('MIMO_API_KEY', '')
    model: str = 'mimo-v2.5-pro'
    temperature: float = 0.6
    max_tokens: int = 4096
    timeout: int = 30


@dataclass
class SecurityConfig:
    """安全配置"""
    bcrypt_rounds: int = 12
    code_timeout: int = 5
    max_output_length: int = 10000


@dataclass
class SyncConfig:
    """同步配置"""
    auto_sync: bool = True
    sync_interval: int = 300  # 秒
    max_offline_queue: int = 1000
    max_retries: int = 3
    retry_delay: int = 5  # 秒


@dataclass
class UIConfig:
    """UI 配置"""
    app_title: str = 'PyStudyAssist'
    window_width: int = 1200
    window_height: int = 800
    min_width: int = 1000
    min_height: int = 600


@dataclass
class KnowledgeConfig:
    """知识点配置"""
    categories: List[str] = field(default_factory=lambda: [
        'Python基础', '数据类型', '运算符与表达式', '流程控制',
        '函数', '字符串处理', '列表与元组', '字典与集合',
        '文件操作', '异常处理', '面向对象编程', '模块与包', '常用标准库'
    ])

    question_types: dict = field(default_factory=lambda: {
        'choice': '选择题',
        'judge': '判断题',
        'fill': '填空题',
        'code': '编程题'
    })

    difficulty_levels: dict = field(default_factory=lambda: {
        'easy': '简单',
        'medium': '中等',
        'hard': '困难'
    })


@dataclass
class Config:
    """主配置类"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)

    # 默认用户
    default_username: str = '1'
    default_password: str = '1'


# 全局配置实例
config = Config()

# 兼容旧代码的配置字典
MIMO_CONFIG = {
    'api_url': config.ai.api_url,
    'api_key': config.ai.api_key,
    'model': config.ai.model,
    'temperature': config.ai.temperature,
    'max_tokens': config.ai.max_tokens,
    'timeout': config.ai.timeout,
}

EDITOR_CONFIG = {
    'font_family': 'Consolas',
    'font_size': 14,
    'tab_size': 4,
    'timeout': config.security.code_timeout,
}

THEME_COLORS = {
    'primary': '#1976D2',
    'secondary': '#424242',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#F44336',
    'background': '#FAFAFA',
    'surface': '#FFFFFF',
    'text': '#212121',
}
