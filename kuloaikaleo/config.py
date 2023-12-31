from dataclasses import dataclass

ACTIVATION_KEYS = "ctrl+alt+space"
EXIT_KEYS = "ctrl+alt+s"
MODEL_ID = "gpt-4-1106-preview"

# HOLD_TO_TALK = True
HOLD_TO_TALK = False
TIMEOUT = 60 * 60  # 1 hour

USE_SPEECH_TO_TEXT = True
USE_GPT_POST_PROCESSING = False
USE_SPOKEN_RESPONSE = False

LOCAL = True
LANGUAGE = "en"


TRANSCRIPTION_PREPROMPT = """
This is the output of an imperfect speech-to-text engine.

Please convert this text into a more readable format.
You should convert the text into production level, enterprise grade, python code.
This means converting the rough idea from the text into a more polished, production ready, python code.

As a part of this, include function definitions, class definitions, and other python code.
You should also have docstrings and, if necessary to explain WHY something is done, comments.
We use numpydoc style docstrings.

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
