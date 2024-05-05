# Voice-Activated Assistant

## Overview

This voice-activated assistant is a Python application designed to listen for specific audio cues and perform corresponding actions. It combines audio recording, transcription, and action execution to provide a voice-activated interface for various tasks. The assistant uses a combination of local speech-to-text processing and customizable actions, integrated with external services for enhanced functionality.

## Features

- **Wake Phrase Detection**: Activates listening mode upon hearing a specified phrase.
- **Audio Transcription**: Converts spoken words into text using a speech-to-text model.
- **Action Handling**: Executes customizable actions based on transcribed text.
- **External Service Integration**: Can be integrated with APIs for additional functionalities such as text generation.

## Requirements

- Rye package manager for Python projects
  - Python 3.12 will be installed by Rye when setting up the project
- FFMPEG for audio processing
- Access to text generation tool:
  1. Ollama server, recommended for local LLM
     - requires a server running on your local machine
  2. HuggingFace's Transformers library
     - works out of the box
     - runs slower than Ollama
  3. OpenAI API key, most powerful
     - requires an internet connection
     - incurs costs
     - may have privacy implications
- Microphone access on your device

## Installation

1. **Install [Rye](https://rye-up.com/guide/installation/)**:
    ```bash
    curl -sSf https://rye-up.com/get | bash
    ```
2. **Install [FFMPEG](https://ffmpeg.org/)**:

    FFmpeg is required for processing audio files.
    Install it using your system's package manager or download the binaries:
    <details>

      <summary>On Ubuntu/Debian:</summary>
      
      ```bash
      sudo apt update
      sudo apt install ffmpeg
      ```
    </details>
    <details>
      <summary>On macOS:</summary>

      ```bash
      brew install ffmpeg
      ```
    </details>
    <details>
      <summary>On Windows:</summary>

    - Download the binaries from [FFmpeg's official website](https://ffmpeg.org/download.html) and add the path to the executable to your system's PATH variable.
    </details>
3. **Set Up Project**:
    Navigate to your project directory and sync the project using Rye:
    ```bash
    rye sync
    ```
4. **Create Your Configure Files**:

    Copy the example configuration files to use them as a starting point.
    ```bash
    cp example_actions_config.yml actions_config.yml
    cp example_settings_config.yml settings_config.yml
    ```
    You should look at the exaple tools provided. You can delete these and make your own as needed.

5. **Set up OpenAI credentials or use a local LLM**
    <details>
      <summary>Use a local LLM (recommended):</summary>

      You can use a local language model (LLM) for text generation instead of the OpenAI API.
      This can be more cost-effective and provide better privacy.
      We enable to ways to de this:
      1. Use Ollama to host a local LLM server.
      2. Use Hugging Face's Transformers library to directly load your local LLM at voice-assistant start-up.
        
      ### Update the `settings_config.yml` file.
      - `settings_config.yml` file to use a local LLM for text generation.
      If you are using Ollama, set the `OLLAMA_SERVER_URL` environment variable to the URL of your Ollama server.
      Otherwise, set the `HUGGINGFACE_MODEL_ID` environment variable to the model ID of the LLM you want to use.
        
      ### 1. Set up Ollama
      1. Go to [Ollama](https://ollama.com/) and download the server for your operating system.
      2. Follow the instructions to set up the server and get the server URL.
      - If the voice assistant is unable to connect to the server, you may need to adjust the Ollama CORS settings.
      - In general setting `OLLAMA_ORIGINS "*"` will allow access from any origin and fixes the problem.
        - This is probably fine locally but is not recommended for production environments.

      ```yaml
      llm_config:
        llm_id: "llama3"
        llm_type: "ollama"
        server_url: "http://localhost:11434/v1"
      ```

      ### 2. Use HuggingFace's Transformers
      You can use Hugging Face's Transformers library to load a local LLM. You can find the model ID for the LLM you want to use on the Hugging Face Model Hub.
      You can also use the `transformers` library to load a local model from a file path.
      ```yaml
      llm_config:
        llm_id: "unsloth/llama-3-8b-Instruct-bnb-4bit"
        llm_type: "huggingface"
      ```
    </details>

    <details open>
      <summary>Use OpenAI for your LLM:</summary>
      
      Sign up for api access at [OpenAI](https://openai.com/index/openai-api) and follow instructions to create an api key.
      If for non-personal, make sure this repo adheres to all required policies, then get an API key from an Admin in your Organization (as applicable).

      ### Update the `settings_config.yml` file.
      - `settings_config.yml` file to use the OpenAI API for text generation.
      Set the `OPENAI_API_KEY` environment variable to your OpenAI API key.
      ```yaml
      llm_config:
        llm_id: "gpt-4-turbo"
        llm_type: "openai"
      ```

      ### Set API key on macOS

      1. Append your API key to your `.bashrc` or `.zshrc` file:
      ```bash
      echo 'export OPENAI_API_KEY="your_openai_api_key"' >> ~bashrc
      ```
      2. Source the file to update your environment variables:
      ```bash
      source ~/.bashrc
      ```
      
      ### Set API key on Windows

      1. Open a new Command Prompt as Administrator.

      2. Set your API key as an environment variable using the `setx` command. Replace `"your_openai_api_key"` with your actual OpenAI API key:
      ```cmd
      setx OPENAI_API_KEY "your_openai_api_key"
      ```
      3. Close the Command Prompt. The changes will take effect when you open a new Command Prompt.

    </details>


## Usage

After setting up the configuration file and environment variables, you can run your application.

To start the voice-activated assistant, run EITHER of the following command in your terminal:

```bash
# Easier to remember but longer to type
rye run voice-assistant

# I also included a shorter version of the same command (see .toml to customize)
rye run va
```

Once running, the application will listen for the wake phrase and then await further voice commands to trigger registered actions.
You may need to adjust settings to allow the application to access your microphone.
On a macOS system, you can do this by going to `System Preferences` -> `Security & Privacy` -> `Privacy` -> `Microphone` and enabling access for the terminal application you are using.

## Actions

The application supports registering custom actions.
Each action is associated with a specific phrase that, when detected in the transcription, will trigger the action's `perform` method.

The following actions are included by default:

- `TranscribeAndPasteTextAction`: Transcribes spoken text and pastes it into a text field.
- `TalkToLanguageModelAction`: Sends the transcribed text to LLM for processing and handles the response.
- `AssistantSettingsAction`: Updates settings based on voice commands.

You can register additional actions by extending the `Action` class and adding them to the `ActionController`.

## Customization

To customize actions or add new ones, modify the `actions_config.yml` file.
Updates to the action config will create new instances of your action classes and register them in the `actions_config.yml` file.

## Settings

To adjust the application's behavior, modify the `settings_config.yml` file. For example, you can change the model ID, enable or disable copying to the clipboard, adjust the maximum audio length, and more.

## License

Please ensure you comply with the licenses of all components and dependencies used within this application.

