"""모듈명 문자열('iradv_3000' 등)을 실제 파이썬 모듈로 로딩."""

import importlib


def load_module(module_name: str):
    return importlib.import_module(f"canon.{module_name}")
