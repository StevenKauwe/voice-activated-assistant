class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.MODEL_ID = "gpt-4-turbo"
        self.COPY_TO_CLIPBOARD = True
        self.EXTRACT_CODE_BLOCKS = True
        self.LOCAL = True  # This only works for STT for now
        self.MAX_AUDIO_LENGTH_SECONDS = 60 * 60  # Audio recording timelimit in seconds

        # This is for text to speech. Currently only works with OpenAI's API. This is expensive.
        self.USE_TTS = False  # This is expensive if you're using a cloud service
        self.AUDIO_SPEED = 1.25  # Speed up the audio by this factor

        # Define Directory Paths. Don't change these unless you know what you're doing.
        self.AUDIO_FILES_DIR = "src/audio_files"
        self.LLM_ACTION_PROMPTS_DIR = "src/llm-action-prompts"

        # This requires system permissions to run.
        # Don't enable this unless you know are certain you want to use it.
        self.PASTE_AT_CURSOR = False

    def update(self, key, value):
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise ValueError(f"Invalid config key: {key}")


config = Config()
