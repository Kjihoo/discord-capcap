# core/streaming.py

import threading
import queue
import time
from typing import Tuple, Callable, Optional

import numpy as np

from core.config import AppConfig
from audio.capture import resolve_device_index, record_once_with_index
from stt.engine import create_stt_engine
from core.debug_config import DEBUG, DEBUG_VAD, DEBUG_STT, DEBUG_CAPTURE

AudioChunk = Tuple[np.ndarray, int]
CaptionCallback = Callable[[str, Optional[str]], None]


# ------------------- 1) 디코 대화용 (VAD + endpoint) ------------------- #
def run_stream_pipeline_vad(app_cfg: AppConfig, caption_callback=None):

    from core.debug_config import DEBUG, DEBUG_VAD, DEBUG_STT, DEBUG_CAPTURE

    audio_cfg = app_cfg.audio
    stt_cfg = app_cfg.stt

    frame_sec = audio_cfg.chunk_duration_sec  # 0.5초

    # VAD 파라미터
    VOICE_ENERGY_TH   = 0.005
    SILENCE_ENERGY_TH = 0.004
    MIN_UTTER_SEC     = 0.8
    MAX_UTTER_SEC     = 15.0
    END_SILENCE_SEC   = 0.40

    print("=== STREAM (VAD + endpoint, 디코 대화용) ===")

    device_index = resolve_device_index(audio_cfg)
    stt_engine = create_stt_engine(stt_cfg)

    audio_queue: "queue.Queue[AudioChunk]" = queue.Queue(maxsize=20)
    stop_flag = threading.Event()

    current_frames = []
    current_dur = 0.0
    silence_dur = 0.0
    in_speech = False

    # ---------------- capture thread ---------------- #
    def capture_worker():
        while not stop_flag.is_set():
            audio_data, sr = record_once_with_index(audio_cfg, device_index)

            if DEBUG_CAPTURE:
                print(f"[CAP] frame captured ({frame_sec}s), samples={len(audio_data)}")

            try:
                audio_queue.put((audio_data, sr), timeout=1.0)
            except queue.Full:
                print("[WARN] audio queue full, dropping frame")

    # ---------------- finalize utterance ---------------- #
    def finalize_utterance():
        nonlocal current_frames, current_dur

        if not current_frames or current_dur < MIN_UTTER_SEC:
            current_frames = []
            current_dur = 0.0
            return

        audio = np.concatenate(current_frames, axis=0)
        sr = audio_cfg.sample_rate

        if DEBUG_STT:
            print(f"[STT] START: duration={current_dur:.2f}s")

        text = stt_engine.transcribe(audio, sr).strip()

        if DEBUG_STT:
            print(f"[STT] END: '{text}'")

        if not text:
            current_frames = []
            current_dur = 0.0
            return

        if caption_callback:
            caption_callback(text, text)
        else:
            print(">>>", text)

        current_frames = []
        current_dur = 0.0

    # ---------------- stt worker ---------------- #
    def stt_worker():
        nonlocal current_frames, current_dur, silence_dur, in_speech

        while not stop_flag.is_set():
            try:
                frame, sr = audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            energy = float(np.mean(np.abs(frame)))

            if DEBUG_VAD:
                print(f"[VAD] energy={energy:.5f}")

            if energy > VOICE_ENERGY_TH:
                current_frames.append(frame)
                current_dur += frame_sec
                silence_dur = 0.0
                in_speech = True

                if current_dur >= MAX_UTTER_SEC:
                    finalize_utterance()
                    in_speech = False
                    silence_dur = 0.0

            else:
                if in_speech:
                    silence_dur += frame_sec
                    if silence_dur >= END_SILENCE_SEC:
                        finalize_utterance()
                        in_speech = False
                        silence_dur = 0.0

    t1 = threading.Thread(target=capture_worker, daemon=True)
    t2 = threading.Thread(target=stt_worker, daemon=True)
    t1.start()
    t2.start()

    try:
        while True:
            time.sleep(0.05)   # 🌟 렉 방지
    except KeyboardInterrupt:
        stop_flag.set()
        t1.join(timeout=2.0)
        t2.join(timeout=2.0)


# ------------------- 2) 브금/영상용 (고정 길이 청크) ------------------- #
def run_stream_pipeline_fixed(
    app_cfg: AppConfig,
    caption_callback: Optional[CaptionCallback] = None,
) -> None:
    """
    브금/영상 모드 (고정 청크 + 파이프라인):

    - audio_cfg.chunk_duration_sec (예: 7초) 길이로 고정 녹음
    - 캡처 스레드: 7초씩 계속 녹음해서 큐에 넣기
    - STT 스레드: 큐에서 꺼내서 STT → 자막 출력
    - 녹음과 STT를 겹쳐서 돌려, 체감 딜레이를 줄인다.
    """
    audio_cfg = app_cfg.audio
    stt_cfg = app_cfg.stt

    chunk_sec = audio_cfg.chunk_duration_sec

    print("=== discord_capcap :: STREAM (고정 청크, 브금/영상용 파이프라인) ===")
    print(f"- device: {audio_cfg.device_name}")
    print(f"- chunk: {chunk_sec} sec")
    print(f"- model: {stt_cfg.model_name}, device={stt_cfg.device}, lang={stt_cfg.language}")
    print()

    device_index = resolve_device_index(audio_cfg)
    stt_engine = create_stt_engine(stt_cfg)

    audio_queue: "queue.Queue[AudioChunk]" = queue.Queue(maxsize=3)
    stop_flag = threading.Event()

    # ---------------- 캡처 스레드 ---------------- #
    def capture_worker():
        while not stop_flag.is_set():
            start_t = time.time()
            audio_data, sr = record_once_with_index(audio_cfg, device_index)
            rec_dur = time.time() - start_t
            print(f"[*] 캡처 완료: {rec_dur:.2f}s, samples={len(audio_data)}")

            try:
                audio_queue.put((audio_data, sr), timeout=1.0)
            except queue.Full:
                print("[WARN] fixed-mode audio_queue full, dropping chunk")

    # ---------------- STT 스레드 ---------------- #
    def stt_worker():
        while not stop_flag.is_set():
            try:
                audio_data, sr = audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            stt_start = time.time()
            if DEBUG_STT:
                print(f"[*] STT 호출(FIXED): duration≈{chunk_sec:.2f}s, samples={len(audio_data)}")

            text = stt_engine.transcribe(audio_data, sr).strip()
            stt_dur = time.time() - stt_start
            if DEBUG_STT:
                print(f"[*] STT 변환 완료(FIXED): {stt_dur:.2f}s")

            if not text:
                caption_callback("...", None)
                continue

            print(f"[STT] '{text}'")

            if caption_callback:
                caption_callback(text, text)
            else:
                print(f">>> [CAPTION] {text}")

    t_cap = threading.Thread(target=capture_worker, daemon=True)
    t_stt = threading.Thread(target=stt_worker, daemon=True)
    t_cap.start()
    t_stt.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_flag.set()
        t_cap.join(timeout=2.0)
        t_stt.join(timeout=2.0)
        print("[*] 브금/영상 모드 종료")

# 기존 코드와의 호환을 위해 기본 run_stream_pipeline은 VAD 버전으로 매핑
def run_stream_pipeline(
    app_cfg: AppConfig,
    caption_callback: Optional[CaptionCallback] = None,
) -> None:
    return run_stream_pipeline_vad(app_cfg, caption_callback)
