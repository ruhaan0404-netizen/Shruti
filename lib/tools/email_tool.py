import base64
import re
from load_dotenv import load_dotenv
from tools import authorise
from googleapiclient.discovery import build
from email.message import EmailMessage
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Union, List
import operator

load_dotenv()

e_service = build("gmail",version='v1',credentials=authorise.my_credentials)

def is_valid_email(email: str) -> bool:
    """Basic regex to check if a string looks like a real email."""
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email.strip()))

writer_prompt=(
    "You are an expert email copywriter. Compose the email based on the user's instructions.\n"
    "1. `temporary_letter`: Your best email draft. Use placeholders (e.g., [Date], [Name]) if information is missing.\n"
    "2. `question_for_user`: Ask a single, concise question to gather missing details or clarify tone.\n"
    "3. `username`: Ask the user for the recipient's email address (e.g., uhand334@gmail.com). Replace 'at the rate' with '@'.\n"
    "CRITICAL: Once the draft is complete and requires no further input, you MUST ask the user 'Shall we finalise this?'. "
    "If the user responds positively, set `question_for_user` to exactly 'FINALISE!'. This acts as a system command to finish the task.\n"
    "Call the provided tool to structure your response." # <-- Added this gentle nudge
)

MSG = Union[HumanMessage,AIMessage]

class WriterState(TypedDict):
    messages:Annotated[List[MSG],operator.add]

class WriterResponse(BaseModel):
    temporary_letter:str = Field(description="The current, temporary draft which is yet to be finalised.")
    question_for_user:str = Field(description="Questions to be asked from the user to gather more information or finalise the draft.")

writer_model = init_chat_model("openai/gpt-oss-120b", model_provider="groq", temperature=0.7)
writer_agent = writer_model.with_structured_output(WriterResponse) 

def writer_node(state: WriterState):
    messages = [SystemMessage(content=writer_prompt)] + state["messages"]
    response: WriterResponse = writer_agent.invoke(messages)
    ai_msg = AIMessage(
        content=response.question_for_user,
        additional_kwargs={
            "temporary_letter": response.temporary_letter,
            "question_for_user": response.question_for_user
        }
    )
    return {"messages": [ai_msg]}

def conditional_node(state: WriterState):
    latest_message = state["messages"][-1]
    question = latest_message.additional_kwargs.get("question_for_user", "")
    print(question)
    if question == "FINALISE!":
        return END
    else:
        return "User_Query"

def user_query_node(state: dict): # <--- Back to standard 'def'
    import asyncio
    import io
    import numpy as np
    from scipy.io import wavfile
    
    # Local import to dodge the Circular Import bug
    import interact 

    latest_message = state["messages"][-1]
    kwargs = getattr(latest_message, "additional_kwargs", {})
    draft_text = kwargs.get("temporary_letter", "")
    question_to_ask = kwargs.get("question_for_user", "What would you like to do next?")

    print(f"\n📝 Draft text ready to send: {draft_text[:50]}...")
    print(interact.MAIN_LOOP)
    # 1. Update UI and Speak safely from a synchronous worker thread
    try:
        # Send the WebSocket message to the main Flutter loop
        if interact.MAIN_LOOP:
            asyncio.run_coroutine_threadsafe(
                interact.broadcast_state("draft_review", question_to_ask, draft_text=draft_text), 
                interact.MAIN_LOOP
            )
        
        # Because this background thread has NO loop, asyncio.run() works perfectly here for TTS
        asyncio.run(interact.speak_response(question_to_ask))
    except Exception as e:
        print(f"⚠️ UI/Speech Error: {e}")

    # 2. Open the microphone (blocks the thread naturally)
    print(f"\n[Agent]: {question_to_ask}")
    interact.listen() 

    # 3. Process the audio
    if interact.audio_buffer:
        print("🔄 Transcribing user feedback...")
        
        final_audio = np.concatenate(interact.audio_buffer, axis=0).flatten()
        virtual_file = io.BytesIO()
        wavfile.write(virtual_file, interact.SAMPLE_RATE, final_audio)
        virtual_file.seek(0)
        
        try:
            # Because we are in a 'def', we don't need threading for Groq! We just call it directly.
            transcription = interact.client.audio.transcriptions.create(
                file=("audio.wav", virtual_file.read()), 
                model="whisper-large-v3",
                response_format="text",
                temperature=0.0
            )
            
            user_feedback = transcription.strip()
            print(f"🗣️ User replied: {user_feedback}")
            return {"messages": [("user", user_feedback)]}
            
        except Exception as e:
            print(f"❌ Whisper Error in node: {e}")
            return {"messages": [("user", "Transcription failed. Please make your best guess.")]}
    else:
        return {"messages": [("user", "No audio detected. Please proceed.")]}

