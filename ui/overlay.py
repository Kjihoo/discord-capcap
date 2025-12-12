from PyQt6 import QtWidgets, QtCore, QtGui
from ui.overlay_caption_manager import CaptionManager


class CaptionOverlay(QtWidgets.QWidget):
    caption_changed = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # 항상 위 + 테두리 없게 + 투명 배경
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 위치: 화면 아래 중앙
        screen = QtGui.QGuiApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.8)
        height = 80
        x = int((screen.width() - width) / 2)
        y = int(screen.height() - height - 80)
        self.setGeometry(x, y, width, height)

        # ---------------- UI ----------------
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._bg = QtWidgets.QLabel(self)
        self._bg.setGeometry(0, 0, width, height)
        self._bg.setStyleSheet(
            "background-color: rgba(0, 0, 0, 160);"
            "border-radius: 16px;"
        )

        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            "color: white;"
            "font-size: 22px;"
            "font-weight: 600;"
        )

        layout.addWidget(self.label)

        # ✅ 자막 관리기 복구
        self.caption_manager = CaptionManager(
            max_chars_per_line=25,
            max_lines=2,
        )

        self.caption_changed.connect(self._on_caption_changed)

        # 우클릭 종료 메뉴
        self._setup_context_menu()

    def _setup_context_menu(self):
        self.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.ActionsContextMenu
        )

        quit_action = QtGui.QAction("종료", self)
        quit_action.triggered.connect(QtWidgets.QApplication.quit)
        self.addAction(quit_action)

    def _on_caption_changed(self, text: str):
        result = self.caption_manager.push(text)
        if result:
            self.label.setText(result)
