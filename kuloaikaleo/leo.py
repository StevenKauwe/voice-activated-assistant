import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from pydub import AudioSegment
from loguru import logger


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

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop()
        logger.info("Recording stopped. Processing...")
        return self.process_recording()

    def process_recording(self):
        data = np.concatenate(self.recording).flatten()
        write("output.wav", self.fs, data)
        audio = AudioSegment.from_wav("output.wav")
        audio.export("output.mp3", format="mp3")
        chunk_length = 10 * 60 * 1000  # 10 minutes in milliseconds
        chunks = [
            audio[i : i + chunk_length] for i in range(0, len(audio), chunk_length)
        ]
        return chunks
