# stt_worker.py

import argparse

from core.config import load_default_config
from core.streaming import (
    run_stream_pipeline_vad,
    run_stream_pipeline_fixed,
)

# ---------------- argparse ---------------- #
def parse_args():
    parser = argparse.ArgumentParser(description="discord-capcap STT worker")

    parser.add_argument(
        "--mode",
        choices=["dialog", "bgm"],
        default="dialog",
        help="STT mode",
    )

    parser.add_argument(
        "--speech-lang",
        default="auto",
        help="input speech language (ko / en / auto)",
    )

    parser.add_argument(
        "--caption-lang",
        default="same",
        help="caption language (same / ko / en / ja / zh)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    print("=== discord_capcap :: STT WORKER ===")
    print(f"- mode            : {args.mode}")
    print(f"- speech_language : {args.speech_lang}")
    print(f"- caption_language: {args.caption_lang}")
    print()

    cfg = load_default_config()
    cfg.stt.speech_language = args.speech_lang
    cfg.stt.caption_language = args.caption_lang

    # 🔥 핵심 추가 부분 🔥
    def on_caption(caption_text, original_text):
        # overlay가 이 줄을 읽는다
        print(f">>> CAPTION: {caption_text}", flush=True)

    # -------- 실행 -------- #
    if args.mode == "dialog":
        run_stream_pipeline_vad(cfg, caption_callback=on_caption)
    else:
        run_stream_pipeline_fixed(cfg, caption_callback=on_caption)


if __name__ == "__main__":
    main()
