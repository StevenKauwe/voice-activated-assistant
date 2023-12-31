import os
import tempfile

import numpy as np
import sounddevice as sd
from loguru import logger
from pydub import AudioSegment
from scipy.io.wavfile import write
from utils import timer_decorator


class AudioRecorder:
    def __init__(self):
        self.recording = None
        self.is_recording = False
        self.fs = 16000  # Sample rate 16000 for whisper model!
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

    def stop_recording(self) -> AudioSegment:
        self.is_recording = False
        self.stream.stop()
        logger.info("Recording stopped. Processing...")
        return self.process_recording()

    @timer_decorator
    def process_recording(self) -> AudioSegment:
        data = np.concatenate(self.recording).flatten()
        logger.debug(f"Data shape: {data.shape}")
        return data

    @timer_decorator
    def save_recording(self, file_name: str):
        data = np.concatenate(self.recording).flatten()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        try:
            logger.debug(f"Writing data to temporary wav file: {temp_wav_path}")
            # Write data to the temporary wav file
            write(temp_wav_path, self.fs, data)

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
