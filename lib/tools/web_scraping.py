import os
import requests
from langchain.tools import tool
from load_dotenv import load_dotenv
import yfinance as yf
from langchain_google_genai import ChatGoogleGenerativeAI as genai

load_dotenv()

@tool
def get_user_location():
    """Get the the current location of the user."""
    response = requests.get("http://ip-api.com/json/")
    data = response.json()
    data.pop('status')
    data.pop('isp')
    data.pop('org')
    data.pop('as')
    data.pop('query')
    return data

@tool
def get_current_weather(loc:str):
    """Gives all the necessary and major weather details at the given location.
    Args:- loc = The name of the city at the location. But, can also take 'latitute,longitude' as value."""
    params={
        "key": os.getenv("WTR_API_KEY"),
        "q": loc,
        "aqi": "yes"
    }
    response = requests.get(f"http://api.weatherapi.com/v1/current.json",params=params).json()
    final_output = {
        "temp_celsius":response['current']['temp_c'],
        'is_day':response['current']['is_day'],
        'condition':response['current']['condition']['text'],
        'wind_kph':response['current']['wind_kph'],
        'wind_dir':response['current']['wind_dir'],
        'humidity':response['current']['humidity'],
        'cloud':response['current']['cloud'],
        'feelslike_celsius':response['current']['feelslike_c'],
        'heatindex_celsius':response['current']['heatindex_c'],
        'vis_km':response['current']['vis_km'],
        'aqi':response['current']['air_quality']
    }
    return final_output

@tool
def get_weather_alerts():
    """Gives you the weather alerts issued by the government. Empty array means 'no alerts'."""
    params={
        "key": os.getenv("WTR_API_KEY"),
        "q": "Mangalore",
        "alerts": "yes"
    }
    response = requests.get(f"http://api.weatherapi.com/v1/alerts.json",params=params).json()
    print(response['alerts']['alert'])
    return response['alerts']['alert']               

@tool
def get_ticker_symbol(company:str,stock_exchange:str):
    """Gets the ticker symbol for the given company and the stock exchange."""
    searcher = genai(
        api_key=os.getenv("CAL_KEY"),
        model="gemini-3.1-flash-preview",
        temperature=1
    )
    system_prompt=("You are a market analyst and a well-known experienced investor."
                   "For the given company name and the stock exchange, give the ticker symbol as mentioned on Yahoo Finance website.")
    all_messages=[system_prompt,f"company:{company}, stock exchange:{stock_exchange}"]
    response = searcher.invoke(all_messages)
    return response.text

@tool
def get_company_history(symbol:str,p:str):
    """Returns the company history.
    Args:-  symbol: symbol for the company as used in Yahoo finance.
            p: period (eg:-1y(year),1mo(month),3mo,6mo,ytd(till date from Jan 1st this year),max(since when the company started operating))"""
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=p)
    return history

@tool
def get_company_info(symbol:str):
    """Returns the basic info about the mentioned company."""
    ticker = yf.Ticker(symbol)
    info = ticker.info()
    return info

@tool
def get_earnings_calendar():
    """Returns the current earnings calendar."""
    calendars = yf.Calendars()
    earnings_calendar = calendars.get_earnings_calendar(limit=50)
    return earnings_calendar

@tool
def search_yf(c_name:str):
    """Searches yahoo finance to fetch specific information.
    Args:- c_name: company name to be searched"""
    response = yf.Search(query=c_name, max_results=5)
    print(response)
    return response

Web_tools = [get_user_location,get_company_info,get_ticker_symbol,get_company_history,get_current_weather,get_weather_alerts,get_earnings_calendar]