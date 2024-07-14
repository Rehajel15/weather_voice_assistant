import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry

import speech_recognition as sr
import pyttsx3

import datetime
import os

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

r = sr.Recognizer()

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
    
    elif 'täglich' in query:
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

    number = number_words.get(query, None)

    if number <= 16 or number >= 1:
        fail = False
        return number
    else:
        fail = True
        speak("Leider habe ich Sie nicht verstanden. Versuchen sie es erneut")
        getForecastDays()


if __name__ == '__main__':
    clear = lambda: os.system('cls')
    clear()
    greeting()
    weatherVariable = getWeatherVariable()

    if weatherVariable == 'days' or weatherVariable == 'hours':
        forecastDays = getForecastDays()
        speak("Weiter geht's")
    else:
        speak("Weiter geht's")




# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 51.5623,
	"longitude": 6.7434,
	"hourly": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "rain", "visibility", "wind_speed_80m", "temperature_80m", "soil_temperature_18cm"],
	"timezone": "Europe/Berlin",
	"forecast_days": 1
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
hourly_apparent_temperature = hourly.Variables(2).ValuesAsNumpy()
hourly_rain = hourly.Variables(3).ValuesAsNumpy()
hourly_visibility = hourly.Variables(4).ValuesAsNumpy()
hourly_wind_speed_80m = hourly.Variables(5).ValuesAsNumpy()
hourly_temperature_80m = hourly.Variables(6).ValuesAsNumpy()
hourly_soil_temperature_18cm = hourly.Variables(7).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}
hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
hourly_data["apparent_temperature"] = hourly_apparent_temperature
hourly_data["rain"] = hourly_rain
hourly_data["visibility"] = hourly_visibility
hourly_data["wind_speed_80m"] = hourly_wind_speed_80m
hourly_data["temperature_80m"] = hourly_temperature_80m
hourly_data["soil_temperature_18cm"] = hourly_soil_temperature_18cm

hourly_dataframe = pd.DataFrame(data = hourly_data)
print(hourly_dataframe)