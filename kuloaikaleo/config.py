ACTIVATION_KEYS = "ctrl+alt+space"
EXIT_KEY = "esc"
MAX_RECORDING_LENGTH = 10 * 60 * 1000  # 10 minutes in milliseconds
MODEL_ID = "gpt-4-1106-preview"

HOLD_TO_TALK = True

USE_SPEECH_TO_TEXT = True
USE_GPT_POST_PROCESSING = False
USE_SPOKEN_RESPONSE = False


TRANSCRIPTION_PREPROMPT = """
This is the output of an imperfect speech-to-text engine.

Please convert this text into a more readable format.
You should convert the text into production level, enterprise grade, python code.
This means converting the rough idea from the text into a more polished, production ready, python code.

As a part of this, include function definitions, class definitions, and other python code.
You should also have docstrings and, if necessary to explain WHY something is done, comments.
We use numpydoc style docstrings.

"""
