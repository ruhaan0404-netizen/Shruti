import os
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from load_dotenv import load_dotenv
from google import genai
from langchain.tools import tool
from qdrant_client.models import PointStruct
from qdrant_client import QdrantClient

load_dotenv()

qdrant_client = QdrantClient(
    url=os.getenv("NODE"),
    api_key=os.getenv("CLOUD_CLUSTER"),
    cloud_inference=True,
    https=True,
    prefer_grpc=False,
    check_compatibility=False
)

# ==========================================
# Helper Functions
# ==========================================

def embedding_model(content_: str = "Hey, Shruti!") -> list:
    """Generates embeddings using Google GenAI."""
    genai_client = genai.Client(api_key=os.getenv("CAL_KEY"))
    result = genai_client.models.embed_content(
        model="gemini-embedding-2",
        contents=content_
    )
    return result.embeddings[0].values

def upsert_points(points: list[PointStruct]):
    """Upserts vector points to the Qdrant database."""
    qdrant_client.upsert(
        collection_name="coding_questions",
        points=points,
    )

def embedding_storage(d: dict):
    """Handles index generation and stores the problem/solution in Qdrant."""
    try:
        with open("index.txt", "r") as f:
            content = f.read().strip()
            i = int(content) if content else 0
    except FileNotFoundError:
        i = 0
    with open("index.txt", "w") as f:
        f.write(str(i + 1))
    text = f"{d.get('problem', '')} {d.get('solution', '')}"
    vector_data = embedding_model(text)
    point = PointStruct(
        id=i,
        vector=vector_data,
        payload={
            "title": d.get('metadata', {}).get('title', ''),
            "description": d.get('description', ''),
            "time_limit": d.get('metadata', {}).get('time_limit', ''),
            "output": d.get('metadata', {}).get('output', ''),
        }
    )
    upsert_points([point])

# ==========================================
#             LangChain Tools
# ==========================================

@tool
def ask_user(question: str) -> str:
    """
    Call this tool when you are missing critical information to draft an email 
    (e.g., recipient email address, subject line, or specific content details).
    """
    import asyncio
    import io
    import numpy as np
    from scipy.io import wavfile
    import interact 
    try:
        if interact.MAIN_LOOP:
            asyncio.run_coroutine_threadsafe(
                interact.broadcast_state("asking_user", question, draft_text=""), 
                interact.MAIN_LOOP
            )
        asyncio.run(interact.speak_response(question))
    except Exception as e:
        print(f"⚠️ UI/Speech Error: {e}")
    print(f"\n[Agent]: {question}")
    interact.listen()
    if interact.audio_buffer:
        final_audio = np.concatenate(interact.audio_buffer, axis=0).flatten()
        virtual_file = io.BytesIO()
        wavfile.write(virtual_file, interact.SAMPLE_RATE, final_audio)
        virtual_file.seek(0)
        try:
            transcription = interact.client.audio.transcriptions.create(
                file=("audio.wav", virtual_file.read()), 
                model="whisper-large-v3",
                response_format="text",
                temperature=0.0
            )
            return transcription.strip()
        except Exception as e:
            return f"System Error: User spoke, but transcription failed ({e}). Ask them to repeat."
    return "System Error: No audio detected. Please ask the user again."

@tool
def upload_question(model_summary: str) -> str:
    """Uploads a specific question and its AI-generated solution to the cloud database."""
    try:
        folder = Path("C:\\Users\\Rishav\\Jarvis\\lib\\memory")
        file = folder/"recent_submission.json"
        with open(file, "r", encoding="utf-8") as f:
            diction = json.load(f)
        diction['solution'] = model_summary
        embedding_storage(diction)
        return "👨‍💻 Question uploaded successfully!"
    except Exception as e:
        return f"Error uploading question: {str(e)}"

@tool
def latest_solved_question():
    """Returns the latest submitted question which the user solved successfully."""
    folder = Path("C:\\Users\\Rishav\\Jarvis\\lib\\memory")
    file = folder/"recent_submission.json"
    try:
        with open(file,"r") as f:
            submissions = json.load(fp=f)
            return submissions[0]
    except FileExistsError or FileNotFoundError:
        return {"Error":"Error opening the file."}

@tool
def ask_codeforces(codeforces_url: str, contest_id: int = None):
    """
    Retrieves information about a specific question from Codeforces. 
    """
    try:
        if contest_id is not None:
            separator = "&" if "?" in codeforces_url else "?"
            codeforces_url = f"{codeforces_url}{separator}contestId={contest_id}"  
        response = requests.get(codeforces_url)
        if response.status_code != 200:
            return {"Error": f"HTTP connection failed with status {response.status_code}."}
        soup = BeautifulSoup(response.content, 'lxml')
        problem_part = soup.find("div", class_="problem-statement")
        if not problem_part:
            return {"error": "Could not find problem statement on the page."}
        children_divs = problem_part.find_all("div", recursive=False)
        main_text = children_divs[1].get_text(separator=" ", strip=True) if len(children_divs) > 1 else ""
        diction = {
            "metadata": {
                "title": problem_part.find("div", class_="title").get_text(strip=True),
                "time_limit": problem_part.find("div", class_="time-limit").get_text(" ", strip=True).replace("time limit per test ", ""),
                "output": problem_part.find("div", class_="output-specification").get_text(separator=" ", strip=True)
            },
            "problem": main_text,
            "solution": ""
        }
        folder=Path("C:\\Users\\Rishav\\Jarvis\\lib\\memory")
        file = folder/"specific_question.json"
        with open(file, "w", encoding="utf-8") as f:
            json.dump(diction, f, indent=4)
        return diction
    except ConnectionError:
        return {"error": "Malformed Request or Unknown query_type"}

@tool
def search_database(question: str):
    """Queries the database directly using Qdrant's built-in query method."""
    response = qdrant_client.query(
        collection_name="coding_questions",
        query_text=question,
        limit=3, 
    )
    return response

CODEFORCES_TOOLS = [ask_codeforces, search_database, upload_question, ask_user, latest_solved_question]