# main_overlay.py

import sys
import subprocess
import threading

from PyQt6 import QtWidgets

from ui.overlay import CaptionOverlay


def start_worker():
    """ stt_worker.py 를 subprocess로 실행 """
    python_exe = sys.executable  # 현재 venv python
    proc = subprocess.Popen(
        [python_exe, "-u", "stt_worker.py"],  # -u: stdout 버퍼링 제거
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1
    )
    return proc


def main():
    app = QtWidgets.QApplication(sys.argv)
    overlay = CaptionOverlay()
    overlay.show()

    def reader():
        """ 워커 stdout 읽어서 자막 업데이트 """
        while True:
            proc = start_worker()
            print("[UI] STT Worker Started")

            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip("\n")
                if line.startswith(">>> CAPTION:"):
                    caption = line.replace(">>> CAPTION:", "", 1).strip()
                    overlay.caption_changed.emit(caption)

            print("[UI] Worker exited. Restarting...")

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
