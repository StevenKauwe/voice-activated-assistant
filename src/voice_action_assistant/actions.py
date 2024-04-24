import json
from abc import abstractmethod
from textwrap import dedent
from typing import Optional

import pyperclip
from loguru import logger
from openai import OpenAI

from voice_action_assistant.config import config
from voice_action_assistant.recorder import AudioRecorder
from voice_action_assistant.transcriber import Transcriber
from voice_action_assistant.utils import (
    init_client,
    load_text_file,
    paste_at_cursor,
    play_sound,
    transcript_contains_phrase,
    tts_transcript,
)


class Action:
    def __init__(self, phrase: str):
        self.phrase = phrase.lower()

    @abstractmethod
    def perform(self, transcript: str = "") -> "ActionResponse":
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError


class ActionResponse:
    def __init__(self, action: Action, success: bool):
        self.action = action
        self.success = success


class TranscribeActionResponse(ActionResponse):
    def __init__(self, action: Action, success: bool, transcript: Optional[str] = None):
        super().__init__(action, success)
        self.transcript = transcript


class StartTranscriptionAction(Action):
    def __init__(
        self,
        phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
    ):
        super().__init__(phrase)
        self.phrase = phrase
        self.audio_recorder = audio_recorder
        self.transcriber = transcriber

    def perform(self, action_phrase_transcript):
        if (
            transcript_contains_phrase(action_phrase_transcript, self.phrase)
            and not self.audio_recorder.is_recording
        ):
            self.audio_recorder.start_recording()
            logger.info("StartTranscriptionAction - Recording started.")
            play_sound("src/audio_files/sound_start.wav")
            return ActionResponse(self, True)
        return ActionResponse(self, False)


class StopTranscriptionAction(Action):
    def __init__(
        self,
        phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
    ):
        super().__init__(phrase)
        self.phrase = phrase
        self.audio_recorder = audio_recorder
        self.transcriber = transcriber

    def perform(self, action_phrase_transcript, in_progress: bool = False):
        if not in_progress:
            return TranscribeActionResponse(self, False)
        if (
            transcript_contains_phrase(action_phrase_transcript, self.phrase)
            and self.audio_recorder.is_recording
        ):
            audio_data = self.audio_recorder.stop_recording()
            logger.info("StopTranscriptionAction - Recording stopped.")
            play_sound("src/audio_files/sound_end.wav")
            action_phrase_transcript = self.transcriber.transcribe_audio(audio_data)
            logger.info(f"Raw Transcript: {action_phrase_transcript}")
            return TranscribeActionResponse(self, True, action_phrase_transcript)
        return TranscribeActionResponse(self, False)


class TranscribeAction(Action):
    def __init__(
        self,
        start_action_phrase: str,
        stop_action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
    ):
        # An empty phrase as this action is composed of sub-actions
        super().__init__("")
        self.start_action = StartTranscriptionAction(
            start_action_phrase, audio_recorder, transcriber
        )
        self.stop_action = StopTranscriptionAction(stop_action_phrase, audio_recorder, transcriber)
        self.transcriber = transcriber
        self.audio_recorder = audio_recorder
        self.in_progress = False

    def _action_logic(self, transcription_response) -> TranscribeActionResponse:
        raise NotImplementedError

    def perform(self, action_phrase_transcript):
        start_action_response = self.start_action.perform(action_phrase_transcript)
        stop_action_response = self.stop_action.perform(action_phrase_transcript, self.in_progress)
        if start_action_response.success:
            self.in_progress = True
            return TranscribeActionResponse(self.start_action, True)
        elif stop_action_response.success and self.in_progress:
            self.in_progress = False
            return self._action_logic(stop_action_response)
        logger.debug("TranscribeAction did not perform any action.")
        return TranscribeActionResponse(self, False)

    def _clean_and_save_transcript(self, transcript):
        cleaned_transcript = self.transcriber.clean_transcript(transcript, self.stop_action.phrase)
        self.transcriber.save_transcript(transcript)
        self.audio_recorder.save_recording("src/audio_files/output.mp3")
        return cleaned_transcript


