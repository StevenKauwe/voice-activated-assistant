from pathlib import Path

import config
import pyautogui
import whisper
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from loguru import logger
from openai import OpenAI
from pydub import AudioSegment
from pygame import mixer

mixer.init()

load_dotenv()


def example_waveform():
    import math

    import torch

    # Parameters for the waveform
    sample_rate = 16000  # Sampling rate in Hz
    duration = 1.0  # Duration in seconds
    frequency = 440.0  # Frequency of the sine wave in Hz (A4 note)

    # Generate time values
    t = torch.linspace(0, duration, int(sample_rate * duration))

    # Generate the sine wave
    waveform = torch.sin(2 * math.pi * frequency * t)
    return waveform


def init_client():
    openai_client = OpenAI(
        api_key="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"
    )
    return openai_client


def init_local_model():
    distil_model = hf_hub_download(
        repo_id="distil-whisper/distil-medium.en", filename="original-model.bin"
    )
    model = whisper.load_model(distil_model, device="cuda")

    _ = model.transcribe(example_waveform())
    return model


def speed_up_audio(filename, speed=2):
    if speed == 1:
        return
    sound = AudioSegment.from_file(filename)
    sound_with_altered_speed = sound.speedup(playback_speed=speed)
    sound_with_altered_speed.export(filename, format="mp3")


class STT:
    def __init__(self, local=True):
        self.local = local
        if self.local:
            self.model = init_local_model()
        else:
            self.client = init_client()

    def transcribe(
        self,
        audio_file: str,
    ):
        if self.local:
            transcript = self.model.transcribe(
                audio=audio_file,
                language=config.LANGUAGE,
                verbose=config.ModelOptions.verbose,
                initial_prompt=config.ModelOptions.initial_prompt,
                condition_on_previous_text=config.ModelOptions.condition_on_previous_text,
                temperature=config.ModelOptions.temperature,
            )
            transcript_text = transcript["text"]
        else:
            with open(audio_file, "rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", file=f
                )
                transcript_text = transcript.text

        return transcript_text.strip()


class Transcriber:
    def __init__(self):
        self.stt = STT(local=config.LOCAL)
        logger.info(f"Hold {config.ACTIVATION_KEYS} and speak for STT")

    def transcribe_and_respond(self, chunks):
        for i, chunk in enumerate(chunks):
            chunk.export(f"output_{i}.mp3", format="mp3")
            self._transcribe_and_respond(f"output_{i}.mp3")

    def _transcribe_and_respond(self, file_name):
        transcript_text = self.stt.transcribe(
            audio_file=file_name,
        )
        logger.info(f"Transcript: {transcript_text}")
        self._generate_response(transcript_text)

    def _generate_response(self, text):
        if config.USE_SPEECH_TO_TEXT:
            pyautogui.write(text, interval=0.005)

        if config.USE_GPT_POST_PROCESSING:
            response = openai_client.chat.completions.create(
                model=config.MODEL_ID,
                messages=[
                    {
                        "role": "system",
                        "content": config.TRANSCRIPTION_PREPROMPT,
                    },
                    {"role": "user", "content": f"Trascription of audio: '{text}'"},
                ],
                max_tokens=1000,
                temperature=0.1,
            )
            response_text = response.choices[0].message.content
            logger.info(f"Response: {response_text}")
        else:
            response_text = text

        if config.USE_SPOKEN_RESPONSE:
            self._speak_response(response_text)

    def _speak_response(self, response_text):
        try:
            speech_file_path = Path(__file__).parent / "response.mp3"
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=response_text,
            )

            response.stream_to_file(speech_file_path)
            speed_up_audio("response.mp3", speed=1.5)
            mixer.music.load("response.mp3")
            mixer.music.play()
            import time

            while mixer.music.get_busy():
                time.sleep(0.1)

            # Unload the current music
            mixer.music.unload()
        except Exception as e:
            logger.error(f"Error with text-to-speech engine: {e}")
        logger.info("Response spoken.")
