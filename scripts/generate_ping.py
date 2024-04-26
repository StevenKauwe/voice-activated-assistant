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
save_to_wav(start_audio, sample_rate, "src/audio_files/sound_start.wav")


# Generate and save stop sound
stop_audio, sample_rate = generate_ping_sound(stop_start_frequency, stop_end_frequency, duration)
save_to_wav(stop_audio, sample_rate, "src/audio_files/sound_end.wav")


# Generate a nice program start-up sound
program_start_audio, sample_rate = generate_ping_sound(400, 500, 0.1)
save_to_wav(program_start_audio, sample_rate, "src/audio_files/program_start.wav")


def my_fn(n):
    if n > 300:
        return (510 - n) ** (3 / 2)
    return n ** (3 / 2)


def generate_bell_sound(frequencies, decay_rates, duration, sample_rate=44100):
    # Generate time array
    t = np.linspace(0, duration, int(duration * sample_rate), False)

    # Generate bell sound
    bell_audio = np.zeros_like(t)
    for freq, decay in zip(frequencies, decay_rates):
        bell_audio += np.exp(-decay * t) * np.sin(2 * np.pi * freq * t)

    # Normalize bell sound
    bell_audio = bell_audio / np.max(np.abs(bell_audio))

    return bell_audio


def generate_sound_from_function(func, length, duration, sample_rate=44100):
    # Generate sequence from function
    sequence = np.array([func(i) for i in range(length)], dtype=float)

    # Normalize sequence
    sequence = sequence / np.max(np.abs(sequence))

    # Repeat sequence to fill duration
    sequence = np.tile(sequence, int(np.ceil(duration * sample_rate / length)))

    # Generate time array
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    sequence = sequence[: len(t)]

    # Generate audio data
    audio = np.sin(5 * np.pi * sequence * t)
    audio = audio * np.hanning(len(audio) * 2)[len(audio) : len(audio) * 2]

    # Generate "ding" sound
    # ding_freqs = [830, 1661, 2489, 3322]  # Frequencies for the "ding" sound
    # ding_decays = [5, 7, 9, 11]  # Decay rates for the "ding" sound
    # ding_duration = 1.0  # Duration of the "ding" sound
    ding_freqs = [55, 110, 165, 220]  # Frequencies for the "gong" sound
    ding_decays = [0.5, 0.75, 1, 1.25]  # Decay rates for the "gong" sound
    ding_duration = 2.0  # Duration of the "
    ding_audio = generate_bell_sound(ding_freqs, ding_decays, ding_duration)
    ding_audio = (
        ding_audio * 2 * np.hanning(len(ding_audio) * 2)[len(ding_audio) : len(ding_audio) * 2]
    )

    # Append "bing" sound to audio data
    audio = np.concatenate((audio, ding_audio))

    # Reduce loudness
    amplitude = 0.5  # Reduce amplitude to 50% for lower volume
    audio = audio * amplitude * (2**15 - 1) / np.max(np.abs(audio))
    audio = audio.astype(np.int16)

    return audio, sample_rate


# Generate and save sound
audio, sample_rate = generate_sound_from_function(my_fn, 510, 2, 44100)
save_to_wav(audio, sample_rate, "src/audio_files/startup-audio.wav")

audio, sample_rate = generate_sound_from_function(my_fn, 510, 0, 44100)
save_to_wav(audio[::-1], sample_rate, "src/audio_files/shutdown-audio.wav")
