"""
NTFS 권한 설정 (icacls).

SMB 공유 권한과 NTFS 파일시스템 권한은 별개이므로,
프린터가 스캔 파일을 실제로 써넣을 수 있으려면 NTFS 쪽도 Everyone: Full Control이 필요하다.
"""

import subprocess

from logger import get_logger

log = get_logger(__name__)


class PermissionManagerError(Exception):
    pass


def grant_everyone_full_control(folder_path: str) -> None:
    cmd = ["icacls", folder_path, "/grant", "Everyone:(OI)(CI)F", "/T"]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)

    if result.returncode != 0:
        log.error(f"권한 설정 실패: {result.stderr.strip()}")
        raise PermissionManagerError(
            f"NTFS 권한 설정 실패 (관리자 권한 필요): {result.stderr.strip()}"
        )
    log.info(f"Everyone Full Control 권한 부여 완료: {folder_path}")
