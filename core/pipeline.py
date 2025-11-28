# core/pipeline.py

import threading
import queue
from typing import Tuple

import numpy as np

from core.config import AppConfig
from audio.capture import resolve_device_index, record_once_with_index
from stt.engine import create_stt_engine

MAX_CAPTION_LEN = 15

AudioChunk = Tuple[np.ndarray, int]  # (audio, sample_rate)


def run_stream_pipeline_threaded(app_cfg: AppConfig) -> None:
    audio_cfg = app_cfg.audio
    stt_cfg = app_cfg.stt

    print("=== discord_capcap :: 쓰레드 기반 스트리밍 STT 테스트 ===")
    print(f"- 오디오 장치: {audio_cfg.device_name}")
    print(f"- 청크 길이: {audio_cfg.chunk_duration_sec} 초")
    print(f"- 자막 한 줄 최대 길이: {MAX_CAPTION_LEN} 글자")
    print("Ctrl + C 를 누르면 종료합니다.\n")

    device_index = resolve_device_index(audio_cfg)
    stt_engine = create_stt_engine(stt_cfg)

    audio_queue: "queue.Queue[AudioChunk]" = queue.Queue(maxsize=5)
    stop_flag = threading.Event()

    caption_buffer = ""

    # 1) 녹음 스레드
    def capture_worker():
        while not stop_flag.is_set():
            audio_data, sr = record_once_with_index(audio_cfg, device_index)
            try:
                audio_queue.put((audio_data, sr), timeout=1.0)
            except queue.Full:
                print("[WARN] 오디오 큐가 가득 찼습니다. 청크를 버립니다.")

    # 2) STT + 자막 스레드
    def stt_worker():
        nonlocal caption_buffer
        while not stop_flag.is_set():
            try:
                audio_data, sr = audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            text_chunk = stt_engine.transcribe(audio_data, sr).strip()
            if not text_chunk:
                print("[*] STT 결과 없음 (무음일 수 있음)")
                continue

            print(f"    [DEBUG] STT 청크: '{text_chunk}'")

            if caption_buffer and not caption_buffer.endswith(" "):
                caption_buffer += " "
            caption_buffer += text_chunk

            if len(caption_buffer) > MAX_CAPTION_LEN:
                print(f"\n>>> [CAPTION DONE] {caption_buffer}\n")
                caption_buffer = ""

            print(f">>> [CAPTION LIVE] {caption_buffer}")

    t_capture = threading.Thread(target=capture_worker, daemon=True)
    t_stt = threading.Thread(target=stt_worker, daemon=True)

    t_capture.start()
    t_stt.start()

    try:
        while True:
            # 메인 스레드는 그냥 살아있기만 하면 됨.
            # 나중에 여기서 UI 이벤트 루프를 돌릴 수 있음.
            pass
    except KeyboardInterrupt:
        print("\n[*] 종료 플래그 설정, 쓰레드 종료 중...")
        stop_flag.set()
        t_capture.join(timeout=2.0)
        t_stt.join(timeout=2.0)
        print("[*] 스트리밍 파이프라인 종료")
