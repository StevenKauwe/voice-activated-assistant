import math
import os
import re
import sys
import time
from collections import deque
from enum import Enum
from pathlib import Path
from textwrap import dedent
from threading import Lock

import numpy as np
import pyautogui
import pygame
import pyperclip
import torch
from loguru import logger
from openai import OpenAI
from pydub import AudioSegment
from pygame import mixer

from voice_action_assistant.config import config


def create_regex_pattern(phrase):
    # Split the phrase into words
    words = phrase.split()

    # Create regex capture groups for each word
    # Join them allowing for non-word characters in between
    regex_pattern = r"[^\w]*".join(map(re.escape, words))

    # Add an assertion to match at the end of the string
    regex_pattern += r"[^\w]*$"

    return regex_pattern


def transcript_contains_phrase(transcript, action_phrase):
    # Generate the regex pattern from the stop phrase
    pattern = create_regex_pattern(action_phrase)

    # Use regex to search for the stop phrase
    match = re.search(pattern, transcript, flags=re.IGNORECASE)
    logger.debug(f"{transcript} contains {action_phrase}: {match is not None}")
    return match is not None


def remove_trailing_phrase(transcript, phrase):
    # Generate the regex pattern from the stop phrase
    pattern = create_regex_pattern(phrase)

    # Use regex to substitute the stop phrase with an empty string
    cleaned_transcript = re.sub(pattern, "", transcript, flags=re.IGNORECASE).strip()

    return cleaned_transcript


def load_numpy_from_audio_file(audio_file: str, target_rate=16000):
    """
    Converts an audio file to a NumPy array and resamples to the target rate.

    Args:
    audio_file (str): The audio file to convert.
    target_rate (int): The target sampling rate in Hz.

    Returns:
    numpy.ndarray: A normalized and resampled NumPy array of the audio.
    """

    audio_segment = AudioSegment.from_file(audio_file)

    # Resample to the target sampling rate
    if audio_segment.frame_rate != target_rate:
        audio_segment = audio_segment.set_frame_rate(target_rate)

    # Ensure the audio is mono
    if audio_segment.channels > 1:
        audio_segment = audio_segment.set_channels(1)

    # Convert to NumPy array
    samples = np.array(audio_segment.get_array_of_samples())

    # Normalize and convert to float32
    samples = samples.astype(np.float32) / (2**15)

    return samples


def play_sound(sound_file):
    pygame.mixer.init()
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # Wait for audio to finish playing
        pygame.time.Clock().tick(10)


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"The method {func.__name__} took {elapsed_time} seconds to complete.")
        return result

    return wrapper


def speed_up_audio(filename: str, speed=2):
    if speed == 1:
        return
    sound: AudioSegment = AudioSegment.from_file(filename)
    sound_with_altered_speed = sound.speedup(playback_speed=speed)
    sound_with_altered_speed.export(filename, format="mp3")


def example_waveform():
    # Parameters for the waveform
    sample_rate = 16000  # Sampling rate in Hz
    duration = 1.0  # Duration in seconds
    frequency = 440.0  # Frequency of the sine wave in Hz (A4 note)

    # Generate time values
    t = torch.linspace(0, duration, int(sample_rate * duration))

    # Generate the sine wave
    waveform = torch.sin(2 * math.pi * frequency * t).numpy()
    return waveform


def load_text_file(file_path):
    with open(file_path, "r") as file:
        text = file.read()
    return text


def init_client():
    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return openai_client


def gpt_post_process_transcript(transcript: str):
    system_prompt = dedent(
        f"""\
        context from user:
        {load_text_file("prompt.md")}

        {pyperclip.paste()}
        """
    )  # config.TRANSCRIPTION_PREPROMPT

    openai_client = init_client()
    completion = openai_client.chat.completions.create(
        model=config.MODEL_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{transcript}"},
        ],
        max_tokens=1024,
        temperature=0.1,
        stream=True,
    )

    response_text = ""

    with open("output.txt", "a") as f:
        f.write("\nGPT output:\n")
    for chunk in completion:
        str_delta = chunk.choices[0].delta.content
        if str_delta:
            response_text += str_delta
            with open("output.txt", "a") as f:
                f.write(f"{response_text}")

    return response_text


def paste_at_cursor():
    """
    Paste the text at the cursor position.
    This requires system permissions to work.
    This is also buggy and may not work on all systems.
    Don't enable this unless you know are certain you want to use it.

    Alternative would be "write at cursor" which would be more reliable.
    This would still require system permissions.
    """
    if config.PASTE_AT_CURSOR:
        pyautogui.keyDown("command")
        pyautogui.press("v")
        pyautogui.keyUp("command")


def copy_to_clipboard(text: str):
    if config.COPY_TO_CLIPBOARD:
        pyperclip.copy(text)
        logger.info("Text copied to clipboard.")


def tts_transcript(transcript: str):
    try:
        openai_client = init_client()
        speech_file_path = Path(__file__).parent / "response.mp3"
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=transcript,
        )

        response.stream_to_file(speech_file_path)
        speed_up_audio("response.mp3", speed=config.AUDIO_SPEED)
        mixer.music.load("response.mp3")
        mixer.music.play()
        import time

        while mixer.music.get_busy():
            time.sleep(0.1)

        # Unload the current music
        mixer.music.unload()
    except Exception as e:
        logger.exception(f"Error with text-to-speech engine: {e}")
    logger.info("Response spoken.")


def stt_audio_file(file_name: str):
    openai_client = init_client()
    with open(file_name, "rb") as f:
        transcript = openai_client.audio.transcriptions.create(model="whisper-1", file=f)
    transcript_text = transcript.text
    return transcript_text


class ColorEnum(str, Enum):
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


class StreamColorPrinter:
    def __init__(self, start_trigger: str, end_trigger: str, buffer_size: int = 100):
        self.start_trigger = start_trigger
        self.end_trigger = end_trigger
        self.buffer_size = buffer_size
        self.buffer = deque(maxlen=buffer_size)
        self.print_lock = Lock()

        self.base_color = ColorEnum.MAGENTA.value
        self.code_block_color = ColorEnum.CYAN.value
        self.current_color = self.base_color

    def _update_color(self, word: str):
        # Update the buffer and check for triggers
        self.buffer.append(word)
        buffer_content = "".join(self.buffer)

        if self.start_trigger in buffer_content and self.current_color == self.base_color:
            self.current_color = self.code_block_color
        elif self.end_trigger in buffer_content and self.current_color == self.code_block_color:
            self.current_color = self.base_color
        else:
            return
        self.buffer.clear()

    def print(self, word: str):
        with self.print_lock:
            self._update_color(word)
            sys.stdout.write(f"{self.current_color}{word}{ColorEnum.RESET.value}")
            sys.stdout.flush()


python_printer = StreamColorPrinter(start_trigger="```", end_trigger="```")
