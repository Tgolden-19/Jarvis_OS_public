import requests
from dotenv import load_dotenv
import os
import json
import asyncio
import commands.validators as validators


load_dotenv()

weather_key = os.getenv('OPENWEATHER_API_KEY')
weather_zip = os.getenv('WEATHER_ZIP')
weather_lat = os.getenv('WEATHER_LAT')
weather_lon = os.getenv('WEATHER_LON')


async def get_weather_coords(lat=weather_lat, lon=weather_lon):
    print("getting weather...")
    url = "https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={weather_key}"
    response = requests.get(url)
    if response.status_code == 200:
        print("got weather info")
        return response.json()
    else:
        print('Error occured: '+ response.status_code, response.text)
        return None
    
def location_to_coords(location):
    pass

def zip_to_coords(zipcode=weather_zip, countrycode=1):
    pass

async def parse_weather_data(section, resp_type, weather_data):
    assert(section in ['current', 'minutely', 'hourly', 'daily'])
    assert(resp_type in ['description', 'data', 'summary'])
    sect_filter = weather_data[section]
    if resp_type == 'description':
        desc = sect_filter['weather']['description']
        return desc
    elif resp_type == 'data':
        data = {
            "temp": sect_filter['temp'],
            "feels_like": sect_filter['feels_like'],
            "humidity": sect_filter['humidity']
        }
        return data
    else:
        return sect_filter