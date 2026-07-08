"""
Canon imageRUNNER ADVANCE Remote UI 로그인.

Remote UI는 기종/펌웨어에 따라 로그인 화면이
1) 관리자모드 라디오버튼 선택 후 비밀번호만 입력하는 방식
2) ID + 비밀번호를 함께 입력하는 방식
두 가지가 흔하다. 아래 코드는 두 케이스를 순차적으로 시도한다.

# TODO(확인필요): 실제 대상 기종의 로그인 화면을 F12로 열어
#   input의 name/id 속성이 아래와 다르면 SELECTORS 딕셔너리만 수정하면 된다.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PWTimeout

from logger import get_logger

log = get_logger(__name__)

# 기종별로 달라지면 여기 셀렉터만 오버라이드해서 쓴다.
SELECTORS = {
    "admin_mode_radio": "input[name='PageJump.SwitchIdentification'][value='administrator']",
    "login_id_input": "input[name='UserName'], input#loginname",
    "login_pw_input": "input[name='Password'], input#loginpass",
    "login_submit": "input[type='submit'], button#loginbtn",
}


class RemoteUILoginError(Exception):
    pass


@dataclass
class RemoteUISession:
    """호출부에서 with문으로 감싸 쓰는 세션 컨테이너."""
    playwright: object
    browser: Browser
    context: BrowserContext
    page: Page
    base_url: str

    def close(self):
        try:
            self.context.close()
        except Exception:
            pass
        try:
            self.browser.close()
        except Exception:
            pass
        try:
            self.playwright.stop()
        except Exception:
            pass


def login(ip: str, admin_id: str, admin_pw: str, headless: bool = True, timeout_ms: int = 15000) -> RemoteUISession:
    """
    Remote UI에 로그인하고 세션(브라우저 페이지)을 반환한다.
    호출부에서 다 쓰고 나면 반드시 session.close()를 호출해야 한다.
    """
    base_url = f"http://{ip}/"
    log.info(f"Remote UI 접속 시도: {base_url}")

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    try:
        page.goto(base_url, timeout=timeout_ms, wait_until="domcontentloaded")
    except PWTimeout:
        browser.close()
        pw.stop()
        raise RemoteUILoginError(f"프린터({ip})에 접속할 수 없습니다. IP/네트워크를 확인하세요.")

    # 관리자 모드 라디오가 있으면 선택
    try:
        radio = page.locator(SELECTORS["admin_mode_radio"])
        if radio.count() > 0:
            radio.first.check(timeout=2000)
    except Exception:
        pass  # 라디오가 없는 기종/화면일 수 있음

    # ID 입력란이 있으면 채움 (없는 기종도 있음 - 비밀번호만 쓰는 경우)
    try:
        id_input = page.locator(SELECTORS["login_id_input"])
        if id_input.count() > 0:
            id_input.first.fill(admin_id, timeout=2000)
    except Exception:
        pass

    try:
        pw_input = page.locator(SELECTORS["login_pw_input"])
        pw_input.first.fill(admin_pw, timeout=timeout_ms)
    except Exception as e:
        browser.close()
        pw.stop()
        raise RemoteUILoginError(
            "로그인 비밀번호 입력란을 찾지 못했습니다. "
            "SELECTORS['login_pw_input']을 실제 기종에 맞게 수정하세요."
        ) from e

    try:
        page.locator(SELECTORS["login_submit"]).first.click(timeout=timeout_ms)
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    except Exception as e:
        browser.close()
        pw.stop()
        raise RemoteUILoginError(f"로그인 버튼 클릭/이동 실패: {e}") from e

    # 로그인 실패 여부 대략 체크 (에러 문구 존재 유무)
    body_text = page.inner_text("body").lower()
    if any(kw in body_text for kw in ["invalid", "실패", "오류", "incorrect"]):
        browser.close()
        pw.stop()
        raise RemoteUILoginError("로그인 실패: ID 또는 비밀번호를 확인하세요.")

    log.info("Remote UI 로그인 성공")
    return RemoteUISession(playwright=pw, browser=browser, context=context, page=page, base_url=base_url)
