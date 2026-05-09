import whisper
class Model:
    def __init__(self):
        self.model = whisper.load_model("turbo",device="cpu")
    def give_text(self,path):
        return self.model.transcribe(path,fp16=False)["text"]

def main():
    stt_model = Model()
    user_command = stt_model.give_text("audio.m4a")

if __name__ == "__main__":
    main()