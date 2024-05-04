import os
import time
from datetime import datetime
from typing import Union

import numpy as np
import torch
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI
from pygame import mixer
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, Pipeline, pipeline

from voice_action_assistant.config import config
from voice_action_assistant.utils import (
    load_numpy_from_audio_file,
    remove_trailing_phrase,
    timer_decorator,
)

mixer.init()

load_dotenv()


def init_client():
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return openai_client


def init_local_model() -> Pipeline:
    start_time = time.time()
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # model_id = "distil-whisper/distil-large-v2"
    # model_id = "distil-whisper/distil-medium.en"
    model_id = "distil-whisper/distil-small.en"

    logger.info(f"Loading model: {model_id} on device: {device}")

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        device_map=device,
    )
    logger.debug(f"Fount model: {model_id}, time: {time.time() - start_time:0.2f} seconds")

    # model.to(device)
    logger.debug(
        f"Model loaded: {model_id} on device: {device} time: {time.time() - start_time:0.2f} seconds"
    )

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        chunk_length_s=15,
        batch_size=16,
        torch_dtype=torch_dtype,
    )

    # # Todo: figure out why so slow on first run
    # logger.debug(f"Testing model on example waveform: {example_waveform()}")
    # test_transcript = pipe(example_waveform())
    # assert isinstance(
    #     test_transcript["text"], str
    # ), "Model failed to transcribe test waveform"

    logger.info(f"Loaded speech to text model in {time.time() - start_time:0.2f} seconds")
    return pipe


class STT:
    def __init__(self, local=True):
        self.local = local
        if self.local:
            self.model = init_local_model()
        else:
            self.client = init_client()

    def transcribe(
        self,
        audio_file: Union[str, np.ndarray],
    ):
        if self.local and isinstance(audio_file, np.ndarray):
            transcript = self.model(inputs=audio_file)
            assert isinstance(transcript, dict), "Failed to transcribe audio"

            transcript_text = transcript.get("text")
        elif isinstance(audio_file, str):
            with open(audio_file, "rb") as f:
                transcript = self.client.audio.transcriptions.create(model="whisper-1", file=f)
                transcript_text = transcript.text
        else:
            raise ValueError("audio_file must be a file path or numpy array")
        assert isinstance(transcript_text, str), "Failed to transcribe audio"

        return transcript_text.strip()


class Transcriber:
    def __init__(self):
        self.stt = STT(local=config.LOCAL)

    @timer_decorator
    def transcribe_audio(self, audio: np.ndarray, pre_audio_file: str = ""):
        if pre_audio_file:
            pre_audio = load_numpy_from_audio_file(pre_audio_file)
            audio = np.concatenate((pre_audio, audio))

        transcript = self.stt.transcribe(
            audio_file=audio,
        )
        logger.debug(f"Raw Transcript: {transcript}")
        return transcript

    def clean_transcript(self, transcript, phrase):
        clean_transcript = remove_trailing_phrase(transcript, phrase)
        logger.debug(f"Clean Transcript: {transcript}")
        return clean_transcript

    def save_transcript(self, transcript):
        with open("output.txt", "a") as f:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n{transcript}\n")
