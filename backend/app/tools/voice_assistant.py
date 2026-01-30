# voice_assistant.py - NEW FILE: Voice assistant script
import speech_recognition as sr
import pyttsx3
import requests  # For calling backend API
import os

BACKEND_API_URL = os.getenv(
    "BACKEND_PUBLIC_URL", "http://127.0.0.1:8000"
)

# Initialize TTS engine
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        query = recognizer.recognize_google(audio)
        print(f"You said: {query}")
        return query
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        speak("Sorry, I didn't catch that.")
        return ""
    except sr.RequestError:
        print("Speech service down.")
        speak("Speech service is down.")
        return ""

# Function to get AI response from backend (POST /chat/send)
def get_ai_response(query):
    response = requests.post(
        f"{BACKEND_API_URL}/chat/send",
        json={"message": query}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("reply", "No response")
    else:
        return "Error connecting to AI backend."

def run_voice_assistant():
    speak("Hello! I'm AI Model 1.0. How can I help?")
    while True:
        command = listen()
        if "exit" in command.lower() or "quit" in command.lower():
            speak("Goodbye!")
            break
        if command:
            response = get_ai_response(command)
            print(f"AI: {response}")
            speak(response)

if __name__ == "__main__":
    run_voice_assistant()