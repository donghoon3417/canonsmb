"""
imageRUNNER ADVANCE DX C3200/C3300/C3500/C3700/C3800/C3900 계열
Remote UI 주소록에 SMB(파일 전송) 원터치를 등록하는 모듈.

Remote UI 주소록 등록 흐름 (전형적인 구조):
  1. 주소록 관리 화면 진입 (AddressBook)
  2. '등록' 버튼 → 새 항목 추가 화면
  3. 종류(파일)를 SMB로 선택
  4. 이름 / 호스트 이름(UNC) / 사용자명 / 비밀번호 / 공유 폴더 경로 입력
  5. 저장

# TODO(확인필요): 이 파일의 URL 경로(ADDRESS_BOOK_ADD_PATH)와
#   FORM_FIELDS의 name 값은 실제 기종/펌웨어에서 F12로 반드시 재확인하세요.
#   Remote UI는 frame 안에 폼이 들어있는 경우가 많아 필요 시
#   page.frame_locator(...)로 바꿔야 할 수도 있습니다.
"""

from __future__ import annotations

from playwright.sync_api import Page

from canon.login import RemoteUISession
from logger import get_logger

log = get_logger(__name__)

# --- 경로/셀렉터: 기종별로 다르면 여기만 고치면 된다 ---
ADDRESS_BOOK_PATH = "AddressBook/AddBookMain.html"
ADDRESS_ADD_PATH = "AddressBook/AddBookAddRegist.html"

FORM_FIELDS = {
    "type_smb_radio": "input[name='addressType'][value='smb']",
    "name_input": "input[name='name']",
    "host_input": "input[name='host']",           # \\PC명 또는 IP
    "folder_path_input": "input[name='folderPath']",  # 공유폴더명
    "username_input": "input[name='username']",
    "password_input": "input[name='password']",
    "save_button": "input[type='submit'][value*='OK'], button#saveBtn",
}


class SMBRegistrationError(Exception):
    pass


def register_smb_onetouch(
    session: RemoteUISession,
    onetouch_name: str,
    pc_name: str,
    share_folder_name: str,
    os_username: str,
    os_password: str,
    timeout_ms: int = 15000,
) -> None:
    """
    주소록에 SMB 원터치 하나를 등록한다.

    onetouch_name   : 프린터 터치패널에 표시될 이름 (예: 'Scan')
    pc_name         : SMB 대상 PC 이름 (예: 'DESKTOP-KJ92A')
    share_folder_name: 공유 폴더 이름 (예: 'Scan')
    os_username/os_password: 공유 폴더에 접근할 Windows 계정 (Everyone 공유면 생략 가능한 기종도 있음)
    """
    page: Page = session.page

    log.info(f"주소록 등록 화면 진입 시도: {onetouch_name}")
    page.goto(session.base_url + ADDRESS_BOOK_PATH, timeout=timeout_ms, wait_until="domcontentloaded")

    # '등록' 버튼을 눌러 추가 화면으로 이동하는 기종도 있고,
    # 바로 ADDRESS_ADD_PATH로 진입 가능한 기종도 있다. 둘 다 시도.
    try:
        add_btn = page.get_by_text("등록", exact=False)
        if add_btn.count() > 0:
            add_btn.first.click(timeout=3000)
            page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        else:
            page.goto(session.base_url + ADDRESS_ADD_PATH, timeout=timeout_ms, wait_until="domcontentloaded")
    except Exception:
        page.goto(session.base_url + ADDRESS_ADD_PATH, timeout=timeout_ms, wait_until="domcontentloaded")

    try:
        # 종류를 SMB(파일)로 선택
        smb_radio = page.locator(FORM_FIELDS["type_smb_radio"])
        if smb_radio.count() > 0:
            smb_radio.first.check(timeout=3000)

        page.locator(FORM_FIELDS["name_input"]).first.fill(onetouch_name, timeout=timeout_ms)
        page.locator(FORM_FIELDS["host_input"]).first.fill(pc_name, timeout=timeout_ms)
        page.locator(FORM_FIELDS["folder_path_input"]).first.fill(share_folder_name, timeout=timeout_ms)

        # 계정 정보는 없는 기종/필드도 있으니 존재할 때만 채움
        user_field = page.locator(FORM_FIELDS["username_input"])
        if user_field.count() > 0 and os_username:
            user_field.first.fill(os_username, timeout=3000)

        pw_field = page.locator(FORM_FIELDS["password_input"])
        if pw_field.count() > 0 and os_password:
            pw_field.first.fill(os_password, timeout=3000)

        page.locator(FORM_FIELDS["save_button"]).first.click(timeout=timeout_ms)
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)

    except Exception as e:
        raise SMBRegistrationError(
            "주소록 SMB 등록 중 오류. FORM_FIELDS 셀렉터가 실제 화면과 다를 수 있습니다. "
            f"원인: {e}"
        ) from e

    body_text = page.inner_text("body").lower()
    if any(kw in body_text for kw in ["error", "오류", "실패", "invalid"]):
        raise SMBRegistrationError("등록 실패 응답이 감지되었습니다. 화면 문구를 확인하세요.")

    log.info(f"SMB 원터치 등록 완료: '{onetouch_name}' → \\\\{pc_name}\\{share_folder_name}")


def verify_registration(session: RemoteUISession, onetouch_name: str, timeout_ms: int = 10000) -> bool:
    """등록 후 주소록 목록에 실제로 이름이 나타나는지 확인."""
    page = session.page
    page.goto(session.base_url + ADDRESS_BOOK_PATH, timeout=timeout_ms, wait_until="domcontentloaded")
    body_text = page.inner_text("body")
    found = onetouch_name in body_text
    log.info(f"등록 확인: '{onetouch_name}' {'발견됨' if found else '발견 안됨'}")
    return found
