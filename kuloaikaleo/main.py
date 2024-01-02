import signal
from typing import Dict

# Assuming the existence of Action classes in actions.py
from actions import (
    Action,
    TalkToGPTAction,
    TranscribeAndPasteTextAction,
    UpdateSettingsAction,
)
from config import config
from kaaoao import Transcriber, init_client
from leo import AudioDetector, AudioRecorder
from loguru import logger
from utils import transcript_contains_phrase

# logger.remove()
# logger.add(sys.stderr, level="INFO")


class ActionController:
    def __init__(self):
        self.actions: Dict[str, Action] = {}

    def register_action(self, action: Action):
        self.actions[action.name] = action

    def check_and_perform_actions(self, transcription: str):
        for action_name, action in self.actions.items():
            logger.debug(
                f"Checking phrase: {action.phrase} in transcription: {transcription}"
            )
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

    def register_actions(self):
        transcribe_action = TranscribeAndPasteTextAction(
            "hi baby", "bye baby", self.recorder, self.transcriber
        )
        talk_to_gpt_action = TalkToGPTAction(
            "hi computer", "bye computer", self.recorder, self.transcriber
        )
        update_settings_action = UpdateSettingsAction(
            "update settings",
            "finish update",
            self.recorder,
            self.transcriber,
            init_client(),
        )

        self.action_controller.register_action(transcribe_action)
        self.action_controller.register_action(talk_to_gpt_action)
        self.action_controller.register_action(update_settings_action)

    def listen_and_respond(self):
        self.register_actions()
        while True:
            transcription = self.audio_detector.detect_phrases(
                listening_interval=0.5,
                pre_audio_file=config.DICTATION_AUDIO_FILE,
            )
            action_performed = self.action_controller.check_and_perform_actions(
                transcription
            )
            if action_performed:
                logger.info(
                    f"Performed action: {action_performed}, clearing signal queue"
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
