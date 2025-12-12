# stt/engine.py

import os
import numpy as np
from faster_whisper import WhisperModel


class FasterWhisperEngine:
    def __init__(self, cfg):
        self.cfg = cfg

        print(
            f"[*] faster-whisper 모델 로드 중... "
            f"({cfg.model_name}, device={cfg.device}, compute_type={cfg.compute_type})"
        )

        self.model = WhisperModel(
            cfg.model_name,
            device=cfg.device,
            compute_type=cfg.compute_type,
        )

        print("[*] STT 모델 로드 완료")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        segments, info = self.model.transcribe(
            audio,
            language=None if self.cfg.speech_language == "auto" else self.cfg.speech_language,
            task="transcribe",      # ⚠ 번역 아님
            beam_size=5,
            best_of=5,
            temperature=0.0,
            no_speech_threshold=0.1,
        )

        text = "".join(seg.text for seg in segments).strip()
        return text


# ---------------- factory ---------------- #

def create_stt_engine(cfg):
    if cfg.engine_type == "faster-whisper":
        return FasterWhisperEngine(cfg)

    raise ValueError(f"지원하지 않는 STT 엔진: {cfg.engine_type}")
