# main_overlay.py
import sys
import subprocess
import threading
from datetime import datetime

from PyQt6 import QtWidgets

from ui.overlay import CaptionOverlay


def start_worker(mode: str, speech_lang: str, caption_lang: str):
    python_exe = sys.executable

    cmd = [
        python_exe,
        "-u",
        "stt_worker.py",
        "--mode", mode,
        "--speech-lang", speech_lang,
        "--caption-lang", caption_lang,
    ]

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )


def main():
    caption_log: list[str] = []

    app = QtWidgets.QApplication(sys.argv)

    overlay = CaptionOverlay()
    overlay.show()

    # ================= 모드 선택 =================
    print("\n자막 모드를 선택하세요:")
    print("  1) 디스코드 대화용")
    print("  2) 브금 / 영상 모드")
    mode_sel = input("번호 입력 (기본 1): ").strip()
    mode = "bgm" if mode_sel == "2" else "dialog"

    # ================= 음성 언어 =================
    print("\n말하는 음성 언어:")
    print("  1) 자동")
    print("  2) 한국어")
    print("  3) 영어")
    speech_sel = input("번호 입력 (기본 1): ").strip()
    speech_lang = {"2": "ko", "3": "en"}.get(speech_sel, "auto")

    # ================= 자막 언어 =================
    print("\n자막 언어:")
    print("  1) 음성과 동일")
    print("  2) 한국어")
    print("  3) 영어")
    caption_sel = input("번호 입력 (기본 1): ").strip()
    caption_lang = {"2": "ko", "3": "en"}.get(caption_sel, "same")

    # ================= 종료 시 저장 =================
    def save_caption_log():
        if not caption_log:
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captions_{ts}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            for line in caption_log:
                f.write(line + "\n")

        print(f"[UI] 자막 로그 저장 완료: {filename}")

    app.aboutToQuit.connect(save_caption_log)

    # ================= Worker stdout reader =================
    def reader():
        while True:
            proc = start_worker(mode, speech_lang, caption_lang)
            print("[UI] STT Worker Started")

            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip("\n")
                print("[WORKER]", line)

                if line.startswith(">>> CAPTION:"):
                    caption = line.replace(">>> CAPTION:", "", 1).strip()
                    overlay.caption_changed.emit(caption)
                    caption_log.append(caption)

            print("[UI] Worker exited. Restarting...")

    threading.Thread(target=reader, daemon=True).start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
