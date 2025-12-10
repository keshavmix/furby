from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

# your input file
input_file = "sounds/clock/clock.wav"

# load audio
audio = AudioSegment.from_wav(input_file)

# split when silence is detected
chunks = split_on_silence(
    audio,
    min_silence_len=200,   # adjust if needed (200 ms silence)
    silence_thresh=-40     # adjust based on noise level
)

os.makedirs("sounds/clock/", exist_ok=True)

# Save each chunk as 1.wav, 2.wav, ...
for i, chunk in enumerate(chunks, start=1):
    filename = f"sounds/clock//{i}.wav"
    chunk.export(filename, format="wav")
    print("Saved", filename)

print("Done! Total files:", len(chunks))
