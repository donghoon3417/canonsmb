# Canon SMB Auto Setup

Canon imageRUNNER ADVANCE DX 시리즈(C3200~C3900 계열, 이후 C4000/C5000 확장)를
위한 **바탕화면 Scan 공유 + Remote UI SMB 원터치 자동 등록** 도구.

## 설치 (Windows, 관리자 PC)

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## 실행

**반드시 관리자 권한으로 실행**하세요 (`net share`, `icacls`, `netsh`가
관리자 권한을 요구합니다).

```bat
python main.py
```

## 동작 순서

1. 바탕화면에 Scan 폴더 생성
2. SMB 공유 등록 (`net share`)
3. NTFS Everyone Full Control 권한 부여 (`icacls`)
4. 방화벽 파일/프린터 공유 규칙 활성화 (`netsh advfirewall`)
5. 프린터 Remote UI 로그인 (Playwright)
6. 기종 자동 인식 → 해당 모듈(`canon/iradv_3000.py` 등) 자동 선택
7. 주소록에 SMB 원터치 등록 + 등록 여부 확인
8. 완료

## 기종 확장하는 방법

`canon/detect_model.py`의 `MODEL_MODULE_MAP`에 새 모델 코드를 추가하고,
필요하면 `canon/iradv_4000.py`처럼 새 모듈 파일을 만들어
`register_smb_onetouch`, `verify_registration` 두 함수만 구현하면 됩니다.

## 실기기 연동 전 반드시 확인할 것

Remote UI의 로그인 화면 및 주소록 등록 화면의 HTML 구조는 기종/펌웨어별로
조금씩 다릅니다. 실제 프린터의 Remote UI를 브라우저로 열고 F12(개발자도구)로
아래 두 파일의 셀렉터를 확인/수정하세요.

- `canon/login.py` → `SELECTORS`
- `canon/iradv_3000.py` → `ADDRESS_BOOK_PATH`, `ADDRESS_ADD_PATH`, `FORM_FIELDS`

디버깅할 때는 `canon_login.login(..., headless=False)`로 호출하면
실제 브라우저 창이 떠서 어느 단계에서 막히는지 눈으로 확인할 수 있습니다.

## 향후 확장 (모듈만 추가하면 됨)

- 이메일/SMTP 자동설정 (Gmail, Office365, 네이버메일)
- LDAP
- 주소록 백업/복원
- 관리자 암호 변경
- 사용자 관리 / 펌웨어 확인
- 프린터 IP 자동 검색(대역 스캔)
- 실패 원인 자동 분석(공유 권한/방화벽/네트워크 구분)

## 보안 정책

관리자 비밀번호는 디스크에 저장하지 않습니다. GUI에서 입력받아 메모리에서만
사용하고, 작업 완료 즉시 제거합니다(`config.JobConfig.clear_secret`).
로그에도 비밀번호가 남지 않도록 마스킹 필터가 적용되어 있습니다.
