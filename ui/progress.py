"""진행상태 체크리스트 위젯 (□ 항목들을 순서대로 체크)."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox


STEP_LABELS = [
    "Scan폴더 생성",
    "공유",
    "Everyone 권한",
    "방화벽",
    "RemoteUI 로그인",
    "모델확인",
    "SMB등록",
    "완료",
]


class ProgressChecklist(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        self._boxes: dict[str, QCheckBox] = {}

        for label in STEP_LABELS:
            box = QCheckBox(label)
            box.setEnabled(False)  # 사용자가 직접 못 누르게, 표시 전용
            self._boxes[label] = box
            layout.addWidget(box)

    def mark_done(self, label: str):
        if label in self._boxes:
            self._boxes[label].setChecked(True)

    def reset(self):
        for box in self._boxes.values():
            box.setChecked(False)
