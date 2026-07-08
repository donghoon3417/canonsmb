"""메인 윈도우 - Canon SMB Auto Setup"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QGroupBox, QMessageBox,
)
from PySide6.QtCore import Qt

from config import JobConfig
from ui.progress import ProgressChecklist
from ui.worker import SMBAutoWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Canon SMB Auto Setup")
        self.resize(560, 640)

        self.worker: SMBAutoWorker | None = None
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- 입력 폼 ---
        form_group = QGroupBox("Canon SMB Auto Setup")
        form = QFormLayout()
        form_group.setLayout(form)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("예: 192.168.0.50")
        form.addRow("프린터 IP", self.ip_input)

        self.admin_id_input = QLineEdit("Administrator")
        form.addRow("관리자 ID", self.admin_id_input)

        self.admin_pw_input = QLineEdit("7654321")
        self.admin_pw_input.setEchoMode(QLineEdit.Password)
        form.addRow("관리자 PW", self.admin_pw_input)

        self.onetouch_input = QLineEdit("Scan")
        form.addRow("원터치 이름", self.onetouch_input)

        self.share_input = QLineEdit("Scan")
        form.addRow("Scan 폴더", self.share_input)

        root.addWidget(form_group)

        # --- 실행 버튼 ---
        self.run_button = QPushButton("SMB 자동설정")
        self.run_button.clicked.connect(self._on_run_clicked)
        root.addWidget(self.run_button)

        # --- 진행상태 ---
        progress_group = QGroupBox("진행상태")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)
        self.checklist = ProgressChecklist()
        progress_layout.addWidget(self.checklist)
        root.addWidget(progress_group)

        # --- 로그 ---
        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_layout.addWidget(self.log_view)
        root.addWidget(log_group, stretch=1)

        # --- 향후 확장 버튼 영역 (지금은 비활성 안내만) ---
        expand_group = QGroupBox("이후 확장")
        expand_layout = QHBoxLayout()
        expand_group.setLayout(expand_layout)
        for name in ["이메일설정", "LDAP", "FTP", "주소록백업/복원"]:
            btn = QPushButton(name)
            btn.setEnabled(False)
            btn.setToolTip("추후 모듈 추가 예정")
            expand_layout.addWidget(btn)
        root.addWidget(expand_group)

    # -------------------------------------------------------------- 동작
    def _collect_config(self) -> JobConfig:
        cfg = JobConfig()
        cfg.printer_ip = self.ip_input.text().strip()
        cfg.admin_id = self.admin_id_input.text().strip()
        cfg.admin_pw = self.admin_pw_input.text()
        cfg.onetouch_name = self.onetouch_input.text().strip()
        cfg.share_folder_name = self.share_input.text().strip()
        return cfg

    def _on_run_clicked(self):
        cfg = self._collect_config()
        errors = cfg.validate()
        if errors:
            QMessageBox.warning(self, "입력값 확인", "\n".join(errors))
            return

        self.checklist.reset()
        self.log_view.clear()
        self.run_button.setEnabled(False)
        self.run_button.setText("진행 중...")

        self.worker = SMBAutoWorker(cfg)
        self.worker.step_done.connect(self.checklist.mark_done)
        self.worker.log_message.connect(self._append_log)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished_ok.connect(self._on_success)
        self.worker.start()

    def _append_log(self, text: str):
        self.log_view.append(text)

    def _on_failed(self, message: str):
        self._append_log(f"[실패] {message}")
        QMessageBox.critical(self, "설정 실패", message)
        self._reset_run_button()

    def _on_success(self, message: str):
        self._append_log(f"[완료] {message}")
        QMessageBox.information(self, "설정 완료", message)
        self._reset_run_button()

    def _reset_run_button(self):
        self.run_button.setEnabled(True)
        self.run_button.setText("SMB 자동설정")
