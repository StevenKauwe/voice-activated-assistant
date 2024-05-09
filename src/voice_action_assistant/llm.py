import os
import time
from threading import Thread
from typing import Iterable

import torch
from loguru import logger
from openai import OpenAI
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice, ChoiceDelta
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from voice_action_assistant.config import config, LanguageModelType


class LocalCompletions:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        self.terminators = [
            self.tokenizer.eos_token_id,
            self.tokenizer.convert_tokens_to_ids("<|eot_id|>"),
        ]

    def stream_as_chat_chunks(self, iterable: Iterable[str]) -> Iterable[ChatCompletionChunk]:
        for i, chunk in enumerate(iterable):
            choice_delta = ChoiceDelta(content=chunk)
            choice = Choice(delta=choice_delta, index=i)
            yield ChatCompletionChunk(
                id="local",
                choices=[choice],
                model=self.model_id,
                created=int(time.time()),
                object="chat.completion.chunk",
            )

    def create(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        stream: bool,
    ) -> Iterable[ChatCompletionChunk]:
        if model != self.model_id:
            logger.debug(f"Model {model} does not match initialized model {self.model_id}.")
        if not stream:
            raise ValueError("Stream must be True for local completions")

        streamer = TextIteratorStreamer(self.tokenizer)
        input_ids = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(self.model.device)
        generation_kwargs = {
            "input_ids": input_ids,
            "max_new_tokens": max_tokens,
            "eos_token_id": self.terminators,
            "do_sample": True,
            "temperature": temperature,
            "top_p": 0.9,
            "streamer": streamer,
        }
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        completions = self.stream_as_chat_chunks(streamer)
        return completions


class LocalChat:
    def __init__(self, model_id: str):
        self.completions = LocalCompletions(model_id)


class LocalLanguageModelClient:
    def __init__(self, model_id: str):
        self.chat = LocalChat(model_id)


def init_llm_client() -> OpenAI | LocalLanguageModelClient:
    model_type = config.llm_config.llm_type
    match model_type:
        case LanguageModelType.HUGGINGFACE:
            return LocalLanguageModelClient(config.llm_config.llm_id)
        case LanguageModelType.OPENAI:
            return OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        case LanguageModelType.OLLAMA:
            return OpenAI(api_key="ollama", base_url=config.llm_config.server_url)
        case _:
            raise ValueError(f"Unsupported model type: {model_type}")


class TextGenerator:
    def __init__(self):
        self.client = init_llm_client()

    def generate_text(
        self, messages, max_tokens: int, temperature: float
    ) -> Iterable[ChatCompletionChunk]:
        completions = self.client.chat.completions.create(
            model=config.llm_config.llm_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        return completions
