import wave
import pyaudio

def play_wav(path):
    wf = wave.open(path, 'rb')
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

    stream.close()
    pa.terminate()
    
#play_wav("sounds/heyhowareyou.wav")

play_wav("sounds/peppaping_heyhowareyou.wav")
