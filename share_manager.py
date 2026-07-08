"""
바탕화면 Scan 폴더 생성 + Windows SMB 공유 등록.

Windows 표준 명령(net share)을 사용한다.
관리자 권한(UAC 상승)으로 실행되어야 공유 등록이 성공한다.
"""

import os
import subprocess

from logger import get_logger

log = get_logger(__name__)


class ShareManagerError(Exception):
    pass


def create_folder(path: str) -> None:
    """폴더가 없으면 생성한다."""
    if os.path.isdir(path):
        log.info(f"폴더가 이미 존재합니다: {path}")
        return
    os.makedirs(path, exist_ok=True)
    log.info(f"폴더 생성 완료: {path}")


def is_shared(share_name: str) -> bool:
    """이미 같은 이름으로 공유되어 있는지 확인."""
    result = subprocess.run(
        ["net", "share"], capture_output=True, text=True, shell=False
    )
    return share_name.lower() in result.stdout.lower()


def create_share(share_name: str, folder_path: str) -> None:
    """
    net share 명령으로 SMB 공유를 생성한다.
    이미 존재하면 먼저 제거 후 재생성해서 항상 folder_path를 가리키도록 한다.
    """
    if is_shared(share_name):
        log.info(f"기존 공유 '{share_name}' 발견 → 제거 후 재생성")
        remove_share(share_name)

    cmd = ["net", "share", f"{share_name}={folder_path}", "/GRANT:Everyone,FULL"]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)

    if result.returncode != 0:
        log.error(f"공유 생성 실패: {result.stderr.strip()}")
        raise ShareManagerError(
            f"SMB 공유 생성 실패 (관리자 권한으로 실행했는지 확인하세요): {result.stderr.strip()}"
        )
    log.info(f"SMB 공유 생성 완료: \\\\{{PC}}\\{share_name} → {folder_path}")


def remove_share(share_name: str) -> None:
    subprocess.run(
        ["net", "share", share_name, "/DELETE", "/Y"],
        capture_output=True,
        text=True,
        shell=False,
    )
    log.info(f"공유 제거: {share_name}")


def setup_share(share_name: str, folder_path: str) -> None:
    """폴더 생성 + 공유 등록을 한 번에 수행."""
    create_folder(folder_path)
    create_share(share_name, folder_path)
