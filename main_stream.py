# main_stream.py

from core.config import load_default_config
from core.streaming import run_stream_pipeline
from audio.capture import list_audio_devices


def main():
    print("=== discord_capcap :: v2 실시간 자막 스트리밍 실행 ===\n")

    # 오디오 장치 확인용 (처음에 한 번만 봐도 됨)
    list_audio_devices()

    cfg = load_default_config()

    # 언어 선택 (1. 한국어 / 2. 영어)
    print("\n사용할 언어를 선택하세요:")
    print("  1) 한국어 (ko)")
    print("  2) 영어 (en)")
    choice = input("번호 입력 (1/2, 기본 1): ").strip()

    if choice == "2":
        cfg.stt.language = "en"
    else:
        cfg.stt.language = "ko"

    print(f"[*] 선택된 언어: {cfg.stt.language}")

    audio_cfg = cfg.audio
    print(f"[*] 현재 오디오 장치 부분 이름: '{audio_cfg.device_name}'")
    print(f"[*] 청크 길이: {audio_cfg.chunk_duration_sec} 초 (5초 단위)")
    input("[엔터]를 누르면 스트리밍 STT를 시작합니다... (Ctrl+C로 종료)\n")

    run_stream_pipeline(cfg)


if __name__ == "__main__":
    main()
