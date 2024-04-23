import os
import tempfile
import time
from collections import deque

import numpy as np
import sounddevice as sd
from loguru import logger
from pydub import AudioSegment
from scipy.io.wavfile import write

from voice_action_assistant.transcriber import Transcriber
from voice_action_assistant.utils import timer_decorator


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
        if not self.is_recording:
            self.is_recording = True
            self.refresh_signal_queue()
            self.stream.start()
            logger.info(f"Recording started for {self.name}...")

    def stop_recording(self) -> np.ndarray | None:
        if self.is_recording:
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
    def signal_array(self):
        signal = np.concatenate(list(self.signal_queue)).flatten()
        logger.debug(f"Len signal queue: {len(self.signal_queue)} ~= len array: {signal.shape}?")
        return signal

    @timer_decorator
    def process_recording(self) -> np.ndarray:
        logger.debug(f"Data shape: {self.signal_array.shape}")
        return self.signal_array

    @timer_decorator
    def save_recording(self, file_name: str):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        try:
            logger.debug(f"Writing data to temporary wav file: {temp_wav_path}")
            # Write data to the temporary wav file
            write(temp_wav_path, self.fs, self.signal_array)

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


class AudioDetector:
    def __init__(self, recorder: AudioRecorder, transcriber: Transcriber):
        self.recorder = recorder
        self.transcriber = transcriber

    def detect_phrases(
        self,
        listening_interval: float,
        pre_audio_file: str = "",
    ):
        if not self.recorder.is_recording:
            logger.debug("Starting wake recorder...")
            self.recorder.start_recording()

        start_time = time.time()
        while time.time() - start_time < listening_interval:
            time.sleep(0.1)

        logger.debug(f"max seconds: {self.recorder.max_seconds}, fs: {self.recorder.fs}")
        array_size = int(self.recorder.max_seconds * self.recorder.fs)
        logger.debug(f"Array size: {array_size} of possible {len(self.recorder.signal_array)}")
        audio_chunk = self.recorder.signal_array[-array_size:]
        transcription = self.transcriber.transcribe_audio(audio_chunk, pre_audio_file).lower()
        return transcription
