from PyQt6 import QtWidgets, QtCore, QtGui


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

        # 배경 + 텍스트
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
        self.label.setStyleSheet(
            "color: white;"
            "font-size: 22px;"
            "font-weight: 600;"
        )

        layout.addWidget(self.label)

        self.caption_changed.connect(self._on_caption_changed)

    def _on_caption_changed(self, text: str):
        self.label.setText(text)
