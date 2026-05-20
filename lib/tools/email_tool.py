import base64
import os
from load_dotenv import load_dotenv
from tools import authorise
from googleapiclient.discovery import build
from email.message import EmailMessage
from groq import Groq
from langchain.tools import tool

load_dotenv()

e_service = build("gmail",version='v1',credentials=authorise.my_credentials)

# ___TOOLS___ #
@tool
def get_my_email_address():
    """Retrieves email address of the authenticated user."""
    profile = e_service.users().getProfile(
        userId='me'
     ).execute()
    return profile.get('emailAddress')

@tool
def create_draft(to:str,sender:str,subject:str,message_body:str):
    """This tool helps you in creating and saving the draft into gmail. You need to pass
    'to': reciever's email address
    'sender': sender's email address
    'subject': subject of the email
    'message': main body or content of the email"""

    message = EmailMessage()
    message.set_content(message_body)
    message['To'] = to
    message['From'] = sender
    message['Subject'] = subject
    
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft_body={
        'message':{
            'raw':encoded_message
        }
    }

    draft = e_service.users().drafts().create(
        userId='me',
        body=draft_body
    ).execute()
    return draft

@tool
def email_content_creation(user:str)->str:
    """This tool activates a writer llm which specialises in content creation. 
    Use it to generate the content for the main body of the email. 
    Pass it a prompt containing all the details pertinent to the email main body as specified by the user."""
    system_prompt=("You are a model who is expert in writing emails. "
                    "Your job is to compose the main body of the email following the standard format for email composition."
                    "Understand the context, and ask for specific details and review from the user."
                    "Don't mention the subject in the body."
                    "When the complete email body is generated, add a question asking the user to finalise or suggest some changes."
                    "The question should be framed exactly like this:"
                    "*** HOW IS IT?"
                    "*** FINALISE!"
                    "*** SUGGEST SOME CHANGES.")
    History=[
        {
            "role":"system",
            "content":system_prompt
        },
    ]
    writer = Groq(api_key=os.getenv("GROQ_API_KEY"))
    while(user!="FINALISE!"):
        History.append({"role":"user","content":user})
        response = writer.chat.completions.create(
            messages=History,
            model="openai/gpt-oss-120b",
            temperature=0.6
        )
        print(f"Writer:\n{response.choices[0].message.content}")
        History.append({"role":"assistant",
                            "content":response.choices[0].message.content})
        user = input()
    output, question = History[-1]["content"].split("*** HOW IS IT?")
    return output

@tool
def send_mail(draft_id:str):
    """This tool helps you send a saved draft."""
    try:
        e_service.users().drafts().send(
            userId='me',
            body={"id":draft_id}
        ).execute()
        return "The email has been sent successfully."
    except:
        return "Error sending the email."

@tool
def update_draft(draft_id:str,new_to:str,new_from:str,new_subject:str,new_content:str):
    """Updates the saved draft.
    Args:
        draft_id: ID of the saved draft
        new_to: new or the original reciever
        new_from: new or the original sender
        new_subject: new or the original subject
        new_content new content for the email body
        """
    message = EmailMessage()
    message.set_content(new_content)
    message['To']=new_to
    message['From']=new_from
    message['Subject']=new_subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft_body={
        "message":{
            "raw": encoded_message
        }
    }
    updated_draft = e_service.users().drafts().update(
        userId='me',
        id=draft_id,
        body=draft_body
    ).execute()
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
    
    results = e_service.users().drafts().list(
        userId='me',
        q=search_query
    ).execute()

    drafts = results.get('drafts',[])
    if not drafts:
        return "No drafts found!"
    else:
        return drafts

Email_tools = [get_my_email_address,create_draft,email_content_creation,send_mail,update_draft,get_saved_draft,find_draft_id]
