import math
import time
from datetime import datetime
from pathlib import Path

import config
import pyautogui
import torch
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI
from pydub import AudioSegment
from pygame import mixer
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

mixer.init()

load_dotenv()


def example_waveform():
    # Parameters for the waveform
    sample_rate = 16000  # Sampling rate in Hz
    duration = 1.0  # Duration in seconds
    frequency = 440.0  # Frequency of the sine wave in Hz (A4 note)

    # Generate time values
    t = torch.linspace(0, duration, int(sample_rate * duration))

    # Generate the sine wave
    waveform = torch.sin(2 * math.pi * frequency * t).numpy()
    return waveform


def init_client():
    openai_client = OpenAI(
        api_key="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"
    )
    return openai_client


def init_local_model():
    start_time = time.time()
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "distil-whisper/distil-large-v2"
    # model_id = "distil-whisper/distil-medium.en"

    logger.info(f"Loading model: {model_id} on device: {device}")

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        device_map="cuda",
    )
    logger.debug(
        f"Fount model: {model_id}, time: {time.time() - start_time:0.2f} seconds"
    )

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
    logger.debug(f"Testing model on example waveform: {example_waveform()}")
    test_transcript = pipe(example_waveform())
    assert isinstance(
        test_transcript["text"], str
    ), "Model failed to transcribe test waveform"

    logger.info(
        f"Loaded speech to text model in {time.time() - start_time:0.2f} seconds"
    )
    return pipe


def speed_up_audio(filename, speed=2):
    if speed == 1:
        return
    sound: AudioSegment = AudioSegment.from_file(filename)
    sound_with_altered_speed = sound.speedup(playback_speed=speed)
    sound_with_altered_speed.export(filename, format="mp3")


class STT:
    def __init__(self, local=True):
        self.local = local
        if self.local:
            self.model = init_local_model()
        else:
            self.client = init_client()

    def transcribe(
        self,
        audio_file: str,
    ):
        if self.local:
            transcript = self.model(inputs=audio_file)
            transcript_text = transcript["text"]
        else:
            with open(audio_file, "rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", file=f
                )
                transcript_text = transcript.text

        return transcript_text.strip()


class Transcriber:
    def __init__(self):
        self.stt = STT(local=config.LOCAL)

    def transcribe_and_respond(self, chunks: list[AudioSegment]):
        for i, chunk in enumerate(chunks):
            chunk.export(f"output_{i}.mp3", format="mp3")
            self._transcribe_and_respond(f"output_{i}.mp3")

    def _transcribe_and_respond(self, file_name: str):
        transcript_text = self.stt.transcribe(
            audio_file=file_name,
        )
        logger.info(f"Transcript: {transcript_text}")
        self._generate_response(transcript_text)

    def _generate_response(self, text: str):
        with open("output.txt", "a") as f:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n{text}\n")

        if config.USE_SPEECH_TO_TEXT:
            pyautogui.write(text, interval=0.0025)

        if config.USE_GPT_POST_PROCESSING:
            openai_client = init_client()
            response = openai_client.chat.completions.create(
                model=config.MODEL_ID,
                messages=[
                    {
                        "role": "system",
                        "content": config.TRANSCRIPTION_PREPROMPT,
                    },
                    {"role": "user", "content": f"Trascription of audio: '{text}'"},
                ],
                max_tokens=1000,
                temperature=0.1,
            )
            response_text = response.choices[0].message.content
            logger.info(f"Response: {response_text}")

            with open("output.txt", "a") as f:
                f.write(f"\nGPT output:{response_text}\n")

        else:
            response_text = text

        if config.USE_SPOKEN_RESPONSE:
            self._speak_response(response_text)

    def _speak_response(self, response_text: str):
        try:
            openai_client = init_client()
            speech_file_path = Path(__file__).parent / "response.mp3"
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=response_text,
            )

            response.stream_to_file(speech_file_path)
            speed_up_audio("response.mp3", speed=1.5)
            mixer.music.load("response.mp3")
            mixer.music.play()
            import time

            while mixer.music.get_busy():
                time.sleep(0.1)

            # Unload the current music
            mixer.music.unload()
        except Exception as e:
            logger.error(f"Error with text-to-speech engine: {e}")
        logger.info("Response spoken.")
