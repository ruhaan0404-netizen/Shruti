import whisper
import os

class Model:
    def __init__(self, model_name="turbo", device="cpu"):
        print(f"Loading Whisper model ({model_name}) on {device}...")
        self.model = whisper.load_model(model_name, device=device)
        print("Whisper model loaded.")
        
    def transcribe(self, path):
        if not os.path.exists(path):
            return ""
        result = self.model.transcribe(path, fp16=False)
        return result["text"]

# Singleton pattern so we only load it once
_stt_model = None

def get_stt_model():
    global _stt_model
    if _stt_model is None:
        _stt_model = Model()
    return _stt_model

def transcribe_audio(path):
    model = get_stt_model()
    return model.transcribe(path)
