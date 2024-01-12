# Voice-Controlled Recorder

## Overview

The Voice-Controlled Recorder is a Python application that listens for specific audio cues and performs actions based on those cues. It uses a combination of audio recording, transcription, and action handling to provide a voice-activated interface for various tasks.

## Features

- Wake phrase detection to start listening for commands.
- Transcription of audio to text for command recognition.
- Customizable actions that can be triggered by voice commands.
- Integration with external services for advanced functionalities (e.g., GPT, transcription services).

## Requirements

- Python 3.x
- Dependencies from `requirements.txt` (install with `pip install -r requirements.txt`)

## Setup

1. Install the required Python packages.
2. Ensure you have the necessary credentials and settings for any external services used by the actions (e.g., GPT, transcription services).

## Usage

To start the voice-controlled recorder, run the following command in your terminal:

```bash
python main.py
```

Once running, the application will listen for the wake phrase and then await further voice commands to trigger registered actions.

## Actions

The application supports registering custom actions. Each action is associated with a specific phrase that, when detected in the transcription, will trigger the action's `perform` method.

The following actions are included by default:

- `TranscribeAndPasteTextAction`: Transcribes spoken text and pastes it into a text field.
- `TalkToGPTAction`: Sends the transcribed text to GPT for processing and handles the response.
- `UpdateSettingsAction`: Updates settings based on voice commands.

You can register additional actions by extending the `Action` class and adding them to the `ActionController`.

## Customization

To customize actions or add new ones, modify the `VoiceControlledRecorder.register_actions` method. Create instances of your action classes and register them with the `ActionController`.

## Logging

The application uses `loguru` for logging. You can adjust the logging level by modifying the `logger_init` function call in the script.

## Graceful Shutdown

The application handles `SIGTERM` and `SIGINT` signals to ensure a graceful shutdown when the process is terminated.

## License

Please ensure you comply with the licenses of all components and dependencies used within this application.
