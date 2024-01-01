import os
import tempfile
import time
from collections import deque

import numpy as np
import sounddevice as sd
from loguru import logger
from pydub import AudioSegment
from scipy.io.wavfile import write
from utils import timer_decorator


class AudioRecorder:
    def __init__(self, name="AudioRecorder", max_seconds=600):
        self.name = name
        self.max_seconds = max_seconds
        self.is_recording = False

        self.fs = 16000  # Sample rate 16000 for whisper model!
        self.channels = 1  # Number of audio channels
        self.stream = sd.InputStream(
            samplerate=self.fs, channels=self.channels, callback=self.audio_callback
        )

    def refresh_signal_queue(self):
        array_size = self.max_seconds * self.fs
        logger.debug(f"Array size: {array_size}")
        self.signal_queue = deque(maxlen=array_size)

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.is_recording:
            self.signal_queue.extend(indata.copy())

    def start_recording(self):
        self.is_recording = True
        self.refresh_signal_queue()
        self.stream.start()
        logger.info(f"Recording started for {self.name}...")

    def stop_recording(self) -> np.ndarray:
        self.is_recording = False
        self.stream.stop()
        logger.info("Recording stopped. Processing...")
        return self.process_recording()

    def record_chunk(self, chunk_length=15):
        """Record a single chunk of audio."""
        self.start_recording()
        start_time = time.time()

        while time.time() - start_time < chunk_length:
            time.sleep(0.1)

        return self.stop_recording()

    @property
    def singal_array(self):
        signal_array = np.concatenate(list(self.signal_queue)).flatten()
        logger.debug(
            f"Length of signal queue: {len(self.signal_queue)} array: {signal_array.shape}"
        )
        return signal_array

    @timer_decorator
    def process_recording(self) -> np.ndarray:
        logger.debug(f"Data shape: {self.singal_array.shape}")
        return self.singal_array

    @timer_decorator
    def save_recording(self, file_name: str):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        try:
            logger.debug(f"Writing data to temporary wav file: {temp_wav_path}")
            # Write data to the temporary wav file
            write(temp_wav_path, self.fs, self.singal_array)

            logger.debug("Loading temporary wav file into an AudioSegment")
            # Load the temporary wav file into an AudioSegment
            audio: AudioSegment = AudioSegment.from_wav(temp_wav_path)

            logger.debug(f"Exporting AudioSegment as an mp3: {file_name}")
            # Export the AudioSegment as an mp3
            audio.export(file_name, format="mp3")
        finally:
            logger.debug(f"Deleting temporary file: {temp_wav_path}")
            # Delete the temporary file
            os.remove(temp_wav_path)
