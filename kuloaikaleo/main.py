import math
import signal
from collections import deque
from typing import Tuple

import config
import numpy as np
from kaaoao import Transcriber
from leo import AudioRecorder
from loguru import logger
from utils import play_sound


class VoiceControlledRecorder:
    """
    A voice-controlled recorder that starts and stops recording based on specific trigger words.
    """

    def __init__(self, start_word: str, stop_word: str):
        """
        Initialize the voice-controlled recorder with start and stop words.

        Parameters
        ----------
        start_word : str
            The word that triggers the start of the recording.
        stop_word : str
            The word that triggers the end of the recording.
        """
        logger.info("Initializing voice-controlled recorder...")
        self.start_word = start_word.lower()
        self.stop_word = stop_word.lower()
        self.recorder = AudioRecorder()
        self.wake_audio_recorder = AudioRecorder("wake word recorder")
        self.transcriber = Transcriber()
        self.is_recording = False
        self.buffers = deque()

    def _cleanup_buffers(self, max_length):
        """
        Clean up the buffers to prevent memory leak.
        """
        # Keep only the last 4 chunks in the buffer
        while len(self.buffers) > max_length:
            self.buffers.popleft()

    def _record_audio(self) -> Tuple[bool, bytes]:
        """
        Record audio until the stop word is detected.

        Returns
        -------
        Tuple[bool, bytes]
            A tuple containing a boolean indicating if the stop word was detected and the recorded audio bytes.
        """
        self.recorder.start_recording()
        logger.info("Recording started...")
        self.is_recording = True

        while self.is_recording:
            word_detected = self._continuous_detection(
                self.stop_word, pre_audio_file=config.DICTATION_AUDIO_FILE
            )
            if word_detected:
                self.is_recording = False

        audio_data = self.recorder.stop_recording()
        logger.info("Recording stopped.")
        return self.is_recording, audio_data

    def _continuous_detection(
        self,
        word: str,
        listening_interval: float = 0.5,
        audio_length: float = 1.5,
        pre_audio_file: str = None,
    ):
        """
        Continuously detect the start word and respond by recording until the stop word is detected.
        """
        audio_chunk = self.wake_audio_recorder.record_chunk(listening_interval)
        self.buffers.append(audio_chunk)  # Add the new chunk to the buffer

        # Concatenate the buffered audio chunks
        audio_chunk = np.concatenate(list(self.buffers))
        max_length = math.ceil(audio_length / listening_interval)
        self._cleanup_buffers(max_length)

        transcription = self.transcriber.transcribe(audio_chunk, pre_audio_file).lower()
        word_detected = word in transcription

        if word_detected:
            self.buffers = deque()  # Reset the buffer on detection

        return word_detected

    def listen_and_respond(self):
        """
        Listen for the start word and respond by recording until the stop word is detected.
        """

        while True:
            word_detected = self._continuous_detection(
                self.start_word, pre_audio_file=config.DICTATION_AUDIO_FILE
            )
            if word_detected and not self.is_recording:
                play_sound("sound_start.wav")
                _, audio_data = self._record_audio()
                play_sound("sound_end.wav")
                self.transcriber.transcribe_and_respond(audio_data)
                self.recorder.save_recording("output.mp3")


def main():
    """
    Main function to run the voice-controlled recorder.
    """
    voice_controlled_recorder = VoiceControlledRecorder(
        start_word=config.START_WORD, stop_word=config.STOP_WORD
    )
    logger.info("Voice-controlled recorder initialized.")
    voice_controlled_recorder.listen_and_respond()


def run():
    """
    Run the main function with proper signal handling.
    """
    logger.info("Starting voice-controlled recorder...")
    signal.signal(signal.SIGTERM, lambda signum, frame: exit())
    signal.signal(signal.SIGINT, lambda signum, frame: exit())
    main()


if __name__ == "__main__":
    run()
