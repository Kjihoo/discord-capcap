from core.config import STTConfig
from stt.engine import create_stt_engine
import numpy as np

cfg = STTConfig(engine_type="faster_whisper", model_name="small",
                device="cpu", compute_type="int8", language="ko")
engine = create_stt_engine(cfg)
dummy = np.zeros(16000 * 3, dtype="float32")
print(engine.transcribe(dummy, 16000))
