import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer
import keyboard


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
vosk_model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(vosk_model, 16000)
recognizer.SetWords(True)

q = queue.Queue()

TRIGGER_PHRASES = ["", ""]
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

            if DEBUG and keyboard.is_pressed("Esc"):
                print("manual exit triggered to stop vosk loop")
                return
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

def run_trigger_loop():
    """Endless loop: wait for trigger → run commands → repeat."""
    global triggered
    while True:
        triggered = False
        listen_for_trigger()         # blocks until trigger
        if DEBUG and keyboard.is_pressed("Esc"):
            print("manual exit triggered to stop program test")
            break
        debug_print("Returned from Deepgram. Restarting trigger loop...\n")

def trigger_loop_elsewhere():
    """single instance of the loop: check for trigger with vosk → run command association → return to be looped again by another function"""
    global triggered
    triggered = False
    listen_for_trigger()
    # debug_print("checking for trigger words...")

# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------
if __name__ == "__main__":
    run_trigger_loop()
