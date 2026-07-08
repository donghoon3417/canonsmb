"""
Canon SMB Auto Setup - 진입점

실행:
    python main.py

주의:
    - Windows에서 관리자 권한(우클릭 → 관리자 권한으로 실행)으로 실행해야
      net share / icacls / netsh 명령이 성공합니다.
    - 최초 1회 `playwright install chromium` 실행 필요.
"""

import sys

from PySide6.QtWidgets import QApplication

from ui.mainwindow import MainWindow
from logger import get_logger

log = get_logger(__name__)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    log.info("Canon SMB Auto Setup 시작")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
