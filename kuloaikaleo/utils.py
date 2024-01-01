import math
import time

import numpy as np
import pygame
import torch
from loguru import logger
from pydub import AudioSegment


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
