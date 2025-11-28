# core/streaming.py

import threading
import queue
from typing import Tuple

import numpy as np

from core.config import AppConfig
from audio.capture import resolve_device_index, record_once_with_index
from stt.engine import create_stt_engine

# 한 줄 자막 최대 길이 (대략 15글자 전후, 필요하면 조정)
MAX_CAPTION_LEN = 15

AudioChunk = Tuple[np.ndarray, int]  # (audio, sample_rate)


def run_stream_pipeline(app_cfg: AppConfig) -> None:
    """
    5초 단위로 계속 녹음하고,
    별도 STT 쓰레드에서 변환 → 자막 버퍼를 업데이트하는 스트리밍 파이프라인.

    지금은 오버레이 대신 콘솔에만:
    - [CAPTION LIVE]: 현재 화면에 떠 있을 자막 한 줄
    - [CAPTION DONE]: 하나의 자막 블록이 끝났을 때 출력
    """
    audio_cfg = app_cfg.audio
    stt_cfg = app_cfg.stt

    print("=== discord_capcap :: v2 스트리밍 STT (5초 + GPU + 언어고정) ===")
    print(f"- 오디오 장치 부분 이름: {audio_cfg.device_name}")
    print(f"- 청크 길이: {audio_cfg.chunk_duration_sec} 초")
    print(f"- 자막 한 줄 최대 길이: {MAX_CAPTION_LEN} 글자")
    print(f"- STT 모델: {stt_cfg.model_name}, device={stt_cfg.device}, lang={stt_cfg.language}")
    print("Ctrl + C 를 누르면 종료합니다.\n")

    # 1) 장치 인덱스 한 번만 해결
    device_index = resolve_device_index(audio_cfg)

    # 2) STT 엔진 준비 (GPU 위에 올림)
    stt_engine = create_stt_engine(stt_cfg)

    # 3) 오디오 청크 전달용 큐
    audio_queue: "queue.Queue[AudioChunk]" = queue.Queue(maxsize=5)
    stop_flag = threading.Event()

    caption_buffer = ""  # 현재 화면에 보여줄 자막 한 줄

    # ─────────────────────────────
    # Producer: 캡처 스레드 (5초씩 계속 녹음)
    # ─────────────────────────────
    def capture_worker():
        while not stop_flag.is_set():
            audio_data, sr = record_once_with_index(audio_cfg, device_index)
            try:
                audio_queue.put((audio_data, sr), timeout=1.0)
            except queue.Full:
                print("[WARN] 오디오 큐가 가득 찼습니다. 청크를 버립니다.")

    # ─────────────────────────────
    # Consumer: STT + 자막 스레드
    # ─────────────────────────────
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

            # 기존 자막에 자연스럽게 이어붙이기
            if caption_buffer and not caption_buffer.endswith(" "):
                caption_buffer += " "
            caption_buffer += text_chunk

            # 자막이 너무 길어지면 한 줄을 완료로 간주하고 초기화
            if len(caption_buffer) >= MAX_CAPTION_LEN:
                print(f"\n>>> [CAPTION DONE] {caption_buffer}\n")
                caption_buffer = ""

            # 현재 자막 상태를 출력 (나중에 오버레이 쪽에 이 텍스트를 넘기면 됨)
            print(f">>> [CAPTION LIVE] {caption_buffer}")

    t_capture = threading.Thread(target=capture_worker, daemon=True)
    t_stt = threading.Thread(target=stt_worker, daemon=True)

    t_capture.start()
    t_stt.start()

    try:
        while True:
            # 메인 스레드는 그냥 살아있기만 하면 됨.
            # 나중에 여기에서 GUI 이벤트 루프(PyQt 등)를 돌릴 예정.
            pass
    except KeyboardInterrupt:
        print("\n[*] 종료 플래그 설정, 쓰레드 종료 중...")
        stop_flag.set()
        t_capture.join(timeout=2.0)
        t_stt.join(timeout=2.0)
        print("[*] 스트리밍 파이프라인 종료")
