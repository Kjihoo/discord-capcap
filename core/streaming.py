# core/streaming.py

import threading
import queue
from typing import Tuple, Callable, Optional

import numpy as np

from core.config import AppConfig
from audio.capture import resolve_device_index, record_once_with_index
from stt.engine import create_stt_engine

MAX_CAPTION_LEN = 15

AudioChunk = Tuple[np.ndarray, int]
CaptionCallback = Callable[[str, Optional[str]], None]


def run_stream_pipeline(
    app_cfg: AppConfig,
    caption_callback: Optional[CaptionCallback] = None,
    stt_engine=None,  # 🔥 외부에서 엔진 주입 가능하도록
) -> None:
    audio_cfg = app_cfg.audio
    stt_cfg = app_cfg.stt

    print("[STREAM] STT 스트리밍 시작")
    print(f"- device: {audio_cfg.device_name}")
    print(f"- chunk: {audio_cfg.chunk_duration_sec} sec")
    print(f"- model: {stt_cfg.model_name}, device={stt_cfg.device}, lang={stt_cfg.language}")

    device_index = resolve_device_index(audio_cfg)

    # 🔥 stt_engine이 안 들어오면 (콘솔 전용 모드 등) 기존처럼 여기서 생성
    if stt_engine is None:
        stt_engine = create_stt_engine(stt_cfg)

    audio_queue: "queue.Queue[AudioChunk]" = queue.Queue(maxsize=5)
    stop_flag = threading.Event()

    caption_buffer = ""

    def capture_worker():
        while not stop_flag.is_set():
            audio_data, sr = record_once_with_index(audio_cfg, device_index)
            try:
                audio_queue.put((audio_data, sr), timeout=1.0)
            except queue.Full:
                print("[WARN] audio queue full, dropping chunk")

    def stt_worker():
        nonlocal caption_buffer
        while not stop_flag.is_set():
            try:
                audio_data, sr = audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            text_chunk = stt_engine.transcribe(audio_data, sr).strip()
            if not text_chunk:
                if caption_callback:
                    caption_callback(caption_buffer, None)
                else:
                    print(f">>> [CAPTION LIVE] {caption_buffer}")
                continue

            print(f"[DEBUG] STT CHUNK: '{text_chunk}'")

            if caption_buffer and not caption_buffer.endswith(" "):
                caption_buffer += " "
            caption_buffer += text_chunk

            done_text: Optional[str] = None
            if len(caption_buffer) >= MAX_CAPTION_LEN:
                done_text = caption_buffer
                caption_buffer = ""

            if caption_callback:
                caption_callback(caption_buffer, done_text)
            else:
                if done_text:
                    print(f">>> [CAPTION DONE] {done_text}")
                print(f">>> [CAPTION LIVE] {caption_buffer}")

    t_cap = threading.Thread(target=capture_worker, daemon=True)
    t_stt = threading.Thread(target=stt_worker, daemon=True)
    t_cap.start()
    t_stt.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        stop_flag.set()
        t_cap.join(timeout=2.0)
        t_stt.join(timeout=2.0)
