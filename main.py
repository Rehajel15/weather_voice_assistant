import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry
from geopy.geocoders import Nominatim
import numpy as np

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
        print(f"Sie haben gesagt: {query}\n")

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
        speak("Als erstes müssen Sie mir sagen, ob Sie das aktuelle Wetter oder eine Wettervorhersage haben möchten. Bitte sagen Sie jetziges Wetter oder Wettervorhersage")
    
    query = takeCommand().lower()

    if 'jetziges wetter' in query:
        fail = False
        return 'current'
    
    elif 'wettervorhersage' in query:
        fail = False
        return 'days'
    
    else:
        fail = True
        speak("Ungültige Eingabe. Versuchen Sie es erneut.")
        return 'error'


def getForecastDays():
    global fail
    if not fail:
        speak("Bitte sagen Sie mir für wie viele Tage Sie die Wettervorhersage haben möchten. Bitte nennen Sie eine Zahl zwischen 1 und 14")
    query = takeCommand().lower()

    if query.isalpha():
        number = number_words.get(query, 0)
    else:
        number = int(query)

    if number <= 14 and number >= 1:
        fail = False
        return number
    else:
        fail = True
        speak("Ungültige Eingabe. Versuchen Sie es erneut.")
        return 'error'

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
       return 'error'

def tellWeather(weather_code):
    match weather_code:
        case 0:
            return "klarem Himmel"
        case 1:
            return "hautpsächlich klarem Himmel" 
        case 2:
            return "teilweise bewölktem Himmel"
        case 3:
            return "bewölktem Himmel"
        case 45:
            return "Nebel"
        case 48:
            return "ablagernden Raureifnebel"
        case 51:
            return "leichtem Nieselregen"
        case 53:
            return "mäßigem Nieselregen"
        case 55:
            return "dichtem Nieselregen"
        case 56:
            return "leichtem gefrierendem Nieselregen"
        case 57:
            return "dichtem gefrierendem Nieselregen"
        case 61:
            return "leichtem Regen"
        case 63:
            return "mäßigem Regen"
        case 65:
            return "starkem Regen"
        case 66:
            return "leichtem Eisregen"
        case 67: 
            return "starkem Eisregen"
        case 71:
            return "leichtem Schneefall"
        case 73:
            return "mäßigem Schneefall"
        case 75:
            return "starkem Schneefall"
        case 77:
            return "fallenden Schneekörnern"
        case 80:
            return "leichtem Regenschauer"
        case 81:
            return "mäßigem Regenschauer"
        case 82:
            return "heftigem Regenschauer"
        case 85:
            return "leichtem Schneeschauer"
        case 86:
            return "heftigem Schneeschauer"
        case 95:
            return "leichtem bis mäßgen Gewitter"
        case 96:
            return "Gewitter und leichtem Hagel"
        case 99:
            return "Gewitter und schwerem Hagel"
        

if __name__ == '__main__':
    clear = lambda: os.system('cls')
    clear()
    greeting()
    while True:
        weatherVariable = getWeatherVariable()

        while weatherVariable == 'error':
            weatherVariable = getWeatherVariable()

        if weatherVariable == 'days':
            forecastDays = getForecastDays()
            while forecastDays == 'error':
                forecastDays = getForecastDays()

        forecastDays = forecastDays + 2

        city = getCity()

        while city == 'error':
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
            current_temperature_2m = np.round(current_temperature_2m, 1)
            current_temperature_2m = str(current_temperature_2m).replace(".", ",")

            current_relative_humidity_2m = current.Variables(1).Value()
            current_relative_humidity_2m = np.round(current_relative_humidity_2m, 1)
            current_relative_humidity_2m = str(current_relative_humidity_2m).replace(".", ",")

            current_is_day = current.Variables(2).Value()

            if current_is_day == 0:
                dayOrNight = "Nacht"
            else:
                dayOrNight = "Tag"

            current_weather_code = current.Variables(3).Value()

            
            current_wind_speed_10m = current.Variables(4).Value()
            current_wind_speed_10m = np.round(current_wind_speed_10m, 1)
            current_wind_speed_10m = str(current_wind_speed_10m).replace(".", ",")


            current_wind_direction_10m = current.Variables(5).Value()
            current_wind_direction_10m = np.round(current_wind_direction_10m, 1)
            current_wind_direction_10m = str(current_wind_direction_10m).replace(".", ",")

            
            speak(f"In {city} ist es gerade {dayOrNight} mit {tellWeather(current_weather_code)} und die Temperatur beträgt momentan {current_temperature_2m} grad bei einer relativen Luftfeuchtigkeit von {current_relative_humidity_2m}%.")
            speak(f"Die aktuelle Windgeschwindigkeit auf 10 Metern beträgt {current_wind_speed_10m} km/h in der Himmelsrichtung {current_wind_direction_10m}°.")

        elif weatherVariable == 'days':
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "sunrise", "sunset", "daylight_duration", "wind_speed_10m_max", "wind_gusts_10m_max"],
                "timezone": "Europe/Berlin",
                "forecast_days": forecastDays
            }

            responses = openmeteo.weather_api(url, params=params)

            response = responses[0]

            daily = response.Daily()
            daily_weather_code = daily.Variables(0).ValuesAsNumpy()
            daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
            daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
            daily_sunrise = daily.Variables(3).ValuesAsNumpy()
            daily_sunset = daily.Variables(4).ValuesAsNumpy()
            daily_daylight_duration = daily.Variables(5).ValuesAsNumpy()
            daily_wind_speed_10m_max = daily.Variables(6).ValuesAsNumpy()

            daily_data = {"date": pd.date_range(
                start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
                end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
                freq = pd.Timedelta(seconds = daily.Interval()),
                inclusive = "left"
            )}
            daily_data["weather_code"] = daily_weather_code
            daily_data["temperature_2m_max"] = daily_temperature_2m_max
            daily_data["temperature_2m_min"] = daily_temperature_2m_min
            daily_data["sunrise"] = daily_sunrise
            daily_data["sunset"] = daily_sunset
            daily_data["daylight_duration"] = daily_daylight_duration
            daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max

            daily_dataframe = pd.DataFrame(data = daily_data)
            speak(f"Hier die Wettervorhersage für gestern, heute und die nächsten {forecastDays - 2} Tage")
            print(daily_dataframe)

        speak("Möchten Sie weitere Wetterdaten oder möchten Sie das Programm schließen. Sagen sie schließen zum Beenden des Programms.")
        query = takeCommand().lower()

        if 'schließen' in query:
            speak("Haben Sie noch einen schönen Tag!")
            break
        else:
            continue


            


