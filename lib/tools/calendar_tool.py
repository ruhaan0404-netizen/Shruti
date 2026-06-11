from langchain_core.tools import tool
from tools import authorise
from googleapiclient.discovery import build
from pydantic import BaseModel, Field
from langchain.tools import tool
from typing import Optional

service = build("calendar",version='v3',credentials=authorise.my_credentials)

class EventDateTime(BaseModel):
    dateTime: str = Field(description="The time of the event strictly in RFC3339 format, e.g., '2026-06-10T15:30:00+05:30'")
    timeZone: Optional[str] = Field(default="Asia/Kolkata", description="The timezone, e.g., 'Asia/Kolkata'")

class EventDetails(BaseModel):
    summary: Optional[str] = Field(None, description="The title or name of the event.")
    start: Optional[EventDateTime] = Field(None, description="The new start time of the event.")
    end: Optional[EventDateTime] = Field(None, description="The new end time of the event.")
    description: Optional[str] = Field(None, description="Any notes or description for the event.")

@tool
def get_events(start:str,end:str,cal_id:str='primary'):
    """This tool helps you query the calendar and get the list of all the events starting from the start date to the end date."""
    global service
    event_list = service.events().list(
        calendarId=cal_id,
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return event_list.get('items',[])

@tool
def is_busy(start:str,end:str):
    """This tool doesn't give you event details but gives you the busy time slots from the start time to the end time."""
    global service
    busySlots = service.freebusy().query(
        body={
            "timeMin":start,
            "timeMax":end,
            "items":[{"id":"primary"}]
        }
    ).execute()
    return busySlots

@tool
def get_specific_event(start:str,end:str,event_name:str,cal_id:str='primary'):
    """This tool helps you check whether a given event occurs in the calendar from the start time to the end time."""
    global service
    event_details = service.events().list(
        calendarId=cal_id,
        q=event_name,
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return event_details.get('items',[])

@tool
def delete_event(event_id:str):
    """This tool helps you delete an event from the calendar.You cannot delete a religious holiday."""
    global service
    service.events().delete(
        calendarId='primary',
        eventId=event_id
    ).execute()

@tool
def update_event(event_id:str,event_details:str,calendar_id:str='primary'):
    """This tool helps you update an event in the calendar."""
    global service
    service.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=event_details
    ).execute()

@tool
def add_event(event_details:EventDetails):
    """This tool helps you add an event to the calendar. You cannot add any religious holiday."""
    global service
    service.events().insert(
        calendarId='primary',
        body=event_details
    ).execute()

CALENDAR_TOOLS = [get_events, is_busy, get_specific_event, delete_event, update_event, add_event]