import os
from pydub import AudioSegment, silence

# ------------ SETTINGS -------------
INPUT_FOLDER = "sounds/clock/intro"      # folder containing wav files
OUTPUT_FOLDER = "sounds/clock/intro/clean_wav/"    # folder for trimmed files
SILENCE_THRESHOLD = -40        # dB, adjust if needed
CHUNK_SIZE = 10                # ms
# -----------------------------------

def trim_silence(sound, silence_threshold=SILENCE_THRESHOLD, chunk_size=CHUNK_SIZE):
    # Trim start
    start_trim = silence.detect_leading_silence(sound, silence_threshold, chunk_size)
    # Trim end
    end_trim = silence.detect_leading_silence(sound.reverse(), silence_threshold, chunk_size)

    duration = len(sound)
    return sound[start_trim:duration-end_trim]

# Create output folder
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Process each WAV file
for filename in os.listdir(INPUT_FOLDER):
    if filename.lower().endswith(".wav"):
        file_path = os.path.join(INPUT_FOLDER, filename)

        # Load audio
        audio = AudioSegment.from_wav(file_path)

        # Trim silence
        trimmed = trim_silence(audio)

        # Save cleaned file
        out_path = os.path.join(OUTPUT_FOLDER, filename)
        trimmed.export(out_path, format="wav")

        print(f"Trimmed: {filename}")

print("All files trimmed successfully!")
