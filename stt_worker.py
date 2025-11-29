# stt_worker.py

import sys
from core.config import load_default_config
from core.streaming import run_stream_pipeline


def caption_printer(live_text: str, done_text: str | None):
    """ STT에서 넘어온 자막을 표준 출력(stdout)으로 보냄 """
    if done_text:
        print(f">>> CAPTION: {done_text}", flush=True)
    if live_text:
        print(f">>> CAPTION: {live_text}", flush=True)


def main():
    print("=== discord_capcap :: STT WORKER (faster-whisper) ===", flush=True)

    cfg = load_default_config()

    # 언어는 기본 'ko'
    cfg.stt.language = "ko"

    # STT 워커는 바로 시작
    run_stream_pipeline(cfg, caption_callback=caption_printer)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[WORKER ERROR] {e}", file=sys.stderr, flush=True)
        raise
