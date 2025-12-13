import datetime
import os
import wave
import pyaudio
import random

SOUND_FOLDER = "sounds/clock/"

# Intro WAV files
INTROS = [
    "dateintro1", "dateintro2", "dateintro3", "dateintro4",
    "dateintro5", "dateintro6", "dateintro7", "dateintro8"
]

# Outro WAV files
OUTROS = [
    "dateoutro1", "dateoutro2", "dateoutro3", "dateoutro4",
    "dateoutro5", "dateoutro6", "dateoutro7", "dateoutro8"
]


def play(name):
    """Play WAV file using PyAudio."""
    filename = os.path.join(SOUND_FOLDER, f"{name}.wav")

    if not os.path.exists(filename):
        print("Missing sound:", filename)
        return

    wf = wave.open(filename, "rb")
    pa = pyaudio.PyAudio()

    stream = pa.open(
        format=pa.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True
    )

    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    pa.terminate()
    wf.close()


def speak_year(year):
    """Speak year as: 2025 = 2 / thousand / 25"""
    year_str = str(year)
    first_digit = int(year_str[0])
    last_three = int(year_str[1:])

    play(str(first_digit))
    play("thousand")
    play(str(last_three))


def speak_date():
    today = datetime.datetime.now()

    # Day name (monday, tuesday…)
    weekday = today.strftime("%A").lower()

    # Date number 1–31 → date1.wav, date2.wav...
    date_num = today.day
    date_file = f"date{date_num}"

    # Month number 1–12 → month1.wav, month2.wav...
    month_num = today.month
    month_file = f"month{month_num}"

    # Year
    year = today.year

    # ------------------------------
    # 1. RANDOM INTRO
    # ------------------------------
    play(random.choice(INTROS))

    # ------------------------------
    # 2. FULL DATE
    # Example:
    # Monday → the → date23 → of → month1 → 2 thousand 25
    # ------------------------------
    play(weekday)
    #play("the")
    play(date_file)
    play("of")
    play(month_file)
    speak_year(year)

    # ------------------------------
    # 3. RANDOM OUTRO
    # ------------------------------
    play(random.choice(OUTROS))


if __name__ == "__main__":
    print("Date Speaker with month1.wav–month12.wav Ready!")
    speak_date()
