import os
import asyncio
import httpx
import json
from load_dotenv import load_dotenv
from google import genai
import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import UnstructuredPDFLoader
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Document

load_dotenv()

background_tasks=set()

client = AsyncQdrantClient(
    url=os.getenv("NODE"),
    api_key=os.getenv("CLOUD_CLUSTER"),
    cloud_inference=True
)

async def create_collection(collection_name="coding_questions"):
    if await client.collection_exists(collection_name):
            print(f"Collection '{collection_name}' already exists. Skipping creation.")
    else:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
        print(f"Collection '{collection_name}' created successfully for the first time!")

async def get_specific_question(model_summary:str):
    with open("specific_question.json","r",encoding="utf-8") as f:
        s= f.read()
        diction = json.loads(s)
    diction['solution']=model_summary
    await embedding_storage(diction)

async def embedding_model(content_:str="Hello, Jarvis!"):
    client = genai.Client(api_key=os.getenv("CAL_KEY"))
    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=content_
    )
    return result.embeddings[0].values

async def upsert_points(points:list[PointStruct]):
    await client.upsert(
    collection_name="coding_questions",
    points=points,
    )

async def embedding_storage(d:dict):
    with open("index.txt","r") as f:
        i=int(f.read().strip() or 0)
    with open("index.txt","w") as f:
        f.write(str(i+1))
    text = f"{d.get('problem', '')} {d.get('solution', '')}"
    vector_data = await embedding_model(text)
    point = PointStruct(
    id=i,
    vector=vector_data,
    payload={
        "title": d['metadata']['title'],
        "description": d.get('description', ''),
        "time_limit": d['metadata']['time_limit'],
        "output": d['metadata']['output'],
    }
    )
    await upsert_points([point])

def ask_codeforces(file_name:str,file_url:str,phase:str=None,contest_id:int=None):
    if contest_id != None:
        file_url=file_url+f"?contestId={contest_id}"
    response = requests.get(file_url)
    soup = BeautifulSoup(response.content,'lxml')
    soup.prettify()
    contents = soup.p.get_text(strip=True)
    if file_name=="contest_lists":
        diction = json.loads(contents)
        relevant = [item for item in diction['result'] if item['phase'] != phase]
    elif file_name=="contest_ratings":
        diction = json.loads(contents)
        relevant = [item for item in diction['result'] if item['handle'] == 'Itu_Talishman']
    elif file_name=="contest_standings":
        diction = json.loads(contents)
        relevant = [{"contests":diction['result']['contest']}]
        relevant.append({"problems":diction['result']['problems']})
        relevant.append({"standings":[item for item in diction['result']['rows'] if item['party']['members'][0]['handle']=='Itu_Talishman']})
    elif file_name=="user_ratings":
        diction = json.loads(contents)
        relevant = diction['result']
    elif file_name=="problem_set":
        diction = json.loads(contents)
        relevant = diction["result"]["problems"]
    elif file_name=="specific_question":
        problem_part=soup.find("div",class_="problem-statement")
        relevant = problem_part.get_text(separator="\n",strip=True)
        children_divs = problem_part.find_all("div", recursive=False)
        main_text = children_divs[1].get_text(separator=" ", strip=True)
        diction = {"metadata":{"title":problem_part.find("div",class_="title").get_text(),
                    "time_limit":problem_part.find("div",class_="time-limit").get_text(" ", strip=True).replace("time limit per test ", ""),
                    "output":problem_part.find("div", class_="output-specification").get_text(separator=" ", strip=True)}
                    ,"problem":main_text
                    ,"solution":""
        }
        with open(f"{file_name}.json","w",encoding="utf-8") as f:
            json.dump(diction,f,ensure_ascii=False,indent=2)
        return "Request Successful"
    else:
        return "Malformed Request"
    if response.status_code == 200:
        file = open(f"{file_name}.json",'w')
        file.close()
        with open(f"{file_name}.json",'a',encoding='utf-8') as f:
            json.dump(relevant,fp=f,indent=1)
        return "Request successful."
    else:
        return "Request failed."

async def get_sub_history():
    async with httpx.AsyncClient() as client:
        while(True):
            response = await client.get("https://codeforces.com/api/user.status?handle=Itu_Talishman&from=1&count=30")
            soup = BeautifulSoup(response.content,'lxml')
            soup.prettify()
            contents = soup.p.get_text(strip=True)
            diction = json.loads(contents)
            relevant = diction['result']
            with open("recent_submission.json","w") as f:
                json.dump(relevant,fp=f,indent=1)
            print("stuck")
            await asyncio.sleep(1800)

async def search_questions(search_text: str, limit: int = 3):
    print(f"Searching for: '{search_text}'...")
    query_vector = await embedding_model(search_text)
    search_results = await client.search(
        collection_name="coding_questions",
        query_vector=query_vector,
        limit=limit,
    )
    if not search_results:
        print("No matches found.")
        return

    print("\n--- Top Matches ---")
    for hit in search_results:
        print(f"Score: {hit.score:.4f} | Title: {hit.payload.get('title', 'Unknown')}")
        print(f"Output Format: {hit.payload.get('output', 'N/A')}")
        print("-" * 30)
    return 


async def main():
    await create_collection()
    task = asyncio.create_task(get_sub_history())
    background_tasks.add(task)
    print("running in background")
    ask_codeforces('specific_question',"https://codeforces.com/contest/2223/problem/A")
    await task

asyncio.run(main())