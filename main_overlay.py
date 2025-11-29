# main_overlay.py

import sys
import subprocess
import threading

from PyQt6 import QtWidgets

from ui.overlay import CaptionOverlay


def start_worker(mode: str):
    """ stt_worker.py 를 subprocess로 실행 (mode: 'dialog' or 'bgm') """
    python_exe = sys.executable  # 현재 venv python
    proc = subprocess.Popen(
        [python_exe, "-u", "stt_worker.py", "--mode", mode],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    return proc


def main():
    app = QtWidgets.QApplication(sys.argv)
    overlay = CaptionOverlay()
    overlay.show()

    # ===== 모드 선택 =====
    print("자막 모드를 선택하세요:")
    print("  1) 디스코드 대화용 (VAD, 문장단위)")
    print("  2) 브금/영상 모드 (7초 고정 청크)")
    sel = input("번호 입력 (1/2, 기본 1): ").strip()

    if sel == "2":
        mode = "bgm"
    else:
        mode = "dialog"

    print(f"[*] 선택된 모드: {mode}")

    def reader():
        """ 워커 stdout 읽어서 자막 업데이트 """
        while True:
            proc = start_worker(mode)
            print("[UI] STT Worker Started")
            assert proc.stdout is not None

            for line in proc.stdout:
                line = line.rstrip("\n")
                print("[WORKER]", line)  # 디버깅용: 워커 로그 그대로 보여주기

                if line.startswith(">>> CAPTION:"):
                    caption = line.replace(">>> CAPTION:", "", 1).strip()
                    overlay.caption_changed.emit(caption)

            print("[UI] Worker exited. Restarting...")

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
