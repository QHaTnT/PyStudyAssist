# -*- coding: utf-8 -*-
"""
PyStudyAssist 入口文件
"""
import sys
import traceback


def run():
    """启动应用"""
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtGui import QFont
        from core.services.auth_service import auth_service
        from models.user import User

        app = QApplication(sys.argv)
        app.setFont(QFont("Microsoft YaHei", 13))
        app.setApplicationName("PyStudyAssist")

        def on_login_success(username, password):
            try:
                user = auth_service.get_current_user()
                if user:
                    # 启动数据同步
                    from core.database.sync_manager import sync_manager
                    sync_manager.startup_sync()
                    sync_manager.start_auto_sync()

                    from ui.windows.main_window import MainWindow
                    window = MainWindow(user)
                    app._main_window = window
                    window.show()
            except Exception as e:
                QMessageBox.critical(None, '错误', f'启动主窗口失败:\n{str(e)}')
                traceback.print_exc()

        from ui.windows.login_window import LoginWindow
        login_window = LoginWindow()
        login_window.finished.connect(on_login_success)
        login_window.show()

        sys.exit(app.exec_())

    except ImportError as e:
        print(f"\n[错误] 导入模块失败: {e}")
        print("\n请检查是否安装了所有依赖:")
        print("  pip install PyQt5 sqlalchemy pymysql requests bcrypt pillow")
        input("\n按 Enter 键退出...")
        sys.exit(1)

    except Exception as e:
        print(f"\n[错误] 程序启动失败: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        input("\n按 Enter 键退出...")
        sys.exit(1)


if __name__ == '__main__':
    run()
