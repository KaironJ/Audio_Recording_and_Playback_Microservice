import wave
import threading
import pyaudio
import uuid
import os
import time
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
AUDIO_DIR = "recordings"

os.makedirs(AUDIO_DIR, exist_ok=True)

# Recording State
audio_data = []        # Stores chunks of audio during recording
p = pyaudio.PyAudio()
stream = None
audio_id = None
is_recording = False


# ------------------ Recording Callback ------------------ #
def record_callback(in_data, frame_count, time_info, status):
    # Called repeatedly by PyAudio during recording
    if is_recording:
        audio_data.append(in_data)
        return (None, pyaudio.paContinue)
    else:
        return (None, pyaudio.paComplete)

    
# ------------------ Play Callback ------------------ #
def play_callback(wf):
    """Return a callback function to stream audio from a wave file."""
    def callback(in_data, frame_count, time_info, status):
        data = wf.readframes(frame_count)
        if len(data) == 0:
            return (None, pyaudio.paComplete)
        return (data, pyaudio.paContinue)
    return callback

# ------------------ Endpoints ------------------ #
@app.post("/start")
def start_recording():
    """Start recording from the server microphone."""
    global stream, audio_data, audio_id, is_recording

    if is_recording:
        return {"error": "Already recording"}

    audio_data = []
    audio_id = f"{uuid.uuid4()}.wav"
    is_recording = True

    # Open a non-blocking input stream with callback
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=record_callback)
    stream.start_stream()

    return {"message": "Recording started", "audio_id": audio_id}


@app.post("/stop")
def stop_recording():
    """Stop recording and save the WAV file."""
    global stream, audio_id, is_recording

    if not is_recording:
        return {"error": "Not recording"}

    is_recording = False
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save recorded chunks to WAV
    file_path = os.path.join(AUDIO_DIR, audio_id)
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(audio_data))

    return {"message": "Recording stopped", "file": audio_id}


@app.get("/audio/{file_name}")
def get_audio(file_name: str):
    """Return stored audio file to client."""
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav", filename=file_name)
    return {"error": "File not found"}


@app.post("/play/{file_name}")
def play_audio(file_name: str):
    """Play a stored audio file on the server speakers asynchronously."""
    file_path = os.path.join(AUDIO_DIR, file_name)
    if not os.path.exists(file_path):
        return {"error": "Audio not found"}

    def _play():
        wf = wave.open(file_path, 'rb')
        p_play = pyaudio.PyAudio()

        # Open non-blocking output stream using callback
        stream_play = p_play.open(format=p_play.get_format_from_width(wf.getsampwidth()),
                                  channels=wf.getnchannels(),
                                  rate=wf.getframerate(),
                                  output=True,
                                  stream_callback=play_callback(wf))
        stream_play.start_stream()

        # Wait for playback to finish
        while stream_play.is_active():
            time.sleep(0.1)

        stream_play.stop_stream()
        stream_play.close()
        p_play.terminate()

    # Run playback in background so endpoint returns immediately
    threading.Thread(target=_play, daemon=True).start()
    return {"message": f"Playing audio {file_name}"}
