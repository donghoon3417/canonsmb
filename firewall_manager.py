"""
Windows 방화벽에서 '파일 및 프린터 공유' 규칙 그룹을 활성화한다.
스캔투폴더(SMB, 포트 445)가 막혀 있으면 프린터에서 PC로 파일을 보낼 수 없다.
"""

import subprocess

from logger import get_logger

log = get_logger(__name__)


class FirewallManagerError(Exception):
    pass


FILE_PRINTER_SHARING_GROUP = "File and Printer Sharing"


def enable_file_printer_sharing() -> None:
    cmd = [
        "netsh", "advfirewall", "firewall", "set", "rule",
        f"group={FILE_PRINTER_SHARING_GROUP}", "new", "enable=Yes",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)

    if result.returncode != 0:
        log.error(f"방화벽 규칙 활성화 실패: {result.stderr.strip()}")
        raise FirewallManagerError(
            f"방화벽 설정 실패 (관리자 권한 필요): {result.stderr.strip()}"
        )
    log.info("방화벽: '파일 및 프린터 공유' 규칙 활성화 완료")


def open_smb_port_445() -> None:
    """일부 환경에서 위 그룹 규칙만으로 부족할 때를 대비한 명시적 포트 오픈."""
    cmd = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=CanonSMBAuto-SMB445",
        "dir=in", "action=allow", "protocol=TCP", "localport=445",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        log.warning(f"445 포트 개별 규칙 추가 실패(무시 가능): {result.stderr.strip()}")
    else:
        log.info("방화벽: TCP 445 포트 개별 허용 규칙 추가 완료")
