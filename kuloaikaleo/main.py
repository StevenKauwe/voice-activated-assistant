import keyboard
import signal
import concurrent.futures
from loguru import logger
from leo import AudioRecorder
from kaaoao import Transcriber

import time


def main():
    recorder = AudioRecorder()
    transcriber = Transcriber()
    while True:
        if keyboard.is_pressed("a"):
            if not recorder.is_recording:
                recorder.start_recording()
                time.sleep(0.5)  # Add a small delay
            else:
                chunks = recorder.stop_recording()
                transcriber.transcribe_and_respond(chunks)
        if keyboard.is_pressed("esc"):
            logger.info("Exiting...")
            exit()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda signum, frame: exit())
    signal.signal(signal.SIGINT, lambda signum, frame: exit())
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(main)
        future.result()
