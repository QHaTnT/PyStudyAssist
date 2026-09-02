# -*- mode: python ; coding: utf-8 -*-
"""
PyStudyAssist PyInstaller 打包配置
支持 Windows 单文件绿色版

打包内容：
- 主程序代码
- SQLite 初始数据库
- UI 图标素材
- 主题配置文件
"""
import os
import sys

block_cipher = None

# 项目根目录
ROOT_DIR = os.path.abspath('.')

# 收集数据文件
datas = []

# SQLite 数据库文件（初始数据）
db_files = [
    (os.path.join(ROOT_DIR, 'data', 'database', 'pystudyassist.db'), 'data/database'),
]
for src, dst in db_files:
    if os.path.exists(src):
        datas.append((src, dst))
        print(f"[打包] 添加数据库: {src}")

# 图标和资源文件
images_dir = os.path.join(ROOT_DIR, 'images')
if os.path.exists(images_dir):
    datas.append((images_dir, 'images'))
    print(f"[打包] 添加图片目录: {images_dir}")

# 资源目录
resources_dir = os.path.join(ROOT_DIR, 'resources')
if os.path.exists(resources_dir):
    datas.append((resources_dir, 'resources'))
    print(f"[打包] 添加资源目录: {resources_dir}")

# 配置文件
config_files = [
    os.path.join(ROOT_DIR, 'config.py'),
    os.path.join(ROOT_DIR, '.env'),
]
for config_path in config_files:
    if os.path.exists(config_path):
        datas.append((config_path, '.'))
        print(f"[打包] 添加配置文件: {config_path}")

# 排除不必要的模块（减小打包体积）
excludes = [
    # 测试相关
    'tkinter', '_tkinter',
    'matplotlib.tests',
    'numpy.tests',
    'pandas.tests',
    'scipy.tests',
    'pytest',
    'unittest',
    'test',

    # 开发工具
    'distutils',
    'setuptools',
    'pip',
    'wheel',

    # Jupyter 相关
    'IPython',
    'jupyter',
    'notebook',
    'notebook.auth',
    'notebook.base',
    'notebook.notebookapp',
    'IPython.core',
    'IPython.display',
    'IPython.kernel',

    # 其他不需要的模块
    'xmlrpc',
    'pydoc',
    'doctest',
    'argparse',  # 如果不需要命令行参数
]

a = Analysis(
    ['main.py'],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt5 核心
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',

        # 数据库相关
        'sqlalchemy',
        'sqlalchemy.dialects.mysql',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.pool',
        'pymysql',

        # 网络和加密
        'requests',
        'bcrypt',
        'hashlib',
        'json',

        # 标准库
        'sqlite3',
        'logging',
        'threading',
        'concurrent.futures',

        # 项目模块 - core
        'core',
        'core.database',
        'core.database.mysql_manager',
        'core.database.sqlite_manager',
        'core.database.sync_manager',
        'core.services',
        'core.services.auth_service',
        'core.services.data_service',
        'core.services.exam_service',

        # 项目模块 - ui
        'ui',
        'ui.windows',
        'ui.windows.main_window',
        'ui.windows.login_window',
        'ui.widgets',
        'ui.widgets.ai_assistant',
        'ui.widgets.editor_widget',
        'ui.widgets.knowledge_widget',
        'ui.widgets.practice_widget',
        'ui.widgets.exam_widget',
        'ui.widgets.progress_widget',
        'ui.widgets.mistakes_widget',
        'ui.widgets.statistics_widget',
        'ui.widgets.profile_widget',
        'ui.styles',
        'ui.styles.theme',
        'ui.styles.icons',
        'ui.styles.glass_components',

        # 项目模块 - utils
        'utils',
        'utils.code_executor',
        'utils.data_loader',

        # 项目模块 - models
        'models',
        'models.user',
        'models.knowledge',
        'models.question',
        'models.record',

        # 项目模块 - data
        'data',
        'data.seed',
        'data.seed.init_data',
        'data.seed.init_exams',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PyStudyAssist',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口（GUI 应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT_DIR, 'images', 'icon.ico') if os.path.exists(os.path.join(ROOT_DIR, 'images', 'icon.ico')) else None,
)

# 打包完成提示
print("\n" + "="*50)
print("打包配置完成！")
print(f"输出文件: PyStudyAssist.exe")
print(f"数据文件数量: {len(datas)}")
print("="*50 + "\n")
