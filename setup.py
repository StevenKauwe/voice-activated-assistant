from setuptools import setup, find_packages

setup(
    name="kuloaikaleo",
    version="0.1.0",
    description="A voice assistant that transcribes and corrects medical dictations.",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "keyboard",
        "loguru",
        "sounddevice",
        "openai",
        "python-dotenv",
        "scipy",
        "pydub",
        "pygame",
        "gTTS",
    ],
    python_requires=">=3.8",
)
