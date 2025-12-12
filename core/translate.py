# core/translate.py

from transformers import pipeline
from functools import lru_cache

# -------------------------------
# 내부 캐시: 언어쌍별 번역기
# -------------------------------

@lru_cache(maxsize=8)
def _load_translator(src: str, tgt: str):
    """
    HuggingFace 번역 파이프라인 로드 (언어쌍별 캐싱)
    """
    model_name = f"Helsinki-NLP/opus-mt-{src}-{tgt}"
    print(f"[TRANSLATE] loading model: {model_name}")

    return pipeline(
        task="translation",
        model=model_name,
    )


# -------------------------------
# 외부에서 호출되는 함수
# -------------------------------

def translate_text(text: str, src: str, tgt: str) -> str:
    """
    STT 결과를 로컬 HuggingFace 모델로 번역한다.
    - 완전 무료
    - 오프라인 가능
    """

    if not text or not text.strip():
        return ""

    # 동일 언어면 번역 안 함
    if src == tgt or tgt == "same":
        return text

    try:
        translator = _load_translator(src, tgt)
        result = translator(
            text,
            max_length=400,
            clean_up_tokenization_spaces=True,
        )
        return result[0]["translation_text"]

    except Exception as e:
        print(f"[TRANSLATE][ERROR] {e}")
        # 실패 시 원문 그대로 반환 (서비스 죽지 않게)
        return text
