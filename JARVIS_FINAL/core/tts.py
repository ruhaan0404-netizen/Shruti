import os
import subprocess
import ollama

# File paths
piper_path = r"C:\Users\Rishav\FINAL_JAR\venv\Scripts\piper.exe"
model_path = r"C:\Users\Rishav\FINAL_JAR\JARVIS_FINAL\en_US-lessac-medium.onnx"
input_file = r"C:\piper\input.txt"
output_file = r"C:\piper\output.wav"

def speak(text, play_audio=True):
    # Ensure directory structures exist
    os.makedirs(os.path.dirname(input_file), exist_ok=True)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 1. Write the input text file
    with open(input_file, "w", encoding="utf-8") as file:
        file.write(text)

    # 2. Build the command string
    command = (
        f'type "{input_file}" | '
        f'"{piper_path}" '
        f'--model "{model_path}" '
        f'--output_file "{output_file}"'
    )
    
    # 3. ALWAYS run the command so the WAV file is created for Streamlit/Local play
    subprocess.run(command, shell=True)

    # 4. If called in local console mode, open it natively
    if play_audio and os.path.exists(output_file):
        os.startfile(output_file)

    # 5. CRITICAL: Return the file path so app.py can capture and read it!
    return output_file

def get_reply(question):
    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {
                    "role": "system",
                    "content": "You are Jarvis, a helpful and sophisticated AI assistant."
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "I am sorry, sir. I am having trouble processing that request at the moment."

def jarvis():
    # Initial greeting
    initial_greeting = "Hello, I am Jarvis. System is fully operational. How can I assist you, sir?"
    print(f"Jarvis: {initial_greeting}")
    speak(initial_greeting)
    
    # Continuous conversational loop
    while True:
        print("\n" + "="*30)
        # Capture input from the console terminal
        question = input("You: ").strip()
        
        # Exit conditions
        if not question:
            continue
        if question.lower() in ["exit", "quit", "goodbye", "bye"]:
            farewell = "Goodbye, sir. Shutting down systems."
            print(f"Jarvis: {farewell}")
            speak(farewell)
            break
            
        print("Jarvis is thinking...")
        
        # 1. Fetch response from Ollama
        reply = get_reply(question)
        
        # 2. Print response to console
        print(f"\nJarvis: {reply}")
        
        # 3. Speak response using Piper
        speak(reply)

if __name__ == "__main__":
    jarvis()