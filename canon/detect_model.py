"""
Remote UI 상단/장치정보 화면에서 기종명을 읽어 어떤 모듈(iradv_3000 등)을
사용할지 결정한다.

# TODO(확인필요): 장치정보 페이지 경로는 보통 /sysinfo.html 또는
#   포털 첫 화면 상단에 노출된다. 기종에 따라 다르면 DEVICE_INFO_PATHS에 추가.
"""

from __future__ import annotations

import re

from canon.login import RemoteUISession
from logger import get_logger

log = get_logger(__name__)

DEVICE_INFO_PATHS = [
    "sysinfo.html",
    "portal/portal.html",
    "",  # 로그인 후 첫 화면에 이미 모델명이 노출되는 경우
]

# 모델명 접두어 → 사용할 모듈 이름 매핑
MODEL_MODULE_MAP = {
    "C3200": "iradv_3000", "C3226": "iradv_3000", "C3326": "iradv_3000",
    "C3300": "iradv_3000", "C3330": "iradv_3000",
    "C3500": "iradv_3000", "C3520": "iradv_3000",
    "C3700": "iradv_3000", "C3720": "iradv_3000", "C3730": "iradv_3000",
    "C3800": "iradv_3000", "C3820": "iradv_3000", "C3826": "iradv_3000",
    "C3900": "iradv_3000", "C3922": "iradv_3000",
    "C4000": "iradv_4000", "C4300": "iradv_4000",
    "C5000": "iradv_5000", "C5200": "iradv_5000", "C5300": "iradv_5000",
}

MODEL_PATTERN = re.compile(r"(iR-?ADV\s*(?:DX\s*)?[A-Z]?\s*C?\d{3,4}[A-Za-z]*)", re.IGNORECASE)


class ModelDetectionError(Exception):
    pass


def detect_model_name(session: RemoteUISession) -> str:
    """장치정보 화면에서 모델명 문자열(예: 'iR-ADV DX C3826')을 찾아 반환."""
    page = session.page

    for path in DEVICE_INFO_PATHS:
        url = session.base_url + path
        try:
            page.goto(url, timeout=8000, wait_until="domcontentloaded")
        except Exception:
            continue

        text = page.inner_text("body")
        match = MODEL_PATTERN.search(text)
        if match:
            model = re.sub(r"\s+", " ", match.group(1)).strip()
            log.info(f"기종 인식 성공: {model}")
            return model

    raise ModelDetectionError(
        "기종명을 자동으로 찾지 못했습니다. "
        "detect_model.py의 DEVICE_INFO_PATHS / MODEL_PATTERN을 확인하세요."
    )


def resolve_module_name(model_name: str) -> str:
    """모델명 문자열에서 C0000 형태 코드를 추출해 모듈명으로 매핑."""
    code_match = re.search(r"C\d{3,4}[A-Za-z]*", model_name.upper())
    if not code_match:
        raise ModelDetectionError(f"모델 코드 파싱 실패: '{model_name}'")

    code = code_match.group(0)
    # 정확 매치 우선, 없으면 앞자리(예: C382x → C3800 계열)로 근사 매치
    if code in MODEL_MODULE_MAP:
        return MODEL_MODULE_MAP[code]

    prefix = code[:5]  # 'C3826' -> 'C3826'... 계열 판단용으로 4자리도 시도
    for known_code, module in MODEL_MODULE_MAP.items():
        if code.startswith(known_code[:4]):
            log.info(f"'{code}'를 '{known_code}' 계열로 근사 매치 → {module}")
            return module

    raise ModelDetectionError(
        f"'{model_name}'({code})에 대응하는 모듈이 없습니다. "
        f"MODEL_MODULE_MAP에 추가해주세요."
    )


def detect_and_resolve(session: RemoteUISession) -> tuple[str, str]:
    """(모델명 문자열, 모듈명) 튜플 반환."""
    model_name = detect_model_name(session)
    module_name = resolve_module_name(model_name)
    return model_name, module_name
