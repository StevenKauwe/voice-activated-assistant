from dataclasses import dataclass

ACTIVATION_KEYS = "ctrl+alt+space"
EXIT_KEYS = "ctrl+alt+s"
MODEL_ID = "gpt-4-1106-preview"
MODEL_ID = "gpt-3.5-turbo-1106"
AUDIO_FILE_DIR = "outputs"

# HOLD_TO_TALK = True
HOLD_TO_TALK = False
TIMEOUT = 60 * 60  # 1 hour

USE_SPEECH_TO_TEXT = True
USE_GPT_POST_PROCESSING = True
USE_SPOKEN_RESPONSE = False

LOCAL = True
LANGUAGE = "en"


TRANSCRIPTION_PREPROMPT = """
# Trascript Converter

This is the output of an imperfect speech-to-text engine.
Please convert this text into a more readable format.

## python code

You should convert the text into production level, enterprise grade, python code.
This means converting the rough idea from the text into a more polished, production ready, python code.

As a part of this, include function definitions, class definitions, and other python code.
You should also have docstrings if usage is complex (otherwise we prefer simple) and, if necessary to explain WHY something is done, comments.
We use numpy doc style docstrings. Black and flake8 are used for formatting and linting.

## general

You should fix any spelling mistakes, grammar mistakes, and other mistakes in the text.
You should also seek to fix any mistakes from the speech-to-text engine itself.
This includes fixing any mistakes in the punctuation, capitalization, and other aspects of the text.
You might need to replace words based on context, or add words to make the text more readable.
You should also add whitespace to make the text more readable (e.g. add newlines, spaces, etc.) since the speech-to-text engine does not add any whitespace.
"""

PRINT_TO_TERMINAL = True


@dataclass
class ApiOptions:
    model: str = "whisper-1"
    language: str = None
    temperature: float = 0.0
    initial_prompt: str = None


@dataclass
class ModelOptions:
    model: str = "base"
    device: str = None
    language: str = None
    temperature: float = 0.0
    initial_prompt: str = None
    condition_on_previous_text: bool = True
    verbose: bool = False


ApiOptions = ApiOptions()
ModelOptions = ModelOptions()
