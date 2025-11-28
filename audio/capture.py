# audio/capture.py

from typing import Tuple

import numpy as np
import sounddevice as sd

from core.config import AudioConfig


def list_audio_devices() -> None:
    """
    사용 가능한 입력 오디오 장치 목록을 콘솔에 출력.
    VB-Cable Output 장치 이름/인덱스를 확인할 때 사용.
    """
    devices = sd.query_devices()
    print("=== 입력 가능한 오디오 장치 목록 ===")
    for idx, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            print(f"[{idx}] {dev['name']} (max_input_channels={dev['max_input_channels']})")
    print("====================================")


def _find_device_index(name_part: str) -> int:
    """
    장치 이름에 name_part 문자열이 포함된 입력 장치의 인덱스를 반환.
    - 여러 개가 매칭되면 첫 번째 것을 사용.
    - 못 찾으면 ValueError 발생.
    """
    devices = sd.query_devices()
    matches = []
    for idx, dev in enumerate(devices):
        if dev["max_input_channels"] > 0 and name_part.lower() in dev["name"].lower():
            matches.append((idx, dev["name"]))

    if not matches:
        raise ValueError(f"입력 장치 중에 '{name_part}' 가 포함된 이름을 찾을 수 없습니다.")

    idx, name = matches[0]
    print(f"[*] '{name_part}' 와 매칭된 장치: [{idx}] {name}")
    return idx


def resolve_device_index(config: AudioConfig) -> int:
    """
    AudioConfig 기준으로 한 번만 장치 인덱스를 찾아서 반환.
    스트리밍 도중에는 이 인덱스를 계속 재사용.
    """
    return _find_device_index(config.device_name)


def record_once_with_index(config: AudioConfig, device_index: int) -> Tuple[np.ndarray, int]:
    """
    이미 결정된 device_index를 사용하여
    config.chunk_duration_sec 동안 녹음.
    모노 오디오 데이터와 샘플레이트를 반환.
    """
    sample_rate = config.sample_rate
    channels = config.channels
    duration = config.chunk_duration_sec

    num_frames = int(sample_rate * duration)

    print(f"[*] 장치 [{device_index}] 에서 {duration:.1f}초 동안 녹음 시작...")
    print(f"    - sample_rate={sample_rate}, channels={channels}, frames={num_frames}")

    recording = sd.rec(
        frames=num_frames,
        samplerate=sample_rate,
        channels=channels,
        dtype="float32",
        device=device_index,
    )
    sd.wait()

    if channels == 1:
        audio_mono = recording[:, 0]
    else:
        audio_mono = recording.mean(axis=1)

    print(f"[*] 녹음 완료. raw_shape={recording.shape}, mono_shape={audio_mono.shape}")
    return audio_mono, sample_rate
