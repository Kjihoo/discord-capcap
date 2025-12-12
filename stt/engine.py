# stt/engine.py

import os
import sys


from typing import Protocol
import numpy as np

from core.config import STTConfig
from faster_whisper import WhisperModel


class ISTTEngine(Protocol):
    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        모노 오디오(1D float32)와 샘플레이트를 받아 텍스트를 반환.
        """
        ...


class FasterWhisperEngine:
    """
    faster-whisper 기반 STT 엔진 래퍼.
    GPU(CUDA) 사용을 기본으로 함.
    """
    def __init__(self, cfg: STTConfig):
        self.cfg = cfg
        print(
            f"[*] faster-whisper 모델 로드 중... "
            f"({cfg.model_name}, device={cfg.device}, compute_type={cfg.compute_type})"
        )
        self.model = WhisperModel(
            cfg.model_name,
            device=cfg.device,          # "cuda" or "cpu"
            compute_type=cfg.compute_type,
        )
        print("[*] STT 모델 로드 완료")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        1D numpy 배열 audio (모노, float32)를 받아서 텍스트로 변환.
        sample_rate는 16000 기준.
        """
        language = self.cfg.language  # "ko" / "en" / None
        print("[*] STT 변환 시작...")

        segments, info = self.model.transcribe(
            audio,
            language=self.language,  # "ko"로 강제
            task="transcribe",  # 번역 금지
            beam_size=5,  # 높이면 정확도 증가
            best_of=5,
            temperature=0.0,  # 추측 최소화
            compression_ratio_threshold=2.0,
            no_speech_threshold=0.1,
        )

        texts: list[str] = []
        for seg in segments:
            texts.append(seg.text.strip())

        full_text = " ".join(texts)
        print(
            f"[*] STT 변환 완료. "
            f"detected_language={info.language}, duration={info.duration:.2f}s"
        )
        return full_text


def create_stt_engine(cfg: STTConfig) -> ISTTEngine:
    # 🔥 CUDA 쓸 때만 DLL 경로 추가
    if sys.platform == "win32" and cfg.device == "cuda":
        cuda_paths = [
            r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin",
            r"C:\Program Files\NVIDIA\CUDNN\v9.16\bin\12.9",
        ]
        for p in cuda_paths:
            if os.path.isdir(p):
                try:
                    os.add_dll_directory(p)
                    print(f"[*] DLL 경로 추가: {p}")
                except Exception as e:
                    print(f"[WARN] DLL 경로 추가 실패 ({p}): {e}")

    if cfg.engine_type == "faster_whisper":
        return FasterWhisperEngine(cfg)
    else:
        raise ValueError(f"지원하지 않는 STT 엔진: {cfg.engine_type}")
