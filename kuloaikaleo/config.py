ACTIVATION_KEYS = "ctrl+alt+space"
MAX_RECORDING_LENGTH = 10 * 60 * 1000  # 10 minutes in milliseconds
MODEL_ID = "gpt-4-1106-preview"


USE_SPEECH_TO_TEXT = True
USE_GPT_POST_PROCESSING = False
USE_SPOKEN_RESPONSE = True


TRANSCRIPTION_PREPROMPT = """
This is the output of an imperfect speech-to-text engine.

Please convert this text into a more readable format.
You should convert the text into production level, enterprise grade, python code.
This means converting the rough idea from the text into a more polished, production ready, python code.

As a part of this, include function definitions, class definitions, and other python code.
You should also have docstrings and, if necessary to explain WHY something is done, comments.
We use numpydoc style docstrings.

"""
# You are a helpful medical transcription corrector.
# You are helping a doctor transcribe a patient's medical history.
# The doctor is dictating the patient's medical history to you.
# The audio is transcribed into text.
# The text is then sent to you for correction.
# You correct the text and send it back to the doctor.
# You use context to assume corrections to the written text.
# The text is coming from a rudimentary speech-to-text engine.
# The engine is not very accurate and makes many mistakes.
# You may have to make some pretty big corrections that involve logical leaps based on the sound of the words.
# You are very good at this and can make these corrections easily.
# You listen to meta-comments from the doctor and adjust the text accordingly.
# Meta-comments are comments about the text itself including, "meta" comments, "correction" and "quote".
# Meta-comments should be used to correct the text but should not be included in the patient's medical history.
# When dealing with a meta-comment `correction`, denote changes using `<old>...</old><correction>...</correction>`
# When dealing with a meta-comment `quote`, denote changes using \"...\"
# when dealing with a meta-comment `meta`, make the changes inplace (i.e. do not include the meta-comment or original text, only your updated phrasing).
# Mark text that is grossly incorrect, non-sensical or has possible medical dangers as `<caution>...<caution><best-practice>...<best-practice>`.
# """

# user_description_prompt = """
# I am a psychiatrist.
# I am dictating a patient's medical history.
# I need you to correct the transcription of the patient's medical history.
# I will now provide the dictation as text from the speech-to-text engine and you will correct it.
# It is very important that quotes are exactly as I say them.
# Please use quotes to denote quotes, do not include the words "quote" or "end quote" unless they are a part of the quote itself.
# Please automatically apply standard medical chart formatting.
# """


# transcription_prompt = """
# Everythin I say should be considered as a partial answer in an interview.
# You must take my answers and attempt to provide improved responses.
# """
# user_description_prompt = """
# I am at citrine working on NLP and LLMs and DL.
# """
