import os
import io
import sys
import httpx
sys.modules['interact'] = sys.modules[__name__]
import threading
import keyboard
import torch
import numpy as np
import asyncio
import websockets
import json
import edge_tts
import pygame
from pathlib import Path
from dotenv import load_dotenv
from scipy.io import wavfile
from groq import Groq
import sounddevice as sd
from silero_vad import load_silero_vad
from lib.shruti_backend.agent_core import agent_exe_graph
from langchain.messages import HumanMessage
from tools.codeforces_tool import qdrant_client
from qdrant_client.models import Distance, VectorParams

load_dotenv()

MAIN_LOOP = None

# --- 1. INITIALIZATION ---
raw_key = os.getenv("GROQ_API_KEY")
if not raw_key:
    raise ValueError("❌ GQ_API_KEY is missing from .env!")

clean_key = raw_key.strip().replace('"', '').replace("'", "")
client = Groq(api_key=clean_key)

print("🟢 Loading Silero VAD...")
SAMPLE_RATE = 16000 
CHUNK_SIZE = 512  
SILENCE_THRESHOLD = 0.5 
MAX_SILENCE_CHUNKS = int(1.5 * (SAMPLE_RATE / CHUNK_SIZE))

vad_model = load_silero_vad()
recording_finished = threading.Event()

silence_counter = 0
is_recording = False
audio_buffer = []

# Global set to hold our connected Flutter clients
connected_clients = set()

# --- 2. WEBSOCKET BROADCASTER ---
async def broadcast_state(status, message="", draft_text=""):
    """Shoots a JSON message to Flutter instantly"""
    if not connected_clients:
        return
        
    payload = json.dumps({
        "status": status, 
        "message": message,
        "draft_text": draft_text
    })
    
    tasks = [asyncio.create_task(client_ws.send(payload)) for client_ws in connected_clients]
    if tasks:
        await asyncio.gather(*tasks)
        print(f"📡 Sent to Flutter -> Status: {status}")


# --- 3. AUDIO PIPELINE ---
def audio_callback(indata, frames, time, status):
    global silence_counter, is_recording, audio_buffer
    audio_chunk = indata.copy().flatten().astype(np.float32) / 32768.0
    tensor_chunk = torch.from_numpy(audio_chunk)
    
    with torch.no_grad():
        score = vad_model(tensor_chunk, SAMPLE_RATE).item()
        
    if score >= SILENCE_THRESHOLD:
        if not is_recording:
            print("🗣️ Speech detected! Recording started...")
            is_recording = True
        silence_counter = 0
        audio_buffer.append(indata.copy())
    else:
        if is_recording:
            audio_buffer.append(indata.copy())
            silence_counter += 1
            if silence_counter >= MAX_SILENCE_CHUNKS:
                recording_finished.set()
                raise sd.CallbackStop()

def listen():
    """This runs the physical microphone recording"""
    global silence_counter, is_recording, audio_buffer
    silence_counter = 0
    is_recording = False
    audio_buffer.clear()
    recording_finished.clear()
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', 
                        blocksize=CHUNK_SIZE, callback=audio_callback):
        recording_finished.wait()

async def speak_response(text: str):
    """
    Generates audio using Ava's voice entirely in RAM 
    and plays it immediately without writing to disk.
    """
    voice = "en-US-AvaNeural"
    communicate = edge_tts.Communicate(text, voice)
    audio_buffer = io.BytesIO()
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
    except Exception as e:
        print(f"❌ Error streaming TTS: {e}")
        return
    audio_buffer.seek(0)
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        
    try:
        pygame.mixer.music.load(audio_buffer)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"❌ Playback error: {e}")
    finally:
        pygame.mixer.music.unload()
        audio_buffer.close()
        print("✅ Finished speaking!")

# --- 4. THE ASYNC AGENT LOGIC ---
async def process_voice_command():
    """Handles the UI updates, transcription, and Groq API calls"""
    await broadcast_state("listening", "Listening...")
    await asyncio.to_thread(listen)
    if audio_buffer:
        await broadcast_state("transcribing", "Thinking...")
        final_audio = np.concatenate(audio_buffer, axis=0).flatten()
        virtual_file = io.BytesIO()
        wavfile.write(virtual_file, SAMPLE_RATE, final_audio)
        virtual_file.seek(0)
        try:
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", virtual_file.read()), 
                model="whisper-large-v3",
                response_format="text",
                temperature=0.0
            )
            result_text = transcription.strip()
            graph_inputs = {"messages": [HumanMessage(content=result_text)],"current_batch_index":0}
            graph_config = {"configurable": {"thread_id": "voice_session_001"}}
            final_state = await agent_exe_graph.ainvoke(graph_inputs, config=graph_config)
            agent_response = final_state["messages"][-1].content
            await speak_response(agent_response)
            await broadcast_state("success", agent_response)
        except Exception as e:
            print(f"❌ Cloud transcription failed: {e}")
            await broadcast_state("error", "Failed to connect to cloud.")
    else:
        await broadcast_state("idle", "No speech detected.")

# --- 5. SERVER & EVENT LOOP ---
async def websocket_handler(websocket):
    """Manages incoming connections from Flutter"""
    print("📱 Flutter UI Connected!")
    connected_clients.add(websocket)   
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get("command") == "start_mic":
                print("🎤 Mic triggered from Flutter UI!")
                asyncio.create_task(process_voice_command())              
    except websockets.exceptions.ConnectionClosed:
        print("📱 Flutter UI Disconnected.")
    finally:
        connected_clients.remove(websocket)

async def fetch_codeforces_history_loop():
    """Runs in the background, fetching Codeforces history every 30 mins."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get("https://codeforces.com/api/user.status?handle=Itu_Talishman&from=1&count=30")
                data = response.json()
                if data.get("status") == "OK":
                    all = data['result']
                    relevant = [item for item in all if item["verdict"]=="OK"]
                    folder = Path("C:\\Users\\Rishav\\Jarvis\\lib\\memory")
                    folder.mkdir(parents=True, exist_ok=True)
                    file = folder/"recent_submission.json"
                    with open(file, "w") as f:
                        json.dump(relevant, f, indent=1)
                    print("✅ Codeforces submission history updated.")
                else:
                    print(f"⚠️ API returned non-OK status: {data.get('comment')}") 
            except Exception as e:
                print(f"❌ Failed to fetch Codeforces history: {e}")
            await asyncio.sleep(180)

def create_collection(collection_name="coding_questions"):
    if qdrant_client.collection_exists(collection_name):
            print(f"Collection '{collection_name}' already exists. Skipping creation.")
    else:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
        print(f"Collection '{collection_name}' created successfully for the first time!")


async def main():
    loop = asyncio.get_running_loop()
    global MAIN_LOOP
    MAIN_LOOP = loop
    def hotkey_pressed():
        print("⌨️ Mic triggered from Keyboard Hotkey!")
        asyncio.run_coroutine_threadsafe(process_voice_command(), loop)
    keyboard.add_hotkey('ctrl+shift+space', hotkey_pressed)
    create_collection()
    background_task = asyncio.create_task(fetch_codeforces_history_loop())
    print("\n🚀 Starting WebSocket Server on ws://localhost:8765")
    print("👉 Press \"Ctrl+Shift+Space\" to speak, or connect the Flutter app.")
    async with websockets.serve(websocket_handler, "localhost", 8765):
        await asyncio.Future()


asyncio.run(main())