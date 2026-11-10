import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer
from .settings import *

config = BMOSettings()
# import keyboard

# --- Deepgram integration ---------------------------------------------
# import STT_Driver as STT
# -----------------------------------------------------------------------

# -----------------------------------------------------------------------
# Debug helper
# -----------------------------------------------------------------------
DEBUG = True
def debug_print(msg: str):
    """Print only when DEBUG is True."""
    if DEBUG:
        print(msg)

# -----------------------------------------------------------------------
# Vosk setup
# -----------------------------------------------------------------------
print('loading STT model vosk small...')
vosk_model = Model("models/vosk/vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(vosk_model, 16000)
recognizer.SetWords(True)
print('STT model loaded...')

q = queue.Queue()

TRIGGER_PHRASES = ["start transcription", "hey assistant"]
triggered = False

# -----------------------------------------------------------------------
# Sound-device callback
# -----------------------------------------------------------------------
def audio_callback(indata, frames, time, status):
    if status:
        debug_print(f"Audio status: {status}")
    q.put(bytes(indata))

# -----------------------------------------------------------------------
# Listening loop
# -----------------------------------------------------------------------
def listen_for_trigger():
    """Runs until a trigger phrase is detected."""
    global triggered

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        debug_print("Vosk is listening for trigger phrases...\n")

        while True:
            data = q.get()

            # if DEBUG and keyboard.is_pressed("Esc"):
            #     print("manual exit triggered to stop vosk loop")
            #     return
            # Final result available
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                if text:
                    debug_print(f"[FINAL]  {text}")           # <-- always print

                    # Check triggers
                    for phrase in TRIGGER_PHRASES:
                        if phrase in text:
                            debug_print(f"Trigger detected: {phrase}\n")
                            triggered = True
                            return

            #print for interim results used for granular debugging
            # else:
            #     partial = json.loads(recognizer.PartialResult()).get("partial", "")
            #     if partial:
            #         debug_print(f"[PART]   {partial}")        # <-- always print

def vosk_stt(clean_exit=False, playback_flag=None, pause_flag=None)->str:
    """Runs until a trigger phrase is detected."""
    debug_print(f'input device set is: {config.get_input_device()} | has type {type(config.get_input_device())}')
    with sd.RawInputStream(
        samplerate=16000, #do i need to change to 44100
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback,
        device=config.get_input_device()
    ):
        debug_print("Vosk is listening...\n")
        running = True
        while running:
            if clean_exit.is_set():
                running = False
            if playback_flag != None:
                if not playback_flag.is_set():
                    running = False
                    return None
                    # break
            if pause_flag != None:
                if not pause_flag.is_set():
                    running = False
                    return None
                    
            data = q.get()

            # if DEBUG and keyboard.is_pressed("Esc"):
            #     print("manual exit triggered to stop vosk loop")
            #     return
            # Final result available
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                if text:
                    debug_print(f"[FINAL]  {text}")           # <-- always print
                    return text
            #print for interim results used for granular debugging
            # else:
            #     partial = json.loads(recognizer.PartialResult()).get("partial", "")
            #     if partial:
            #         debug_print(f"[PART]   {partial}")        # <-- always print
        return None
def run_trigger_loop():
    """Endless loop: wait for trigger → run Deepgram → repeat."""
    global triggered
    while True:
        triggered = False
        listen_for_trigger()         # blocks until trigger
        # if DEBUG and keyboard.is_pressed("Esc"):
        #     print("manual exit triggered to stop program test")
        #     break
        debug_print("Returned from Deepgram. Restarting trigger loop...\n")

def trigger_loop_elsewhere():
    """single instance of the loop: check for trigger → run Deepgram → return to be looped again by another function"""
    global triggered
    triggered = False
    listen_for_trigger()
    # debug_print("checking for trigger words...")

def run_process(voice_q, playback_flag, clean_exit, pause_flag):
    running = True
    debug_print('speech to text ready, running speech to text...')
    while running:
        if not playback_flag.is_set():
            debug_print("vosk listener muted so audio playback cant be picked up...")
            # continue
        playback_flag.wait()
        if not pause_flag.is_set():
            debug_print('pausing STT...')
        pause_flag.wait()
        stt_output = vosk_stt(clean_exit=clean_exit, playback_flag=playback_flag, pause_flag=pause_flag)
        if stt_output != None:
            voice_q.put(stt_output)
        if clean_exit.is_set():
            running = False

    debug_print('closing speech to text')

if __name__ == "__main__":
    run_trigger_loop()
