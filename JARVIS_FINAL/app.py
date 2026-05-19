import streamlit as st
import time
import os

# Import core modules
from core.stt import transcribe_audio
from core.tts import speak
from memory.graph import build_graph

# ----------------------------
# 1) Page Configuration
# ----------------------------
st.set_page_config(
    page_title="JARVIS Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# 2) Session State
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "memory_state" not in st.session_state:
    st.session_state.memory_state = {
        "messages": [],
        "short_term_memory": [],
        "execution_log": [],
    }
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None
if "widget_id" not in st.session_state:
    st.session_state.widget_id = 0

@st.cache_resource
def get_jarvis_graph():
    return build_graph()

if "graph" not in st.session_state:
    st.session_state.graph = get_jarvis_graph()

# ----------------------------
# 3) JARVIS / IRON-MAN STYLE UI
# ----------------------------
st.markdown(
    """
    <style>
        .stApp {
            background: radial-gradient(circle at top, rgba(0, 224, 255, 0.12), transparent 35%),
                        radial-gradient(circle at bottom right, rgba(0, 224, 255, 0.08), transparent 30%),
                        linear-gradient(180deg, #02070d 0%, #040b14 45%, #021018 100%);
            color: #d7f9ff;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .jarvis-title {
            font-size: 3rem; font-weight: 800; letter-spacing: 0.18em; text-transform: uppercase;
            color: #9ffcff; text-shadow: 0 0 8px rgba(0, 224, 255, 0.9), 0 0 18px rgba(0, 224, 255, 0.55), 0 0 34px rgba(0, 224, 255, 0.35);
            margin-bottom: 0.2rem;
        }
        .jarvis-subtitle { color: #8fbfc9; font-size: 0.95rem; letter-spacing: 0.12em; margin-bottom: 1.5rem; }
        div[data-testid="stChatInput"] textarea {
            background: rgba(2, 12, 20, 0.95) !important; color: #e8fdff !important;
            border: 1px solid rgba(0, 224, 255, 0.35) !important; border-radius: 16px !important;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(2, 8, 15, 0.98), rgba(3, 18, 28, 0.96));
            border-right: 1px solid rgba(0, 224, 255, 0.15);
        }
        section[data-testid="stSidebar"] * { color: #d7f9ff !important; }
        .stButton > button {
            background: linear-gradient(180deg, rgba(0, 224, 255, 0.22), rgba(0, 224, 255, 0.08));
            color: #dffcff; border: 1px solid rgba(0, 224, 255, 0.35); border-radius: 14px;
        }
        .jarvis-card {
            background: rgba(4, 18, 28, 0.78); border: 1px solid rgba(0, 224, 255, 0.18);
            border-radius: 18px; padding: 0.9rem 1rem; box-shadow: 0 0 18px rgba(0, 224, 255, 0.06);
        }
        .jarvis-card h4 { margin: 0; color: #7cecff; letter-spacing: 0.1em; font-size: 0.8rem; text-transform: uppercase; }
        .jarvis-card p { margin: 0.35rem 0 0 0; color: #dffcff; font-size: 1rem; }
        .glow-line { height: 1px; background: linear-gradient(90deg, transparent, rgba(0,224,255,0.7), transparent); margin: 1rem 0 1.2rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# 4) Sidebar
# ----------------------------
with st.sidebar:
    st.markdown("### ⚙️ SYSTEM CONTROL")
    st.markdown("#### Agent Logs")
    st.markdown('<div class="glow-line"></div>', unsafe_allow_html=True)

    if st.session_state.logs:
        for log in st.session_state.logs[-10:]:
            st.caption(f"• {log}")
    else:
        st.caption("• Awaiting commands...")

    st.markdown('<div class="glow-line"></div>', unsafe_allow_html=True)
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.logs = []
        st.session_state.memory_state = {"messages": [], "short_term_memory": [], "execution_log": []}
        st.rerun()

# ----------------------------
# 5) Main Header
# ----------------------------
st.markdown('<div class="jarvis-title">JARVIS</div>', unsafe_allow_html=True)
st.markdown('<div class="jarvis-subtitle">Multimodal Assistant • Voice • Vision • Command Interface</div>', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown('<div class="jarvis-card"><h4>Status</h4><p>ONLINE</p></div>', unsafe_allow_html=True)
with col_b:
    st.markdown('<div class="jarvis-card"><h4>Mode</h4><p>ASSISTIVE / MULTIMODAL</p></div>', unsafe_allow_html=True)
with col_c:
    st.markdown('<div class="jarvis-card"><h4>Security</h4><p>LOCKED</p></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
# ----------------------------
# 6) Chat History
# ----------------------------
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            # --- TEXT REMOVED HERE ---
            if message.get("audio_path") and os.path.exists(message["audio_path"]):
                st.audio(message["audio_path"])

# ----------------------------
# 7) Multimodal Inputs
# ----------------------------
with st.expander("📸 MULTIMODAL INPUTS", expanded=False):
    # Bind the widget key to our dynamic ID counter
    audio_cmd = st.audio_input("Voice Command", key=f"voice_input_{st.session_state.widget_id}")
    
prompt = st.chat_input("Type a command for JARVIS...")

# Capture Audio Input
if audio_cmd is not None:
    st.session_state.logs.append("Voice command recorded.")
    temp_filename = "temp_audio.wav"
    with open(temp_filename, "wb") as f:
        f.write(audio_cmd.getbuffer())
    
    with st.spinner("Transcribing audio..."):
        transcribed_text = transcribe_audio(temp_filename)
        st.session_state.logs.append(f"Transcribed: {transcribed_text}")
        st.session_state.pending_input = transcribed_text
    st.session_state.widget_id += 1
    st.rerun()

# Capture Text Input
if prompt:
    st.session_state.pending_input = prompt
    
# ----------------------------
# 8) Command Execution
# ----------------------------
# Check if there is an input waiting from either voice or text
if st.session_state.pending_input:
    input_text = st.session_state.pending_input
    st.session_state.pending_input = None
    st.session_state.messages.append({"role": "user", "content": input_text})
    with st.chat_message("user"):
        st.markdown(input_text)

    with st.status("JARVIS is reasoning...", expanded=True) as status:
        st.write("Processing intent and tools...")
        current_state = st.session_state.memory_state.copy()
        current_state["user_input"] = input_text
        final_state = st.session_state.graph.invoke(current_state)
        st.session_state.memory_state = final_state  # Update memory state
        
        assistant_response = final_state.get("response", "I could not process that request.")
        
        st.session_state.logs.extend(final_state.get("execution_log", [])[-3:])
        status.update(label="Task Complete!", state="complete", expanded=False)

    # Render and Play Audio
    with st.spinner("Generating speech..."):
        audio_path = speak(assistant_response, play_audio=False)
        if audio_path and os.path.exists(audio_path):
            st.audio(audio_path, autoplay=True)

    st.session_state.messages.append({
        "role": "assistant", 
        "content": assistant_response,
        "audio_path": audio_path if audio_path else None
    })
    st.rerun()