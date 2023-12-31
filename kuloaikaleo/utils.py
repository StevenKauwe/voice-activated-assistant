import time

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


def speed_up_audio(filename, speed=2):
    if speed == 1:
        return
    sound: AudioSegment = AudioSegment.from_file(filename)
    sound_with_altered_speed = sound.speedup(playback_speed=speed)
    sound_with_altered_speed.export(filename, format="mp3")
