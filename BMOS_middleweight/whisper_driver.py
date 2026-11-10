import numpy as np
import sounddevice as sd
import webrtcvad
import queue
import threading
import wave
import time
from scipy.signal import resample
from faster_whisper import WhisperModel

# Settings
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION_MS = 30  # must be 10, 20, or 30 for webrtcvad
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
MAX_SILENCE_FRAMES = int(0.5 * 1000 / FRAME_DURATION_MS)  # 0.5s of silence
CHUNK_PADDING = 0.5  # seconds of pre-speech buffer
MODEL_SIZE = "small"  # "tiny", "base", "small", "medium", "large-v3"

# Initialize
audio_queue = queue.Queue()
vad = webrtcvad.Vad(2)  # aggressiveness: 0–3
model = WhisperModel(MODEL_SIZE, compute_type="float16")  # use "int8" for CPU

# Util: save audio to WAV
def write_wave(path, audio):
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio)

# VAD worker thread
def vad_listener():
    buffer = bytes()
    pre_speech = []
    silence_counter = 0
    recording = False

    while True:
        frame = audio_queue.get()
        if frame is None:
            break

        is_speech = vad.is_speech(frame, SAMPLE_RATE)

        if is_speech:
            if not recording:
                recording = True
                buffer = b''.join(pre_speech)
                print("🎙️ Speech started")
            buffer += frame
            silence_counter = 0
        else:
            if recording:
                silence_counter += 1
                buffer += frame
                if silence_counter > MAX_SILENCE_FRAMES:
                    print("📪 Speech ended")
                    path = f"/tmp/audio_{int(time.time())}.wav"
                    write_wave(path, buffer)
                    threading.Thread(target=transcribe, args=(path,)).start()
                    recording = False
                    buffer = b''
                    pre_speech.clear()
            else:
                pre_speech.append(frame)
                if len(pre_speech) > int((CHUNK_PADDING * 1000) / FRAME_DURATION_MS):
                    pre_speech.pop(0)

# Transcription
def transcribe(path):
    segments, _ = model.transcribe(path, beam_size=5)
    text = ''.join([seg.text for seg in segments])
    print(f"📝 Transcription: {text}")

# Audio input callback
def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    pcm = (indata * 32767).astype(np.int16).tobytes()
    audio_queue.put(pcm)

# Start everything
def main():
    print("Listening with VAD + Whisper. Speak into the mic...\n")
    threading.Thread(target=vad_listener, daemon=True).start()

    with sd.InputStream(channels=CHANNELS, samplerate=SAMPLE_RATE,
                        blocksize=FRAME_SIZE, callback=audio_callback):
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping...")
            audio_queue.put(None)

if __name__ == "__main__":
    main()
