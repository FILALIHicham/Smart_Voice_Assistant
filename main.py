from datetime import datetime
from datetime import date
from playsound import playsound
import speech_recognition as sr
import pyttsx3
import webbrowser
import wikipedia
import wolframalpha
import configparser
import openai
import requests
import json
import pywhatkit
import sys
import os
import threading
from tkinter import *
from PIL import ImageTk, Image

# config.ini file to keep the API keys secure
config = configparser.ConfigParser()
config.read('config.ini')

# sound effects
on = "On.mp3"
off = "Off.mp3"

# Speech enginge initialisation
engine = pyttsx3.init()
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)
assistantName = "max"
activationword = "hey "+ assistantName #single word

# Browser configuration
# Set path for chrome
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))

# OpenAI configuration
openai.api_key = config['API']['openai']

# openweather configuration
openweather_key = config['API']['openweather']

# Wolfram Alpha client
appId = config['API']['wolfram']
wolframClient = wolframalpha.Client(appId)


def update(label,im):
    label.config(image=im)

# weather function using openweather API
def weather(city):
    openweatherURL = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=imperial&APPID={openweather_key}"
    weather_data = requests.get(openweatherURL)
    if weather_data.json()['cod'] == '404':
        return None
    else:
        weather = weather_data.json()['weather'][0]['main']
        temp = weather_data.json()['main']['temp']
        tempInC = (temp - 32) * 5/9
        return weather,tempInC

# GPT-3 function using openAI API
def ask_GPT(prompt):
    res = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100
    )
    return res["choices"][0]["text"]

# Wikipedia search function using wikipedia API
def search_wikipedia(query = ''):
    searchResults = wikipedia.search(query)
    if not searchResults:
        print("No wikipedia result")
        return 'No result received'
    try:
        wikiPage = wikipedia.page(searchResults[0])
    except wikipedia.DisambiguationError as error:
        wikiPage = wikipedia.page(error.options[0])
    #print(wikiPage.title)
    wikiSummary = str(wikiPage.summary)
    return wikiSummary

# Using zenquotes API to get quotes
def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -" + json_data[0]['a']
  return(quote)

# Function to get the first element of a list or the value of a dictionary
def listOrDict(var):
    if isinstance(var, list):
        return var[0]['plaintext']
    else:
        return var['plaintext']

# Wolfram Alpha search function using wolframalpha API
def search_wolframAlpha(query = ''):
    response = wolframClient.query(query)

    if response["@success"] == "false":
        return "Could not calculate"

    # Query resolved
    else:
        result = ''
        # Question
        pod0 = response['pod'][0]

        pod1 = response['pod'][1]
        # May contain the answer, has the highest confidence value
        # if it's primary, or has the title of result or definition, then it's the official result
        if (('result') in pod1['@title'].lower()) or (pod1.get('@primary', 'false') == 'true') or ('definition' in pod1['@title'].lower()):
            # Get the result
            result = listOrDict(pod1['subpod'])
            # Remove bracketed section
            return result.split('(')[0]
        else:
            # Get the interpretation from pod0
            question = listOrDict(pod0['subpod'])
            # Remove bracketed section
            question = question.split('(')[0]
            # Could search wiki instead here? 
            return question

# Function to make the assistant speak
def speak(text, rate = 150):
    engine.setProperty('rate', rate)
    engine.say(text)
    engine.runAndWait()

# Function to make the assistant parse the commands
def parseCommand():
    global close
    listener = sr.Recognizer()
    #print("Listening for a command")

    with sr.Microphone() as source:
        try:
            listener.adjust_for_ambient_noise(source, duration = 0.2)
            input_speech = listener.listen(source,timeout=5)
            old_stdout = sys.stdout # backup current stdout
            sys.stdout = open(os.devnull, "w") # Preventing the following function from printing
            query = listener.recognize_google(input_speech, language="en-US")
            sys.stdout = old_stdout # reset old stdout
            #print(query)
            if activationword in query.lower() and not close:
                update(robot,img2)
                playsound(on)
                while not close:
                    #print("Listening for a command")
                    input_speech = listener.listen(source,timeout=5)
                    try:
                        #print("Recognizing speech...")

                        old_stdout = sys.stdout # backup current stdout
                        sys.stdout = open(os.devnull, "w") # Preventing the following function from printing
                        query = listener.recognize_google(input_speech, language="en-US")
                        sys.stdout = old_stdout # reset old stdout
                        # print(f"The input speech was: {query}")
                        return query
                    except Exception as exception:
                        speak("Can you repeat please?")
        except Exception as exception:
            # speak("Can you repeat please?")
            print(exception)                
            return None

# Function to run the assistant
def runAssistant():
    global close
    while not close:
        query = parseCommand()
        if query == None:
            continue
        else:
            query = query.lower().split()
            # List commands
            if query[0] == 'say':
                if 'hello' in query:
                    speak("Greetings everyone!.")
                else:
                    query.pop(0) # Remove say
                    speech = ' '.join(query)
                    speak(speech)
            elif  "your name" in ' '.join(query):
                speak(f"My name is {assistantName}")

            elif "date" in ' '.join(query):
                speak(f"Today date is: {date.today()}")

            elif "time" in ' '.join(query):
                time = datetime.today().strftime("%I:%M %p")
                speak(f"it's: {time}")
            # Navigation
            elif query[0] == "open":
                query = ' '.join(query[1:])
                speak(f"Opening {query}")
                webbrowser.get('chrome').open_new(query)

            # Wikipedia
            elif query[0] == 'wikipedia':
                query = ' '.join(query[1:])
                speak('Querying Wikipedia, The free Encyclopedia')
                speak(search_wikipedia(query))

            # Openweather
            elif 'weather' in query:
                city = query[-1]
                result = weather(city)
                if result == None:
                    speak("No city found!")
                else:
                    speak(f"The weather in {city} is: {result[0]}, and the temperature is: {result[1]:.2f}°C")

            # Zenquotes
            elif 'quote' in query:
                speak(get_quote())

            # Play songs on youtube
            elif query[0] == 'play':
                query.pop(0) # Remove play
                query = ' '.join(query)
                speak(f"Playing {query}")
                pywhatkit.playonyt(query)

            # Wolfram ALpha
            elif query[0] == "calculate":
                query = ' '.join(query[1:])
                speak("Calculating...")
                try:
                    result = search_wolframAlpha(query)
                    speak(f'The answer is: {result}')
                except:
                    speak("Unable to calculate.")


            elif 'stop' in query:
                speak('Goodbye')
                playsound(off)
                update(robot,img)
                close = True
                win.quit()
                break

            else:
                prompt = ' '.join(query)
                try:
                    speak(ask_GPT(prompt))
                except:
                    speak("Something is wrong with GPT, Please check your API key and try again later!")
        update(robot,img)
        playsound(off)

# Main loop
if __name__ == '__main__':
    # GUI
    close = False
    win = Tk()
    win.iconbitmap("icon.ico")
    win.geometry("200x250")
    win.resizable(False,False)
    imageOn = Image.open("On.png")
    imageOff = Image.open("Off.png")
    imageOn_resized = imageOn.resize((200, 200))
    imageOff_resized = imageOff.resize((200, 200))
    img2 = ImageTk.PhotoImage(imageOn_resized)
    img = ImageTk.PhotoImage(imageOff_resized)
    robot = Label(win, image = img)
    robot.pack()
    label = Label(win, text=f"Say: {activationword}", font=("Arial",15))
    label.pack()
    
    # Start the assistant in a new thread
    threading.Thread(target=runAssistant).start()

    win.mainloop()
    close = True