sub_graph = StateGraph(WriterState)
sub_graph.add_node("Writer",writer_node)
sub_graph.add_node("User_Query",user_query_node)

sub_graph.add_edge(START,"Writer")
sub_graph.add_conditional_edges("Writer",conditional_node)
sub_graph.add_edge("User_Query","Writer")
compiled_sub_graph = sub_graph.compile()

# ___TOOLS___ #
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

    # 1. Update UI and Speak (Synchronous wrapper)
    try:
        if interact.MAIN_LOOP:
            asyncio.run_coroutine_threadsafe(
                interact.broadcast_state("asking_user", question, draft_text=""), 
                interact.MAIN_LOOP
            )
        asyncio.run(interact.speak_response(question))
    except Exception as e:
        print(f"⚠️ UI/Speech Error: {e}")

    # 2. Listen via Microphone
    print(f"\n[Agent]: {question}")
    interact.listen()

    # 3. Process Audio with Whisper
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
def get_my_email_address():
    """Retrieves email address of the authenticated user."""
    profile = e_service.users().getProfile(userId='me').execute()
    return profile.get('emailAddress')

@tool
def create_draft(to:str,sender:str,subject:str,message_body:str):
    """Save the draft to gmail."""
    # --- THE SAFETY GATE ---
    if not is_valid_email(to):
        return f"ERROR: '{to}' is not a valid email address. Stop. Use the `ask_user` tool to ask the user for the correct email address."
    # -----------------------
    try:
        message = EmailMessage()
        message.set_content(message_body)
        message['To'] = to.strip()
        message['From'] = sender
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft_body={'message':{'raw':encoded_message}}
        
        draft = e_service.users().drafts().create(userId='me',body=draft_body).execute()
        return f"Draft created successfully. Draft ID: {draft.get('id')}"
    except Exception as e:
        return f"Error from Gmail API: {str(e)}"

@tool
def email_content_creation(user:str)->str:
    """Get the body content for the email draft."""
    graph_inputs = {"messages": [HumanMessage(content=user)]}
    final_state = compiled_sub_graph.invoke(graph_inputs)
    
    # Extract the draft from additional_kwargs instead of .content
    last_message = final_state["messages"][-1]
    agent_response = last_message.additional_kwargs.get("temporary_letter", "Draft missing.")
    print(agent_response)
    return agent_response

@tool
def send_mail(draft_id:str):
    """This tool helps you send a saved draft."""
    try:
        e_service.users().drafts().send(userId='me',body={"id":draft_id}).execute()
        return "The email has been sent successfully."
    except:
        return "Error sending the email."

@tool
def update_draft(draft_id:str,new_to:str,new_from:str,new_subject:str,new_content:str):
    """Updates the saved draft."""
    message = EmailMessage()
    message.set_content(new_content)
    message['To']=new_to
    message['From']=new_from
    message['Subject']=new_subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft_body={"message":{"raw": encoded_message}}
    updated_draft = e_service.users().drafts().update(userId='me',id=draft_id,body=draft_body).execute()
    return updated_draft

@tool
def get_saved_draft(draft_id:str):
    """Retrieve all the information about a saved draft justby using the ID through which the draft was saved."""
    draft=e_service.users().drafts().get(
        userId='me',
        id=draft_id,
        format='full'
    ).execute()
    return draft

@tool
def find_draft_id(to:str,subject:str,body_keys:str):
    """Searches draft based on basic criteria and returns draft ID. 
    body_keys: Some keywords from the email body to ease the search process."""
    query_parts=[]
    if to:
        query_parts.append(f"to:{to}")
    if subject:
        query_parts.append(f"subject:{subject}")
    if body_keys:
        query_parts.append(f"{body_keys}")

    search_query = " ".join(query_parts)
    results = e_service.users().drafts().list(userId='me',q=search_query).execute()
    drafts = results.get('drafts',[])
    if not drafts:
        return "No drafts found!"
    else:
        return drafts

EMAIL_TOOLS = [get_my_email_address,create_draft,email_content_creation,send_mail,update_draft,get_saved_draft,find_draft_id,ask_user]
