import json
import os
import re
from textwrap import dedent
from typing import Optional

import pyperclip
from loguru import logger

from voice_action_assistant.config import config
from voice_action_assistant.recorder import AudioRecorder
from voice_action_assistant.transcriber import Transcriber
from voice_action_assistant.utils import (
    ColorEnum,
    color_text,
    copy_to_clipboard,
    init_client,
    paste_at_cursor,
    play_sound,
    python_printer,
    transcript_contains_phrase,
    tts_transcript,
)


class Action:
    def __init__(self, phrase: str):
        self.phrase = phrase.lower()
        self.audio_files_dir = config.AUDIO_FILES_DIR

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
            play_sound(os.path.join(self.audio_files_dir, "sound_start.wav"))
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
            play_sound(os.path.join(self.audio_files_dir, "sound_end.wav"))
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
        action_name: str | None = None,
        system_message: str | None = None,
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
        self.action_name = action_name
        self.system_message = system_message

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
        self.audio_recorder.save_recording("output.mp3")
        return cleaned_transcript


class TranscribeAndSaveTextAction(TranscribeAction):
    def __init__(
        self,
        start_action_phrase: str,
        stop_action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
        action_name: str | None = None,
        system_message: str | None = None,
    ):
        super().__init__(
            start_action_phrase,
            stop_action_phrase,
            audio_recorder,
            transcriber,
            action_name,
            system_message,
        )

    def _action_logic(self, transcription_response: TranscribeActionResponse) -> ActionResponse:
        logger.debug(f"Transcription response for Paste action: {transcription_response}")
        if transcription_response.success:
            transcript = transcription_response.transcript
            cleaned_transcript = self._clean_and_save_transcript(transcript)
            copy_to_clipboard(cleaned_transcript)
            paste_at_cursor()
            logger.info(f"Processed Transcript: {transcript}")
            play_sound(os.path.join(config.AUDIO_FILES_DIR, "action-complete-audio.wav"))
            return ActionResponse(success=True, action=self)
        else:
            return ActionResponse(success=False, action=self)

    @property
    def name(self):
        return self.action_name or self.__class__.__name__


class TalkToLanguageModelAction(TranscribeAction):
    def __init__(
        self,
        start_action_phrase: str,
        stop_action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
        action_name: str | None = None,
        system_message: str | None = None,
    ):
        super().__init__(
            start_action_phrase, stop_action_phrase, audio_recorder, transcriber, action_name
        )
        default_system_message = dedent(
            """\
            Please provide correct answers that are concise but complete.
            Assume the user wants advaced idiomatic answers if coding is involved.
            """
        )
        self.system_message = system_message or default_system_message

    def _action_logic(self, transcription_response: TranscribeActionResponse) -> ActionResponse:
        # Implement specific logic for post-processing after transcription
        if transcription_response.success:
            transcript = transcription_response.transcript
            cleaned_transcript = self._clean_and_save_transcript(transcript)

            # LLM Logic
            system_prompt = dedent(
                f"""\
                {self.system_message}

                My current clipboard content (if any):
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
                max_tokens=2048,
                temperature=0.1,
                stream=True,
            )

            llm_response_content = ""

            # open the file in append mode

            print("\n----- LLM Response Started  -----\n")
            with open("live_response.md", "w") as f:
                f.write("# LLM RESPONSE\n\n")
            for chunk in completion:
                str_delta = chunk.choices[0].delta.content
                if str_delta:
                    with open("live_response.md", "a") as f:
                        f.write(str_delta)
                    llm_response_content += str_delta
                    python_printer.print(str_delta)

            print("\n----- LLM Response Finished -----\n")
            with open("output.txt", "a") as f:
                f.write(f"\nLLM output:\n{llm_response_content}")

            # Copy relevant to clipboard
            try:
                copy_to_clipboard(llm_response_content)
                if config.EXTRACT_CODE_BLOCKS:
                    code_blocks = re.findall(r"```.*?\n(.*?)```", llm_response_content, re.DOTALL)
                    print("Code Blocks: ", code_blocks)
                    if code_blocks:
                        formatted_code_blocks = "\n---\n".join(code_blocks)
                        copy_to_clipboard(formatted_code_blocks)
            except Exception as e:
                logger.error(e)
                none_python_text = llm_response_content

            if config.USE_TTS:
                tts_transcript(none_python_text)

            play_sound(os.path.join(config.AUDIO_FILES_DIR, "action-complete-audio.wav"))
            return ActionResponse(success=True, action=self)
        else:
            return ActionResponse(success=False, action=self)

    @property
    def name(self):
        return self.action_name or self.__class__.__name__


class UpdateSettingsAction(TranscribeAction):
    def __init__(
        self,
        start_action_phrase: str,
        stop_action_phrase: str,
        audio_recorder: AudioRecorder,
        transcriber: Transcriber,
        action_name: str | None = None,
        system_message: str | None = None,
    ):
        super().__init__(
            start_action_phrase,
            stop_action_phrase,
            audio_recorder,
            transcriber,
            action_name,
            system_message,
        )

    def _action_logic(self, transcription_response: TranscribeActionResponse) -> ActionResponse:
        openai_client = init_client()
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
            response = openai_client.chat.completions.create(
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


class ActionFactory:
    def __init__(self):
        self.action_classes = {
            "TalkToLanguageModelAction": TalkToLanguageModelAction,
            "TranscribeAndSaveTextAction": TranscribeAndSaveTextAction,
            "UpdateSettingsAction": UpdateSettingsAction,
        }
        self.loaded_actions = []

    def generate_table(self):
        headers = ["Action Name", "Start Phrase", "End Phrase"]
        table_data = [
            [config["name"], config["start_phrase"], config["end_phrase"]]
            for config in self.loaded_actions
        ]
        max_lengths = [max(len(x) for x in col) for col in zip(*([headers] + table_data))]

        line = (
            "| "
            + " | ".join(f"{header:<{length}}" for header, length in zip(headers, max_lengths))
            + " |"
        )
        separator = "|-" + "-|-".join("-" * length for length in max_lengths) + "-|"
        boarder_separator = "|=" + "===".join("=" * length for length in max_lengths) + "=|"
        table_name = "Loaded Actions"
        table_title = f"| {table_name:^{len(line) - 4}} |"

        table = [boarder_separator, table_title, boarder_separator, line, separator]
        for row in table_data:
            table.append(
                "| "
                + " | ".join(f"{cell:<{length}}" for cell, length in zip(row, max_lengths))
                + " |"
            )
        table.append(boarder_separator)

        return "\n" + color_text("\n".join(table), ColorEnum.CYAN)

    def pretty_print_actions_to_console(self):
        logger.info(self.generate_table())

    def get_action(self, action_config, recorder, transcriber):
        action_class = self.action_classes.get(action_config["class"])
        if not action_class:
            logger.error(f"Action class {action_config['class']} not found")
            return None
        self.loaded_actions.append(action_config)
        return action_class(
            start_action_phrase=action_config["start_phrase"],
            stop_action_phrase=action_config["end_phrase"],
            audio_recorder=recorder,
            transcriber=transcriber,
            action_name=action_config["name"],
            system_message=action_config["prompt"],
        )
