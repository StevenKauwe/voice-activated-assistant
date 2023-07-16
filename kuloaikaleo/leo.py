import numpy as np
import pyttsx3
from pyttsx3 import speak
import os
import time
from loguru import logger
import sounddevice as sd
import concurrent.futures
import openai
import keyboard
from scipy.io.wavfile import write
from dotenv import load_dotenv
import signal
import threading

load_dotenv()

# Set your OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set the OpenAI model you want to use
model_id = "gpt-3.5-turbo"

# Define the key for starting/stopping recording
record_key = "a"

transcription_prompt = """
You are a helpful medical transcription corrector.
You are helping a doctor transcribe a patient's medical history.
The doctor is dictating the patient's medical history to you.
The audio is transcribed into text.
The text is then sent to you for correction.
You correct the text and send it back to the doctor.
You use context to assume corrections to the written text.
The text is coming from a rudimentary speech-to-text engine.
The engine is not very accurate and makes many mistakes.
You may have to make some pretty big corrections that involve logical leaps based on the sound of the words.
You are very good at this and can make these corrections easily.
"""

user_description_prompt = """
I am a psychiatrist.
I am dictating a patient's medical history.
I need you to correct the transcription of the patient's medical history.
I will now provide the dictation as text from the speech-to-text engine and you will correct it.
When I say "correction", the correction is to the chart should not be included in the patient's medical history.
Similarly, when I say "quote", I want the text to be quoted in the patient's medical history.

Please automatically apply correct formatting and punctuation to the text.
Please mark any corrections you make with  "<old>...</old><correction>...</correction>" in cases where the original text is grossly incorrect, non-sensical or may be medically dangerous.
"""


class AudioRecorder:
    def __init__(self):
        self.recording = None
        self.is_recording = False
        self.fs = 44100  # Sample rate
        self.channels = 1  # Number of audio channels
        self.stream = sd.InputStream(
            samplerate=self.fs, channels=self.channels, callback=self.audio_callback
        )

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.is_recording:
            self.recording.append(indata.copy())

    def start_recording(self):
        self.is_recording = True
        self.recording = []
        self.stream.start()
        logger.info("Recording started...")
        time.sleep(0.5)

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop()
        logger.info("Recording stopped. Processing...")
        # Concatenate the blocks of audio data
        data = np.concatenate(self.recording).flatten()
        # Save the data to .wav file
        write("output.wav", self.fs, data)
        self.process_recording()
        time.sleep(0.5)

    def process_recording(self):
        with open("output.wav", "rb") as f:
            transcript = openai.Audio.transcribe("whisper-1", f)
        logger.info(f"Transcript: {transcript['text']}")
        self.generate_response(transcript["text"])

    def generate_response(self, text):
        response = openai.ChatCompletion.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": transcription_prompt,
                },
                {"role": "user", "content": user_description_prompt},
                {"role": "user", "content": text},
            ],
        )
        response_text = response["choices"][0]["message"]["content"]
        logger.info(f"Response: {response_text}")
        try:
            speaker_thread = threading.Thread(target=speak, args=(response_text,))
            speaker_thread.daemon = True
            speaker_thread.start()
        except Exception as e:
            logger.error(f"Error with text-to-speech engine: {e}")
        logger.info("Response spoken.")


def main():
    os.system("cls" if os.name == "nt" else "clear")  # Clear console
    recorder = AudioRecorder()
    while True:  # Keep the program running
        if keyboard.is_pressed(record_key):  # if key 'a' is pressed
            if not recorder.is_recording:
                recorder.start_recording()
            else:
                recorder.stop_recording()
        if keyboard.is_pressed("esc"):  # if key 'esc' is pressed
            logger.info("Exiting...")
            exit()


if __name__ == "__main__":
    # Handle termination signals
    signal.signal(signal.SIGTERM, lambda signum, frame: exit())
    signal.signal(signal.SIGINT, lambda signum, frame: exit())
    # Run the main function in a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(main)
        future.result()
