# main_overlay.py
import sys
import subprocess
import threading

from PyQt6 import QtWidgets

from ui.overlay import CaptionOverlay


def start_worker(
    mode: str,
    speech_lang: str,
    caption_lang: str,
):
    """
    stt_worker.py 를 subprocess로 실행
    - mode: dialog | bgm
    - speech_lang: auto | ko | en
    - caption_lang: same | ko | en
    """
    python_exe = sys.executable  # 현재 venv python

    cmd = [
        python_exe,
        "-u",
        "stt_worker.py",
        "--mode", mode,
        "--speech-lang", speech_lang,
        "--caption-lang", caption_lang,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    return proc


def main():
    app = QtWidgets.QApplication(sys.argv)

    # ================= Overlay =================
    overlay = CaptionOverlay()
    overlay.show()

    # ================= 모드 선택 =================
    print("\n자막 모드를 선택하세요:")
    print("  1) 디스코드 대화용 (VAD, 문장 단위)")
    print("  2) 브금 / 영상 모드 (고정 청크)")
    mode_sel = input("번호 입력 (기본 1): ").strip()

    if mode_sel == "2":
        mode = "bgm"
    else:
        mode = "dialog"

    print(f"[*] 선택된 모드: {mode}")

    # ================= 음성 언어 =================
    print("\n말하는 음성 언어를 선택하세요:")
    print("  1) 자동 감지")
    print("  2) 한국어")
    print("  3) 영어")
    speech_sel = input("번호 입력 (기본 1): ").strip()

    if speech_sel == "2":
        speech_lang = "ko"
    elif speech_sel == "3":
        speech_lang = "en"
    else:
        speech_lang = "auto"

    print(f"[*] 음성 언어: {speech_lang}")

    # ================= 자막 언어 =================
    print("\n자막으로 표시할 언어를 선택하세요:")
    print("  1) 음성과 동일")
    print("  2) 한국어")
    print("  3) 영어")
    caption_sel = input("번호 입력 (기본 1): ").strip()

    if caption_sel == "2":
        caption_lang = "ko"
    elif caption_sel == "3":
        caption_lang = "en"
    else:
        caption_lang = "same"

    print(f"[*] 자막 언어: {caption_lang}")

    print("\n[UI] STT 워커를 시작합니다...\n")

    # ================= Worker stdout reader =================
    def reader():
        while True:
            proc = start_worker(
                mode=mode,
                speech_lang=speech_lang,
                caption_lang=caption_lang,
            )

            print("[UI] STT Worker Started")
            assert proc.stdout is not None

            for line in proc.stdout:
                line = line.rstrip("\n")

                # 워커 로그 그대로 출력
                print("[WORKER]", line)

                # 자막 라인만 overlay로 전달
                if line.startswith(">>> CAPTION:"):
                    caption = line.replace(">>> CAPTION:", "", 1).strip()
                    overlay.caption_changed.emit(caption)

            print("[UI] Worker exited. Restarting...")

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
