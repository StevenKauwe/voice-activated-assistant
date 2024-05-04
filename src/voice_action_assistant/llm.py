import os
from threading import Thread
from typing import Iterable

import torch
from loguru import logger
from openai import OpenAI, Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from voice_action_assistant.config import config


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

    def stream_as_chat_chunks(self, iterable: Iterable[str]) -> Stream[ChatCompletionChunk]:
        for i, chunk in enumerate(iterable):
            choice = Choice(delta=chunk, index=i)
            yield ChatCompletionChunk(id="local", choices=[chunk], model=self.model_id, ]))

    def create(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        stream: bool,
    ) -> Stream[ChatCompletionChunk]:
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


def init_local_llm() -> LocalLanguageModelClient:
    """If the model is set to an OpenAI model, default to the Meta-Llama 3.8B Instruct model.
    Otherwise, attempt to use the specified model."""
    model_id = config.MODEL_ID
    if "gpt" in config.MODEL_ID.lower():
        model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
    return LocalLanguageModelClient(model_id)


def init_llm_client() -> OpenAI | LocalLanguageModelClient:
    return (
        init_local_llm()
        if config.LOCAL
        else OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    )


class TextGenerator:
    """
    A text generator class that uses a singleton pattern to ensure

    only one instance handles all text generation requests.
    """

    def __init__(self):
        self.client = init_llm_client()

    def generate_text(
        self, messages, max_tokens: int, temperature: float
    ) -> Stream[ChatCompletionChunk]:
        completions = self.client.chat.completions.create(
            model=config.MODEL_ID,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        return completions
