import os
import signal
import sys
import threading
import time
from typing import Dict

import yaml
from loguru import logger

# Assuming the existence of Action classes in actions.py
from voice_action_assistant.actions import Action, ActionFactory
from voice_action_assistant.config import config
from voice_action_assistant.recorder import AudioDetector, AudioRecorder
from voice_action_assistant.transcriber import Transcriber
from voice_action_assistant.utils import play_sound, transcript_contains_phrase

# Start a new thread to play the startup audio
threading.Thread(
    target=play_sound,
    args=(
        os.path.join(
            config.AUDIO_FILES_DIR,
            "startup-audio.wav",
        ),
    ),
).start()


def logger_init(level="INFO"):
    logger.remove()
    # Define a custom log level
    logger.level("LLM", no=35, color="<fg #a388f2>", icon="🤖")
    # Add a file handler
    logger.add("llm_logs.log", level="LLM")
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
        self.action_factory = ActionFactory()

    def load_actions_from_yaml(self, yaml_file: str):
        with open(yaml_file, "r") as file:
            actions_config = yaml.safe_load(file)

        for action_config in actions_config["actions"]:
            action = self.action_factory.get_action(action_config, self.recorder, self.transcriber)
            if action:
                self.action_controller.register_action(action)
            else:
                logger.error(f"Failed to create action for {action_config['name']}")

    def register_actions(self):
        self.load_actions_from_yaml("actions_config.yml")
        self.action_factory.pretty_print_actions_to_console()

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
                    f"Action '{action_performed}' is complete and signal queue is cleared... Awaiting next command."
                )
                self.audio_detector.recorder.refresh_signal_queue()


def main():
    voice_controlled_recorder = VoiceControlledRecorder()
    voice_controlled_recorder.listen_and_respond()


def exit_program():
    play_sound(os.path.join(config.AUDIO_FILES_DIR, "shutdown-audio.wav"))
    sys.exit()


def run():
    logger.info("Starting voice-controlled recorder...")
    signal.signal(signal.SIGTERM, lambda signum, frame: exit_program())
    signal.signal(signal.SIGINT, lambda signum, frame: exit_program())
    main()


if __name__ == "__main__":
    run()
