#THIS IS FROM CHATGPT AT LEAST GIVE IT A ONCE OVER AND SOME THOROUGH TESTINGs
import pyaudio
import webrtcvad
import collections
import numpy as np
import wave
import tempfile
import os
import signal
import sys
from faster_whisper import WhisperModel
# import keyboard
from scipy.signal import resample_poly

# ----------------- Config -----------------
SAMPLE_RATE = 44100
FRAME_DURATION_MS = 30  # 30 ms per frame
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
CHANNELS = 1
FORMAT = pyaudio.paInt16

PRE_SPEECH_FRAMES = int(0.5 * 1000 / FRAME_DURATION_MS)  # 0.5 sec
MAX_SILENCE_FRAMES = int(0.8 * 1000 / FRAME_DURATION_MS)  # 0.8 sec

# ----------------- Setup ------------------
vad = webrtcvad.Vad(2)
model = WhisperModel("tiny.en", compute_type="float32")  # Use "tiny" or "tiny.en" for speed

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=0,
                frames_per_buffer=FRAME_SIZE)

def read_audio_frame():
    return stream.read(FRAME_SIZE, exception_on_overflow=False)

def is_speech(frame):
    if(SAMPLE_RATE == 16000):
        return vad.is_speech(frame, 16000)
    else:
        return vad.is_speech(resample_audio(frame), 16000)

def save_wav(frames):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    raw_audio = b''.join(frames)
    resampled = None
    if(SAMPLE_RATE == 16000):
        resampled = raw_audio
    else:
        resampled = resample_audio(raw_audio)
    wf = wave.open(temp_file.name, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(16000)
    wf.writeframes(resampled)
    wf.close()
    # print(f"[DEBUG] Saved WAV to: {temp_file.name}")
    return temp_file.name

def resample_audio(audio_bytes, orig_rate=44100, target_rate=16000):
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
    resampled = resample_poly(audio_np, target_rate, orig_rate)
    return resampled.astype(np.int16).tobytes()

def transcribe(audio_path):
    segments, _ = model.transcribe(audio_path, beam_size=1)
    return "".join([s.text for s in segments]).strip()

def handle_interrupt(sig, frame):
    print("\n[!] Exiting cleanly...")
    stream.stop_stream()
    stream.close()
    p.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, handle_interrupt)

def stt_loop():
    print("Listening... Press Ctrl+C to stop.")

    ring_buffer = collections.deque(maxlen=PRE_SPEECH_FRAMES)
    speech_buffer = []
    recording = False
    silence_counter = 0

    while True:
        frame = read_audio_frame()
        transcription = None
        # if keyboard.on_press_key("Esc"):
        #     print("doing a clean exit via keyboard enacted loop break")
        #     break
        if len(frame) != FRAME_SIZE * 2:
            continue  # skip incomplete frames

        if not recording:
            ring_buffer.append(frame)

        if is_speech(frame):
            if not recording:
                print("Speech started.")
                speech_buffer.extend(ring_buffer)
                ring_buffer.clear()
                recording = True
            speech_buffer.append(frame)
            silence_counter = 0
        elif recording:
            speech_buffer.append(frame)
            silence_counter += 1

            if silence_counter > MAX_SILENCE_FRAMES:
                print("Speech ended. Transcribing...")
                wav_path = save_wav(speech_buffer)
                try:
                    transcription = transcribe(wav_path)
                    if transcription:
                        print(f" Transcription: {transcription}")

                except Exception as e:
                    print(f"[Error] during transcription: {e}")
                os.remove(wav_path)
                speech_buffer.clear()
                silence_counter = 0
                recording = False
        if transcription:
            break

    return transcription
