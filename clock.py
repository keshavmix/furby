import datetime
import time
import os
import random
import wave
import pyaudio

SOUND_FOLDER = "sounds/clock/"
STYLES = ["A", "B"]
# Add as many intro wav names as you have
FUNNY_INTROS = [
    "intro1", "intro2", "intro3", "intro4", "intro5",
    "intro6", "intro7", "intro8", "intro9"]


def play(name):
    """Play WAV file using PyAudio."""
    filename = os.path.join(SOUND_FOLDER, f"{name}.wav")

    if not os.path.exists(filename):
        print("Missing sound:", filename)
        return

    wf = wave.open(filename, "rb")
    pa = pyaudio.PyAudio()

    # Open audio stream based on WAV file properties
    stream = pa.open(
        format=pa.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True
    )

    # Read and play audio data
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    # Cleanup
    stream.stop_stream()
    stream.close()
    pa.terminate()
    wf.close()


def speak_time():
    now = datetime.datetime.now()

    hour = int(now.strftime("%I"))
    minute = int(now.strftime("%M"))
    ampm = now.strftime("%p")
    
    # ------------------------------
    # 1) PLAY RANDOM FUNNY INTRO
    # ------------------------------
    intro = random.choice(FUNNY_INTROS)
    print("Intro:", intro)
    play(intro)

    style = random.choice(STYLES)
    print("Using style:", style)

    # Styles B, C, D start with "its"
    if style in ["A", "B"]:
        play("its")

    # Hour
    play(str(hour))

    # ----- STYLE A -----
    if style == "A":
        if minute == 0:
            play("oclock")
        else:
            play(str(minute))
            play(ampm)
        return

    # ----- STYLE B -----
    if style == "B":
        if minute == 0:
            play("oclock")
        else:
            play(str(minute))
        play(ampm)
        return


if __name__ == "__main__":
    print("Talking Clock (PyAudio) Started")
    speak_time()
