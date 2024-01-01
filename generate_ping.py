import numpy as np
from scipy.io.wavfile import write


def generate_ping_sound(start_frequency, end_frequency, duration, sample_rate=44100):
    # Generate time array
    t = np.linspace(0, duration, int(duration * sample_rate), False)

    # Create a frequency array that decreases over time
    frequency = np.linspace(start_frequency, end_frequency, int(duration * sample_rate))

    # Generate a sliding sine wave
    note = np.sin(2 * np.pi * frequency * t)

    # Reduce loudness
    amplitude = 0.125  # Reduce amplitude to 50% for lower volume
    audio = note * amplitude * (2**15 - 1) / np.max(np.abs(note))
    audio = audio.astype(np.int16)

    return audio, sample_rate


def save_to_wav(audio, sample_rate, filename):
    write(filename, sample_rate, audio)


# Slide from a higher frequency to a lower frequency for start and stop sounds
start_end_frequency = 700  # Start at a higher frequency for the start sound
start_start_frequency = 140  # End at a lower frequency

stop_start_frequency = 1000  # Start at a higher frequency for the stop sound
stop_end_frequency = 440  # End at a lower frequency

# Duration of the sound in seconds
duration = 0.15

# Generate and save start sound
start_audio, sample_rate = generate_ping_sound(
    start_start_frequency, start_end_frequency, duration
)
save_to_wav(start_audio, sample_rate, "sound_start.wav")


# Generate and save stop sound
stop_audio, sample_rate = generate_ping_sound(
    stop_start_frequency, stop_end_frequency, duration
)
save_to_wav(stop_audio, sample_rate, "sound_end.wav")
