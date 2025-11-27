import requests

SERVER_URL = "http://127.0.0.1:8000"  # Adjust if server is remote
audio_id = None


def start_recording():
    """Send start command to server."""
    global audio_id
    print("Sending start command to server...")
    res = requests.post(f"{SERVER_URL}/start")
    data = res.json()
    audio_id = data.get("audio_id")
    if audio_id:
        print(f"Recording started, audio_id: {audio_id}")
    else:
        print("Failed to start recording:", data)


def stop_recording():
    """Send stop command to server."""
    print("Sending stop command to server...")
    res = requests.post(f"{SERVER_URL}/stop")
    print(res.json().get("message", "Recording stopped"))


def download_audio():
    """Download the recorded audio file from the server (optional)."""
    global audio_id
    print("Downloading audio...")
    res = requests.get(f"{SERVER_URL}/audio/{audio_id}")
    if res.status_code == 200:
        filename = f"downloaded_{audio_id}"
        with open(filename, "wb") as f:
            f.write(res.content)
        print(f"Saved as {filename}")
        return filename
    else:
        print("Failed to download audio:", res.json())
        return None


def play_audio_on_server():
    """Send a request for the server to play the audio."""
    global audio_id
    print("Sending play command to server...")
    res = requests.post(f"{SERVER_URL}/play/{audio_id}")
    print(res.json().get("message", "Playing audio"))


if __name__ == "__main__":
    input("Press ENTER to start recording on the server...")
    start_recording()

    input("Recording... Press ENTER to stop recording.")
    stop_recording()

    # Optionally download and save the audio locally for verification
    download_audio()

    # Play the recorded audio on the server's speakers
    play_audio_on_server()

    print("Test complete.")