class TranscribeAndSaveTextAction(TranscribeAction):
    def __init__(
        self,
        start_action_phrase: str,
        stop_action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
    ):
        super().__init__(start_action_phrase, stop_action_phrase, audio_recorder, transcriber)

    def _action_logic(self, transcription_response: TranscribeActionResponse) -> ActionResponse:
        logger.debug(f"Transcription response for Paste action: {transcription_response}")
        if transcription_response.success:
            transcript = transcription_response.transcript
            cleaned_transcript = self._clean_and_save_transcript(transcript)
            if config.COPY_TO_CLIPBOARD:
                pyperclip.copy(cleaned_transcript)
            if config.PASTE_AT_CURSOR:
                paste_at_cursor()
            logger.info(f"Processed Transcript: {transcript}")
            return ActionResponse(success=True, action=self)
        else:
            return ActionResponse(success=False, action=self)

    @property
    def name(self):
        return self.__class__.__name__


class TalkToGPTAction(TranscribeAction):
    def __init__(
        self,
        start_action_phrase: str,
        stop_action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
    ):
        super().__init__(start_action_phrase, stop_action_phrase, audio_recorder, transcriber)

    def _action_logic(self, transcription_response: TranscribeActionResponse) -> ActionResponse:
        # Implement specific logic for post-processing after transcription
        if transcription_response.success:
            transcript = transcription_response.transcript
            cleaned_transcript = self._clean_and_save_transcript(transcript)

            # GPT Logic
            system_prompt = dedent(
                f"""\
                context from user:
                {load_text_file("prompt.md")}

                {pyperclip.paste()}
                """
            )

            openai_client = init_client()
            completion = openai_client.chat.completions.create(
                model=config.MODEL_ID,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{cleaned_transcript}"},
                ],
                max_tokens=1024,
                temperature=0.1,
                stream=True,
            )

            gpt_response_content = ""

            # open the file in append mode
            with open("live_response.md", "w") as f:
                f.write("# GPT RESPONSE\n\n")
            for chunk in completion:
                str_delta = chunk.choices[0].delta.content
                if str_delta:
                    with open("live_response.md", "a") as f:
                        f.write(str_delta)
                    gpt_response_content += str_delta

            logger.log("GPT", f"\n{'-'*20}\n{gpt_response_content}\n{'-'*20}\n")
            with open("output.txt", "a") as f:
                f.write(f"\nGPT output:\n{gpt_response_content}")

            if "```python" in gpt_response_content:
                none_python_text = (
                    gpt_response_content.split("```python")[0]
                    + gpt_response_content.split("```python")[1].split("```")[1]
                )
            else:
                none_python_text = gpt_response_content

            if config.USE_TTS:
                tts_transcript(none_python_text)
            return ActionResponse(success=True, action=self)
        else:
            return ActionResponse(success=False, action=self)

    @property
    def name(self):
        return self.__class__.__name__


class UpdateSettingsAction(TranscribeAction):
    def __init__(
        self,
        start_action_phrase: str,
        stop_action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
        openai_client: OpenAI,
    ):
        super().__init__(start_action_phrase, stop_action_phrase, audio_recorder, transcriber)
        self.openai_client = openai_client

    def _action_logic(self, transcription_response: TranscribeActionResponse) -> ActionResponse:
        cleaned_transcript = self._clean_and_save_transcript(transcription_response.transcript)
        try:
            config_attributes = [attr for attr in dir(config) if not attr.startswith("__")]
            preprompt = f"""
                Update config settings based on config attributes.
                Return json object with updated settings.
                Do not include any other response, just the json object.
                This is effectively "function calling".
                Assume values if not given e.g. "enable internet" -> "USE_INTERNET=True"

                
                Only use the Attributes: {', '.join(config_attributes)}

                Example Response:
                ```json
                {{
                    "ATTRIBUTE_NAME": "NEW_VALUE"
                }}
                ```
            """
            response = self.openai_client.chat.completions.create(
                model=config.MODEL_ID,
                messages=[
                    {"role": "system", "content": preprompt},
                    {
                        "role": "user",
                        "content": f"User Command: '{cleaned_transcript}'",
                    },
                ],
                max_tokens=1000,
                temperature=0.1,
            )
            response_text = response.choices[0].message.content
            logger.info(f"Response: {response_text}")
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            response_json = json.loads(response_text)
            for key, value in response_json.items():
                config.update(key, value)
            return ActionResponse(self, True)
        except Exception as e:
            logger.error(e)
            return ActionResponse(self, False)

    @property
    def name(self):
        return self.__class__.__name__
