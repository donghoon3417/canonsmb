"""
GUI를 막지 않도록 QThread에서 전체 파이프라인을 실행한다.

파이프라인:
  1. Scan폴더 생성
  2. 공유
  3. Everyone 권한
  4. 방화벽
  5. RemoteUI 로그인
  6. 모델확인
  7. SMB등록 (+ 등록확인)
  8. 완료
"""

from PySide6.QtCore import QThread, Signal

import share_manager
import permission_manager
import firewall_manager
from config import JobConfig
from canon import login as canon_login
from canon import detect_model
from canon.module_loader import load_module
from logger import get_logger

log = get_logger(__name__)


class SMBAutoWorker(QThread):
    step_done = Signal(str)          # 체크리스트 라벨
    log_message = Signal(str)        # 로그 텍스트
    failed = Signal(str)             # 에러 메시지
    finished_ok = Signal(str)        # 성공 메시지

    def __init__(self, cfg: JobConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg

    def _log(self, msg: str):
        log.info(msg)
        self.log_message.emit(msg)

    def run(self):
        session = None
        try:
            errors = self.cfg.validate()
            if errors:
                self.failed.emit("\n".join(errors))
                return

            # 1. Scan 폴더 생성
            self._log(f"바탕화면에 폴더 생성 중: {self.cfg.share_path()}")
            share_manager.create_folder(self.cfg.share_path())
            self.step_done.emit("Scan폴더 생성")

            # 2. 공유
            self._log(f"SMB 공유 등록 중: {self.cfg.share_folder_name}")
            share_manager.create_share(self.cfg.share_folder_name, self.cfg.share_path())
            self.step_done.emit("공유")

            # 3. Everyone 권한
            self._log("NTFS 권한(Everyone Full Control) 설정 중...")
            permission_manager.grant_everyone_full_control(self.cfg.share_path())
            self.step_done.emit("Everyone 권한")

            # 4. 방화벽
            self._log("방화벽 규칙(파일 및 프린터 공유) 활성화 중...")
            firewall_manager.enable_file_printer_sharing()
            firewall_manager.open_smb_port_445()
            self.step_done.emit("방화벽")

            # 5. RemoteUI 로그인
            self._log(f"프린터 Remote UI 로그인 시도: {self.cfg.printer_ip}")
            session = canon_login.login(
                ip=self.cfg.printer_ip,
                admin_id=self.cfg.admin_id,
                admin_pw=self.cfg.admin_pw,
                headless=True,
            )
            self.step_done.emit("RemoteUI 로그인")

            # 6. 모델확인
            self._log("기종 자동 인식 중...")
            model_name, module_name = detect_model.detect_and_resolve(session)
            self._log(f"기종 인식: {model_name} → 모듈: {module_name}")
            self.step_done.emit("모델확인")

            # 7. SMB 등록
            self._log(f"SMB 원터치 등록 중: '{self.cfg.onetouch_name}'")
            module = load_module(module_name)
            module.register_smb_onetouch(
                session=session,
                onetouch_name=self.cfg.onetouch_name,
                pc_name=self.cfg.pc_name,
                share_folder_name=self.cfg.share_folder_name,
                os_username=self.cfg.os_user,
                os_password="",  # Everyone 공유이므로 기본은 비워둠. 필요시 GUI에 필드 추가.
            )
            ok = module.verify_registration(session, self.cfg.onetouch_name)
            if not ok:
                raise RuntimeError("등록은 진행됐지만 주소록에서 확인되지 않았습니다. 수동 확인이 필요합니다.")
            self.step_done.emit("SMB등록")

            # 8. 완료
            self.step_done.emit("완료")
            self.finished_ok.emit(
                f"SMB 자동설정 완료!\n"
                f"프린터에서 '{self.cfg.onetouch_name}' 원터치로 스캔하면 "
                f"{self.cfg.unc_path()} 에 저장됩니다."
            )

        except Exception as e:
            log.exception("SMB 자동설정 실패")
            self.failed.emit(str(e))
        finally:
            if session:
                session.close()
            self.cfg.clear_secret()
