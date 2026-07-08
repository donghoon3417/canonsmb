"""
imageRUNNER ADVANCE C5000/C5200/C5300 계열 모듈.
현재는 3000 계열 로직을 재사용. 실제 기기에서 검증 후 필요하면 분리 구현.
"""

from canon import iradv_3000

register_smb_onetouch = iradv_3000.register_smb_onetouch
verify_registration = iradv_3000.verify_registration
