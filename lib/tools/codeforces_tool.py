import os
import json
import requests
from bs4 import BeautifulSoup
from load_dotenv import load_dotenv
from google import genai
from langchain.tools import tool
from qdrant_client.models import PointStruct

# Assuming this imports your initialized Qdrant client
from interact import client as qdrant_client 

load_dotenv()

# ==========================================
# Helper Functions
# ==========================================

def embedding_model(content_: str = "Hello, Jarvis!") -> list:
    """Generates embeddings using Google GenAI."""
    # Renamed to avoid shadowing the global Qdrant 'qdrant_client'
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
    # Safely read or initialize index
    try:
        with open("index.txt", "r") as f:
            content = f.read().strip()
            i = int(content) if content else 0
    except FileNotFoundError:
        i = 0

    # Increment and save index
    with open("index.txt", "w") as f:
        f.write(str(i + 1))

    # Generate vector
    text = f"{d.get('problem', '')} {d.get('solution', '')}"
    vector_data = embedding_model(text)

    # Create payload and upsert
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
# LangChain Tools
# ==========================================

@tool
def upload_question(model_summary: str) -> str:
    """Uploads a specific question and its AI-generated solution to the cloud database."""
    try:
        with open("specific_question.json", "r", encoding="utf-8") as f:
            diction = json.load(f)
        
        diction['solution'] = model_summary
        embedding_storage(diction)
        return "👨‍💻 Question uploaded successfully!"
    except Exception as e:
        return f"Error uploading question: {str(e)}"

@tool
def ask_codeforces(query_type: str, codeforces_url: str, phase: str = None, contest_id: int = None):
    """
    Retrieves information from Codeforces. 
    Valid query_types: 'contest_lists', 'contest_ratings', 'contest_standings', 'user_ratings', 'problem_set', 'specific_question'.
    """
    if contest_id is not None:
        # Avoid malforming URLs that already have parameters
        separator = "&" if "?" in codeforces_url else "?"
        codeforces_url = f"{codeforces_url}{separator}contestId={contest_id}"
        
    response = requests.get(codeforces_url)
    
    if response.status_code != 200:
        return {"Error": f"HTTP connection failed with status {response.status_code}."}

    # Handle HTML Scraping for specific problem pages
    if query_type == "specific_question":
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
        
        # Optionally save this to the local JSON file for the 'upload_question' tool
        with open("specific_question.json", "w", encoding="utf-8") as f:
            json.dump(diction, f, indent=4)
            
        return diction

    # Handle Standard Codeforces API JSON Responses
    try:
        # API requests return standard JSON, no need for BeautifulSoup parsing
        data = response.json() 
    except ValueError:
        return {"error": "Failed to parse JSON from Codeforces API."}

    if data.get('status') != 'OK':
        return {"error": data.get('comment', 'Unknown API error')}

    # Route based on query_type
    if query_type == "contest_lists":
        return [item for item in data['result'] if item.get('phase') != phase]
        
    elif query_type == "contest_ratings":
        return [item for item in data['result'] if item.get('handle') == 'Itu_Talishman']
        
    elif query_type == "contest_standings":
        relevant = [
            {"contests": data['result']['contest']},
            {"problems": data['result']['problems']},
            {"standings": [
                item for item in data['result']['rows'] 
                if item['party']['members'][0]['handle'] == 'Itu_Talishman'
            ]}
        ]
        return relevant
        
    elif query_type == "user_ratings":
        return data['result']
        
    elif query_type == "problem_set":
        return data["result"]["problems"]
        
    else:
        return {"error": "Malformed Request or Unknown query_type"}

@tool
def search_questions(search_text: str, limit: int = 3) -> list:
    """Searches the cloud database using a text query to find similar coding questions."""
    print(f"Searching for: '{search_text}'...")
    query_vector = embedding_model(search_text)
    
    search_results = qdrant_client.search(
        collection_name="coding_questions",
        query_vector=query_vector,
        limit=limit,
    )
    
    if not search_results:
        print("No matches found.")
        return []
        
    return search_results

@tool
def ask_question(question: str):
    """Queries the database directly using Qdrant's built-in query method."""
    response = qdrant_client.query(
        collection_name="coding_questions",
        query_text=question,
        limit=3, 
    )
    return response

# Export tools for LangGraph / LangChain
CODEFORCES_TOOLS = [ask_codeforces, ask_question, search_questions, upload_question]