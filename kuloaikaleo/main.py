import re
import signal
import sys
import time
from collections import deque
from typing import Tuple

import config
from kaaoao import Transcriber
from leo import AudioRecorder
from loguru import logger
from utils import play_sound

logger.remove()
logger.add(sys.stderr, level="INFO")


class VoiceControlledRecorder:
    """
    A voice-controlled recorder that starts and stops recording based on specific trigger words.
    """

    def __init__(self, start_phrase: str, stop_phrase: str):
        """
        Initialize the voice-controlled recorder with start and stop phrases.

        Parameters
        ----------
        start_phrase : str
            The phrase that triggers the start of the recording.
        stop_phrase : str
            The phrase that triggers the end of the recording.
        """
        self.start_phrase = start_phrase.lower()
        self.stop_phrase = stop_phrase.lower()
        self.recorder = AudioRecorder()
        self.wake_audio_recorder = AudioRecorder("wake phrase recorder", max_seconds=2)
        self.transcriber = Transcriber()
        self.is_recording = False

    def _create_buffers(self, max_length):
        self.buffers = deque(maxlen=max_length)

    def _record_audio(self) -> Tuple[bool, bytes]:
        """
        Record audio until the stop phrase is detected.

        Returns
        -------
        Tuple[bool, bytes]
            A tuple containing a boolean indicating if the stop phrase was detected and the recorded audio bytes.
        """
        self.recorder.start_recording()
        logger.info("Recording started...")
        self.is_recording = True

        while self.is_recording:
            phrase_detected = self._continuous_detection(
                self.stop_phrase, pre_audio_file=config.DICTATION_AUDIO_FILE
            )
            if phrase_detected:
                self.is_recording = False

        audio_data = self.recorder.stop_recording()
        logger.info("Recording stopped.")
        return self.is_recording, audio_data

    def _continuous_detection(
        self,
        phrase: str,
        listening_interval: float = 0.5,
        audio_length: float = 2.0,
        pre_audio_file: str = None,
    ):
        """
        Continuously detect the start phrase and respond by recording until the stop phrase is detected.
        """
        if not self.wake_audio_recorder.is_recording:
            logger.debug("Starting wake recorder...")
            self.wake_audio_recorder.start_recording()

        start_time = time.time()

        while time.time() - start_time < listening_interval:
            time.sleep(0.1)

        array_size = int(audio_length * self.wake_audio_recorder.fs)
        logger.debug(
            f"Array size: {array_size} of possible {len(self.wake_audio_recorder.singal_array)}"
        )
        audio_chunk = self.wake_audio_recorder.singal_array[-array_size:]

        transcription = self.transcriber.transcribe(audio_chunk, pre_audio_file).lower()
        phrase_words = phrase.split()
        pattern = (
            r"\b" + r"\b.*\b".join(re.escape(word) for word in phrase_words) + r"\b"
        )
        match = re.search(pattern, transcription)

        phrase_detected = bool(match)

        if phrase_detected:
            self.wake_audio_recorder.refresh_signal_queue()

        return phrase_detected

    def listen_and_respond(self):
        """
        Listen for the start phrase and respond by recording until the stop phrase is detected.
        """
        logger.info(f"Listening for Start phrase: --> '{config.START_PHRASE}'\n")
        while True:
            phrase_detected = self._continuous_detection(
                self.start_phrase, pre_audio_file=config.DICTATION_AUDIO_FILE
            )
            if phrase_detected and not self.is_recording:
                logger.info(
                    f"Started recording. Stop phrase: --> '{config.STOP_PHRASE}'\n"
                )
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
        start_phrase=config.START_PHRASE, stop_phrase=config.STOP_PHRASE
    )
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
