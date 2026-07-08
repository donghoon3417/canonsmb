"""
imageRUNNER ADVANCE C4000/C4300 계열 모듈.

C3000 계열과 Remote UI 구조가 거의 동일할 가능성이 높으므로,
우선 iradv_3000의 로직을 그대로 재사용하고 차이가 발견되면
FORM_FIELDS만 오버라이드한다.
"""

from canon import iradv_3000
from canon.login import RemoteUISession
from logger import get_logger

log = get_logger(__name__)

# 3000 계열과 동일하면 이대로 위임, 다르면 이 파일에 별도 FORM_FIELDS를 정의해서 재구현
register_smb_onetouch = iradv_3000.register_smb_onetouch
verify_registration = iradv_3000.verify_registration
