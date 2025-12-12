# core/config.py

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
    STT 엔진 관련 설정
    """

    engine_type: str = "faster-whisper"
    model_name: str = "small"
    device: str = "cuda"
    compute_type: str = "float16"

    # 🔽 반드시 기본값 필요
    speech_language: str = "auto"     # 입력 음성 언어 ("auto", "ko", "en")
    caption_language: str = "same"    # 출력 자막 언어 ("same", "ko", "en", "ja", "zh")

@dataclass
class AppConfig:
    audio: AudioConfig
    stt: STTConfig


def load_default_config() -> AppConfig:
    audio_cfg = AudioConfig()
    stt_cfg = STTConfig()
    return AppConfig(audio=audio_cfg, stt=stt_cfg)
