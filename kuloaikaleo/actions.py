import json
from typing import Optional

from config import config
from kaaoao import Transcriber
from leo import AudioRecorder
from loguru import logger
from openai import OpenAI
from utils import (
    gpt_post_process_transcript,
    paste_transcript,
    play_sound,
    transcript_contains_phrase,
    tts_transcript,
)


class Action:
    def __init__(self, phrase: str):
        self.phrase = phrase.lower()

    def perform(self, transcript: str = None) -> "ActionResponse":
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


class ToggleGptAction(Action):
    def __init__(self):
        super().__init__(config.TOGGLE_GPT_ACTION_PHRASE)

    def perform(self, transcript: str = None):
        config.USE_GPT = not config.USE_GPT
        logger.info(
            f"Toggling GPT to {config.USE_GPT}; GPT phrase detected in Trascription:\n'{transcript}'"
        )
        return ActionResponse(self, True)


class StartTranscriptionAction(Action):
    def __init__(
        self,
        action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
    ):
        super().__init__(action_phrase)
        self.action_phrase = action_phrase
        self.audio_recorder = audio_recorder
        self.transcriber = transcriber

    def perform(self, action_phrase_transcript):
        if (
            transcript_contains_phrase(action_phrase_transcript, self.action_phrase)
            and not self.audio_recorder.is_recording
        ):
            self.audio_recorder.start_recording()
            logger.info("Recording started...")
            play_sound("sound_start.wav")
            return ActionResponse(self, True)
        return ActionResponse(self, False)


class StopTranscriptionAction(Action):
    def __init__(
        self,
        action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
    ):
        super().__init__(action_phrase)
        self.action_phrase = action_phrase
        self.audio_recorder = audio_recorder
        self.transcriber = transcriber

    def perform(self, action_phrase_transcript):
        if (
            transcript_contains_phrase(action_phrase_transcript, self.action_phrase)
            and self.audio_recorder.is_recording
        ):
            audio_data = self.audio_recorder.stop_recording()
            logger.info("Recording stopped.")
            play_sound("sound_end.wav")
            action_phrase_transcript = self.transcriber.transcribe_audio(audio_data)
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
        self.stop_action = StopTranscriptionAction(
            stop_action_phrase, audio_recorder, transcriber
        )
        self.transcriber = transcriber
        self.audio_recorder = audio_recorder

    def _action_logic(self, transcription_response) -> TranscribeActionResponse:
        raise NotImplementedError

    def perform(self, action_phrase_transcript):
        start_action_response = self.start_action.perform(action_phrase_transcript)
        stop_action_response = self.stop_action.perform(action_phrase_transcript)
        if start_action_response.success:
            return TranscribeActionResponse(self.start_action, True)
        elif stop_action_response.success:
            return self._action_logic(stop_action_response)
        logger.warning("TranscribeAction failed")
        return TranscribeActionResponse(self, False)

    def _clean_and_save_transcript(self, transcript):
        cleaned_transcript = self.transcriber.clean_transcript(transcript)
        self.transcriber.save_transcript(transcript)
        self.audio_recorder.save_recording("output.mp3")
        return cleaned_transcript


class TranscribeAndPasteTextAction(TranscribeAction):
    def __init__(
        self,
        start_action_phrase: str,
        stop_action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
    ):
        super().__init__(
            start_action_phrase, stop_action_phrase, audio_recorder, transcriber
        )

    def _action_logic(
        self, transcription_response: TranscribeActionResponse
    ) -> ActionResponse:
        logger.debug(
            f"Transcription response for Paste action: {transcription_response}"
        )
        if transcription_response.success:
            transcript = transcription_response.transcript
            cleaned_transcript = self._clean_and_save_transcript(transcript)
            paste_transcript(cleaned_transcript)
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
        super().__init__(
            start_action_phrase, stop_action_phrase, audio_recorder, transcriber
        )

    def _action_logic(
        self, transcription_response: TranscribeActionResponse
    ) -> ActionResponse:
        # Implement specific logic for post-processing after transcription
        if transcription_response.success:
            transcript = transcription_response.transcript
            cleaned_transcript = self._clean_and_save_transcript(transcript)
            processed_transcript = gpt_post_process_transcript(cleaned_transcript)
            if config.USE_TTS:
                tts_transcript(processed_transcript)
            if config.USE_STT:
                paste_transcript(processed_transcript)
            logger.debug(f"GPT Processed Transcript: {processed_transcript}")
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
        super().__init__(
            start_action_phrase, stop_action_phrase, audio_recorder, transcriber
        )
        self.openai_client = openai_client

    def _action_logic(
        self, transcription_response: TranscribeActionResponse
    ) -> ActionResponse:
        cleaned_transcript = self._clean_and_save_transcript(
            transcription_response.transcript
        )
        try:
            config_attributes = [
                attr for attr in dir(config) if not attr.startswith("__")
            ]
            preprompt = f"""
                Update config settings based on config attributes.
                Return json object with updated settings.
                example usage:
                
                Attributes: {', '.join(config_attributes)}

                Response:
                ```json
                {{
                    "ATTRIBUT_NAME": "NEW_VALUE"
                }}
                ```
            """
            response = self.openai_client.chat.completions.create(
                model=config.MODEL_ID,
                messages=[
                    {"role": "system", "content": preprompt},
                    {
                        "role": "user",
                        "content": f"Trascription of audio: '{cleaned_transcript}'",
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
