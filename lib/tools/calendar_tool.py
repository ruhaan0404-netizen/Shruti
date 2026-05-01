from langchain_core.tools import tool
from tools import authorise
from googleapiclient.discovery import build

service = build("calendar",version='v3',credentials=authorise.my_credentials)

@tool
def get_events(start:str,end:str,cal_id:str='primary'):
    """This tool helps you query the calendar and get the list of all the events starting from the start date to the end date.
    Args:-
        start: start date and time in STRICT ISO format with Kolkata offset. Example: '2026-04-27T09:00:00+05:30'
        end: end date and time in STRICT ISO format with Kolkata offset. Example: '2026-04-27T17:00:00+05:30'
        cal_Id: 'primary' for meetings, etc. Keep it 'primary' if not stated explicitly. For religious holidays 'en.indian#holiday@group.v.calendar.google.com'"""
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
    """This tool doesn't give you event details but gives you the busy time slots from the start time to the end time.
    Args:-
        start: start date and time in iso format, timezone: "Asia/Kolkata
        end: end date and time in iso format, timezone: "Asia/kolkata"""
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
    """This tool helps you check whether a given event occurs in the calendar from the start time to the end time.
    Args:-
        start: start date and time in iso format, timezone: "Asia/Kolkata 
        end: end date and time in iso format, timezone: "Asia/kolkata 
        cal_id: 'primary' for meetings, birthdays, etc. and 'en.indian#holiday@group.v.calendar.google.com' for religious holidays. Keep it primary if not stated explicitly."""
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
    """This tool helps you delete an event from the calendar.You cannot delete a religious holiday.
    Args:-
        event_id: name of the event"""
    global service
    service.events().delete(
        calendarId='primary',
        eventId=event_id
    ).execute()

@tool
def update_event(event_id:str,event_details:str,calendar_id:str='primary'):
    """This tool helps you update an event in the calendar.
    Args:-
    Args:-
        start: start date and time in iso format, timezone: "Asia/Kolkata
        end: end date and time in iso format, timezone: "Asia/kolkata
        cal_Id: 'primary' for meetings, birthdays, etc. and 'en.indian#holiday@group.v.calendar.google.com' for religious holidays.Keep it primary if not stated explicitly.
        event_details:{
            "title": "Meeting with Ajith Sir",
            "start_datetime": "20260427T1030",  # Format: yyyymmddTHHMM
            "duration": "1h",                   # Format: [number]d[number]h[number]m
            "location": "College Campus, Bangalore",
            "description": "Discussing the 'The Dream Not Too Far' speech and attendance records.",
            "attendees": ["ajith_sir@example.edu", "manoj@example.edu"],
            "is_all_day": False
        }"""
    global service
    service.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=event_details
    ).execute()

@tool
def add_event(event_details:str):
    """This tool helps you add an event to the calendar. You cannot add any religious holiday.
    This is a sample for understanding the format in which the arguments should be passed.
    Args:-
    event_details:{
    "summary": "Project Sync",
    "location": "Bengaluru, Karnataka",
    "description": "Discussing the upcoming launch and timelines.",
    "start": {
        "dateTime": "2026-04-28T10:00:00+05:30",
        "timeZone": "Asia/Kolkata"
    },
    "end": {
            "dateTime": "2026-04-28T11:00:00+05:30",
            "timeZone": "Asia/Kolkata"
        },
        "attendees": [
            {
            "email": "colleague@example.com"
            }
        ],
        "reminders": {
            "useDefault": false,
            "overrides": [
            {
                "method": "email",
                "minutes": 1440
            },
            {
                "method": "popup",
                "minutes": 10
            }
            ]
        }
    }"""
    global service
    service.events().insert(
        calendarId='primary',
        body=event_details
    ).execute()

Calendar_tools = [get_events, is_busy, get_specific_event, delete_event, update_event, add_event]