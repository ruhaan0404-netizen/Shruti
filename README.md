<!-- HEADER SECTION -->
<div align="center">
  <img src="docs/assets/logo.png" alt="Agent Logo" width="150"/>

  # Meet Shruti 
  
  **A friendly, intuitive AI desktop agent ready to help you get things done.**

  <!-- BADGES -->
  [![Flutter](https://img.shields.io/badge/Flutter-%2302569B.svg?style=flat&logo=Flutter&logoColor=white)](#)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#)
  [![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](#)
</div>

---

## 📖 Overview
A multimodal, agentic AI system equipped with comprehensive calendar orchestration, end-to-end email processing, natural language conversation handling, and a dedicated module for archiving and tracking Codeforces problem solutions. Acting as an orchestrator, the main agent parses intricate user assignments into manageable sub-tasks, delegating them to worker subagents for seamless, sequential execution. Equipped with end-to-end voice processing capabilities, the agent accepts audio inputs and generates calming, natural-sounding vocal responses.

<!-- VISUAL DEMO -->
## 🚀 See it in Action
> 
<div align="center">
  <video src="docs/demo/demo.gif" alt="Demo Animation" width="100"/>
</div>

---

## ✨ Key Features
* **Feature 1:** Acting as the central orchestrator, Shruti intelligently decomposes user instructions into distinct subtasks. It dynamically maps execution pathways optimizing for both sequential and parallel processing and delegates workloads across four domain-specific subagents: Calendar, Email, Codeforces, and General.
* **Feature 2:** Implemented a stateful memory architecture using LangGraph, tracking active thread nodes in-memory for seamless task resumption and strict context preservation. Developed a dynamic conversation summarization module to bypass LLM context window constraints during extended sessions.
* **Feature 3:** Shruti’s voice ingestion pipeline is engineered for ultra-low latency and dynamic responsiveness. By integrating Silero VAD, the system intelligently detects natural speech pauses to automatically truncate recordings. The strictly in-memory audio buffer (io.BytesIO) is then instantly routed to the Groq API, leveraging the whisper-large-v3 model for high-fidelity, millisecond-level transcription.
* **Feature 4:** Shruti’s vocal engine is designed for absolute minimal latency. Utilizing the asynchronous streaming capabilities of Edge-TTS, the system synthesizes audio chunk-by-chunk. By routing these streams directly into an in-memory buffer (io.BytesIO) and bypassing disk I/O entirely, Shruti achieves near-instantaneous, non-blocking playback via pygame.
* **Feature 5:** The Codeforces RAG Vault is an autonomous, semantic knowledge base that meticulously tracks your competitive programming journey. By utilizing targeted web scraping to extract raw problem statements and Gemini embeddings to vectorize AI-generated solutions, the system constructs a highly searchable repository within Qdrant Cloud. This architecture elegantly isolates rigid execution constraints—like time limits and I/O formats—into payload metadata, allowing you to seamlessly retrieve historical solutions based purely on underlying algorithmic concepts and mathematical logic rather than exact keyword matches.

---

## 🛠️ Tech Stack
| Component | Technology |
|---|---|
| **Frontend** | Flutter, Dart |
| **Backend/Core** | Python |
| **AI Model** | OpenAI API, Groq API, Gemini API |
| **Neural Model** | Silero Vad, Whisper |
---

## ⚙️ Getting Started

### Prerequisites
Before you begin, ensure you have met the following requirements:
* [Flutter SDK](https://flutter.dev/docs/get-started/install) (Version X.X.X or higher)
* An API key for Groq, Gemini, OpenAI
* token.json file from google cloud console.
* Permission to access Google Calendar and Gmail on Google Cloud Console
* Codeforces handle

### Installation
**1. Clone the repository**
\`\`\`bash
git clone https://github.com/ruhaan0404-netizen/Shruti.git
cd Shruti
cd lib
\`\`\`

**2. Install dependencies**
\`\`\`
bash flutter pub get

pip install requirements.txt or uv add requirements.txt
\`\`\`

**3. Set up environment variables**
Create a `.env` file in the root directory and add your keys:
\`\`\`text
API_KEY=your_api_key_here
\`\`\`

**4. Run the app**
\`\`\`bash
python main.py
\`\`\`

---

## 🧭 Roadmap
- [x] Initial UI and basic agent responses
- [o] Websocket Connection
- [x] RAM memory audio file 
- [o] Add TTS pipelinne
- [x] Main Agent workflow and Supervisor pipeline
- [o] Integrate subagents
- [x] Debugging the workflow and the connection
- [o] Package for standalone Windows executable

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! 
1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

