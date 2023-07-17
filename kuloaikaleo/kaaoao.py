import openai
import os
from dotenv import load_dotenv
from loguru import logger
from pyttsx3 import speak
import threading

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
model_id = "gpt-4"


transcription_prompt = """
You are a helpful medical transcription corrector.
You are helping a doctor transcribe a patient's medical history.
The doctor is dictating the patient's medical history to you.
The audio is transcribed into text.
The text is then sent to you for correction.
You correct the text and send it back to the doctor.
You use context to assume corrections to the written text.
The text is coming from a rudimentary speech-to-text engine.
The engine is not very accurate and makes many mistakes.
You may have to make some pretty big corrections that involve logical leaps based on the sound of the words.
You are very good at this and can make these corrections easily.
You listen to meta-comments from the doctor and adjust the text accordingly.
Meta-comments are comments about the text itself including, "meta" comments, "correction" and "quote".
Meta-comments should be used to correct the text but should not be included in the patient's medical history.
When dealing with a meta-comment `correction`, denote changes using `<old>...</old><correction>...</correction>`
When dealing with a meta-comment `quote`, denote changes using \"...\"
when dealing with a meta-comment `meta`, make the changes inplace (i.e. do not include the meta-comment or original text, only your updated phrasing).
Mark text that is grossly incorrect, non-sensical or has possible medical dangers as `<caution>...<caution><best-practice>...<best-practice>`.
"""

user_description_prompt = """
I am a psychiatrist.
I am dictating a patient's medical history.
I need you to correct the transcription of the patient's medical history.
I will now provide the dictation as text from the speech-to-text engine and you will correct it.
It is very important that quotes are exactly as I say them.
Please use quotes to denote quotes, do not include the words "quote" or "end quote" unless they are a part of the quote itself. 
Please automatically apply standard medical chart formatting.
"""


class Transcriber:
    def __init__(self):
        pass

    def transcribe_and_respond(self, chunks):
        for i, chunk in enumerate(chunks):
            chunk.export(f"output_{i}.mp3", format="mp3")
            self._transcribe_and_respond(f"output_{i}.mp3")

    def _transcribe_and_respond(self, file_name):
        with open(file_name, "rb") as f:
            transcript = openai.Audio.transcribe("whisper-1", f)
        logger.info(f"Transcript: {transcript['text']}")
        self._generate_response(transcript["text"])

    def _generate_response(self, text):
        response = openai.ChatCompletion.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": transcription_prompt,
                },
                {"role": "user", "content": user_description_prompt},
                {"role": "user", "content": f"Trascription of audio: '{text}'"},
            ],
            max_tokens=1000,
            temperature=0.1,
        )
        response_text = response["choices"][0]["message"]["content"]
        logger.info(f"Response: {response_text}")
        try:
            speaker_thread = threading.Thread(target=speak, args=(response_text,))
            speaker_thread.daemon = True
            speaker_thread.start()
        except Exception as e:
            logger.error(f"Error with text-to-speech engine: {e}")
        logger.info("Response spoken.")
