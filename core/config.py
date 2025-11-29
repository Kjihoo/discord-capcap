# core/config.py

from dataclasses import dataclass


from dataclasses import dataclass

@dataclass
class AudioConfig:
    device_name: str = "CABLE Output"
    sample_rate: int = 16000
    channels: int = 1              # 🔥 새로 추가 (모노)
    chunk_duration_sec: float = 0.5  # 프레임 길이(예: 0.5초)

@dataclass
class STTConfig:
    """
    STT 엔진 관련 설정.
    - model_name: faster-whisper 모델 사이즈 (tiny/base/small/medium...)
    - device: "cuda"면 GPU, "cpu"면 CPU 사용
    - compute_type: "float16"은 GPU에서 속도/정확도 균형 좋음
    - language: "ko" or "en" 으로 고정 (None이면 자동 감지)
    """
    engine_type: str = "faster_whisper"
    model_name: str = "small"          # 정확도 고려해서 small 기본
    device: str = "cuda"               # 🔥 GPU 사용
    compute_type: str = "float16"      # GPU용 추천
    language: str | None = None     # main_stream에서 ko/en으로 설정


@dataclass
class AppConfig:
    audio: AudioConfig
    stt: STTConfig


def load_default_config() -> AppConfig:
    audio_cfg = AudioConfig()
    stt_cfg = STTConfig()
    return AppConfig(audio=audio_cfg, stt=stt_cfg)
