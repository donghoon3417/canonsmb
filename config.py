"""
런타임 설정 컨테이너.

정책: 관리자 비밀번호는 디스크에 절대 저장하지 않는다.
      매 실행/매 작업마다 GUI에서 입력받아 메모리에서만 사용하고,
      작업이 끝나면 참조를 지운다(clear()).
"""

from dataclasses import dataclass, field
import getpass
import socket


@dataclass
class JobConfig:
    # --- 프린터 접속 정보 ---
    printer_ip: str = ""
    admin_id: str = "Administrator"
    admin_pw: str = ""  # 메모리에만 존재, 저장 금지

    # --- 원터치/SMB 설정 ---
    onetouch_name: str = "Scan"
    share_folder_name: str = "Scan"

    # --- PC 정보 (자동 수집) ---
    pc_name: str = field(default_factory=lambda: socket.gethostname())
    os_user: str = field(default_factory=lambda: getpass.getuser())

    def share_path(self) -> str:
        """바탕화면에 만들 Scan 폴더의 로컬 경로"""
        import os
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        return os.path.join(desktop, self.share_folder_name)

    def unc_path(self) -> str:
        """공유 후 프린터에 입력할 UNC 경로"""
        return f"\\\\{self.pc_name}\\{self.share_folder_name}"

    def clear_secret(self):
        """작업 종료 후 비밀번호를 메모리에서 제거"""
        self.admin_pw = ""

    def validate(self) -> list[str]:
        """필수값 누락 체크. 문제 목록을 반환(비어있으면 통과)"""
        errors = []
        if not self.printer_ip.strip():
            errors.append("프린터 IP를 입력하세요.")
        if not self.admin_id.strip():
            errors.append("관리자 ID를 입력하세요.")
        if not self.admin_pw:
            errors.append("관리자 비밀번호를 입력하세요.")
        if not self.share_folder_name.strip():
            errors.append("Scan 폴더 이름을 입력하세요.")
        if not self.onetouch_name.strip():
            errors.append("원터치 이름을 입력하세요.")
        return errors
