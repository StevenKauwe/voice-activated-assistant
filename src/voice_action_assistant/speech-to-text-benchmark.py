from time import time

from loguru import logger

from voice_action_assistant.transcriber import STT

stt = STT(local=True)


times = []
for i in range(10):
    start_time = time()
    stt.transcribe("output.mp3")
    transcribed_time = time() - start_time
    logger.debug(f"transcribed in {transcribed_time:0.2f} seconds")
    times.append(transcribed_time)

logger.info(f"average time: {sum(times) / len(times):0.2f} seconds")
