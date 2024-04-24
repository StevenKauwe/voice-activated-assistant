import os
import signal
import sys
import time
from typing import Dict

from loguru import logger

# Assuming the existence of Action classes in actions.py
from voice_action_assistant.actions import (
    Action,
    TalkToGPTAction,
    TranscribeAndSaveTextAction,
    UpdateSettingsAction,
)
from voice_action_assistant.config import config
from voice_action_assistant.recorder import AudioDetector, AudioRecorder
from voice_action_assistant.transcriber import Transcriber, init_client
from voice_action_assistant.utils import load_text_file, transcript_contains_phrase


def logger_init(level="INFO"):
    logger.remove()
    # Define a custom log level
    logger.level("GPT", no=35, color="<fg #a388f2>", icon="🤖")
    # Add a file handler
    logger.add("gpt_logs.log", level="GPT")
    logger.add(sys.stderr, level=level)


logger_init()


class ActionController:
    def __init__(self):
        self.actions: Dict[str, Action] = {}

    def register_action(self, action: Action):
        self.actions[action.name] = action

    def check_and_perform_actions(self, transcription: str):
        for action_name, action in self.actions.items():
            logger.debug(f"Checking phrase: {action.phrase} in transcription: {transcription}")
            if transcript_contains_phrase(transcription, action.phrase):
                response = action.perform(transcription)
                if response.success:
                    return action_name
        return None


class VoiceControlledRecorder:
    def __init__(self):
        self.wake_audio_recorder = AudioRecorder("wake phrase recorder", max_seconds=3)
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.audio_detector = AudioDetector(self.wake_audio_recorder, self.transcriber)
        self.action_controller = ActionController()
        self.action_prompts_dir = config.LLM_ACTION_PROMPTS_DIR

    def register_actions(self):
        """
        This is where all user actions are registered.
        This should probably define the different "gpt" actions in a configuration file.
        """
        transcribe_action = TranscribeAndSaveTextAction(
            "hi friend", "see ya", self.recorder, self.transcriber
        )
        talk_to_gpt_action = TalkToGPTAction(
            "hi computer",
            "see ya",
            self.recorder,
            self.transcriber,
            action_name="general gpt",
            system_message=load_text_file(os.path.join(self.action_prompts_dir, "general_gpt.md")),
        )
        write_ticket_action = TalkToGPTAction(
            "new ticket",
            "see ya",
            self.recorder,
            self.transcriber,
            action_name="write ticket",
            system_message=load_text_file(os.path.join(self.action_prompts_dir, "jira_ticket.md")),
        )
        write_pr_action = TalkToGPTAction(
            "new pull request",
            "see ya",
            self.recorder,
            self.transcriber,
            action_name="write pull request description",
            system_message=load_text_file(
                os.path.join(self.action_prompts_dir, "pull_request.md"),
            ),
        )
        update_settings_action = UpdateSettingsAction(
            "update settings",
            "finish update",
            self.recorder,
            self.transcriber,
            init_client(),
        )

        self.action_controller.register_action(transcribe_action)
        self.action_controller.register_action(update_settings_action)
        self.action_controller.register_action(write_ticket_action)
        self.action_controller.register_action(talk_to_gpt_action)
        self.action_controller.register_action(write_pr_action)

    def listen_and_respond(self):
        self.register_actions()
        start_time = time.time()  # get the current time
        while True:
            if time.time() - start_time > 8 * 60 * 60:
                logger.info("8 hours have passed, shutting down...")
                break
            transcription = self.audio_detector.detect_phrases(
                listening_interval=0.5,
            )
            action_performed = self.action_controller.check_and_perform_actions(transcription)
            if action_performed:
                logger.info(
                    f"Detected audio event for `{action_performed}`, clearing signal queue"
                )
                logger.info(
                    "Action is complete and signal queue is cleared... Awaiting next command."
                )
                self.audio_detector.recorder.refresh_signal_queue()


def main():
    voice_controlled_recorder = VoiceControlledRecorder()
    voice_controlled_recorder.listen_and_respond()


def run():
    logger.info("Starting voice-controlled recorder...")
    signal.signal(signal.SIGTERM, lambda signum, frame: exit())
    signal.signal(signal.SIGINT, lambda signum, frame: exit())
    main()


if __name__ == "__main__":
    run()
