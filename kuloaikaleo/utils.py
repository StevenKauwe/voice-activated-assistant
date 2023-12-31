import math
import time

import torch
from loguru import logger
from pydub import AudioSegment


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(
            f"The method {func.__name__} took {elapsed_time} seconds to complete."
        )
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
