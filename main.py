import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry
from geopy.geocoders import Nominatim

import speech_recognition as sr
import pyttsx3

import datetime
import os

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

geolocator = Nominatim(user_agent="my_geocoder")

r = sr.Recognizer()

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

url = "https://api.open-meteo.com/v1/forecast"

number_words = {
    "eins": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
    "sieben": 7,
    "acht": 8,
    "neun": 9,
    "zehn": 10,
    "elf": 11,
    "zwölf": 12,
    "dreizehn": 13,
    "vierzehn": 14,
    "fünfzehn": 15,
    "sechzehn": 16
}

def speak(audio):
    print(f"Assistent: {audio}")
    engine.say(audio)
    engine.runAndWait()


def takeCommand():
    r = sr.Recognizer()

    with sr.Microphone() as source:

        print("Höre zu...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Verarbeite...")
        query = r.recognize_google(audio, language='de-DE')
        print(f"Du hast gesagt: {query}\n")

    except Exception as e:
        print(e)
        print("Keine Stimme erkannt")
        return "None"

    return query


def greeting():
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Guten Morgen")

    elif 12 <= hour < 18:
        speak("Guten Mittag")

    else:
        speak("Guten Abend")

    speak("Willkommen bei Ihrem Wetter Sprachassistent.")

fail = False

def getWeatherVariable():
    global fail
    if not fail:
        speak("Als erstes müssen sie mir sagen, in welchem Wetterformat sie ihre Daten haben wollen. Bitte antworten Sie mit Stunden, Tagen oder jetziges Wetter.")
    query = takeCommand().lower()

    if 'stunden' in query:
        fail = False
        return 'hours'
    
    elif 'tagen' in query:
        fail = False
        return 'days'
    
    elif 'jetziges wetter' in query:
        fail = False
        return 'current'

    else:
        fail = True
        speak("Leider habe ich Sie nicht verstanden. Versuchen sie es erneut")
        getWeatherVariable()

def getForecastDays():
    global fail
    if not fail:
        speak("Bitte sagen Sie mir für wie viele Tage Sie die Wettervorhersage haben möchten. Bitte nennen Sie eine Zahl zwischen 1 und 16")
    query = takeCommand().lower()

    if query.isalpha():
        number = number_words.get(query, 0)
    else:
        number = int(query)

    if number <= 16 and number >= 1:
        fail = False
        return number
    else:
        fail = True
        speak("Leider habe ich Sie nicht verstanden. Versuchen sie es erneut")
        getForecastDays()

def getCity():
    global fail
    if not fail:
        speak("Bitte nennen Sie mir nun die Stadt, für die Sie die Wetterdaten haben möchten.")
    query = takeCommand().lower()

    location = geolocator.geocode(query)

    if location:
        fail = False
        return location
    else:
       fail = True
       speak("Ich habe Sie nicht verstanden oder konnte keine Stadt mit dem Namen finden. Bitte versuchen Sie es erneut.")
       getCity()

if __name__ == '__main__':
    clear = lambda: os.system('cls')
    clear()
    greeting()
    weatherVariable = getWeatherVariable()

    if weatherVariable in ('days','hours'):
        forecastDays = getForecastDays()

    city = getCity()
    
    latitude = city.latitude
    longitude = city.longitude
    
    if weatherVariable == 'current':
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timeformat": "unixtime",
            "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day", "precipitation", "rain", "showers", "snowfall", "weather_code", "wind_speed_10m", "wind_direction_10m"],
            "timezone": "Europe/Berlin",
        }

        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        current = response.Current()
        current_temperature_2m = current.Variables(0).Value()
        current_relative_humidity_2m = current.Variables(1).Value()
        current_apparent_temperature = current.Variables(2).Value()
        current_is_day = current.Variables(3).Value()
        current_weather_code = current.Variables(4).Value()
        current_wind_speed_10m = current.Variables(5).Value()
        current_wind_direction_10m = current.Variables(6).Value()

        if current_is_day > 0:
            speak(f"In {city} ist es gerade Tag und die Temperatur beträgt momentan {current_temperature_2m} C° bei einer relativen Luftfeuchtigkeit von {current_relative_humidity_2m}%")
            
        
        
       
        print(f"Current weather_code {current_weather_code}")
        print(f"Current wind_speed_10m {current_wind_speed_10m}")
        print(f"Current wind_direction_10m {current_wind_direction_10m}")

    #elif weatherVariable == 'days':
      #  params = {
       #     "latitude": latitude,
       #     "longitude": longitude,
        #    "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset", "daylight_duration", "sunshine_duration", "uv_index_max", "precipitation_probability_max"],
        #   "timezone": "Europe/Berlin",
          #  "forecast_days": forecastDays
       # }
