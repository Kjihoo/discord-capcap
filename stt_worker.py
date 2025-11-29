# stt_worker.py

import sys
import argparse

from core.config import load_default_config
from core.streaming import (
    run_stream_pipeline_vad,
    run_stream_pipeline_fixed,
)


def caption_printer(live_text: str, done_text: str | None):
    """ STT에서 넘어온 자막을 표준 출력(stdout)으로 보냄 """
    # overlay 쪽에서 >>> CAPTION: 으로 파싱하고 있으니까 포맷 유지
    if done_text:
        print(f">>> CAPTION: {done_text}", flush=True)
    if live_text and live_text != done_text:
        print(f">>> CAPTION: {live_text}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["dialog", "bgm"],
        default="dialog",
        help="STT 모드 선택: dialog(디코 대화용), bgm(브금/영상용)",
    )
    args = parser.parse_args()

    print("=== discord_capcap :: STT WORKER (faster-whisper) ===", flush=True)

    cfg = load_default_config()
    cfg.stt.language = "ko"  # 일단 ko 고정 (나중에 옵션으로 뺄 수 있음)

    if args.mode == "dialog":
        # 디코 대화용: 0.5초 프레임 + VAD
        cfg.audio.chunk_duration_sec = 0.5
        print("[WORKER] 모드: 디코 대화용 (VAD + 문장 단위)", flush=True)
        run_stream_pipeline_vad(cfg, caption_printer)

    else:
        # 브금/영상용: 5초 고정 청크
        cfg.audio.chunk_duration_sec = 5.0  # 🔥 7.0 → 5.0
        print("[WORKER] 모드: 브금/영상용 (5초 고정 청크)", flush=True)
        run_stream_pipeline_fixed(cfg, caption_printer)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[WORKER ERROR] {e}", file=sys.stderr, flush=True)
        raise
