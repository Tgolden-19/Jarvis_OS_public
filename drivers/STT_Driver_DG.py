#local
from deepgram import PrerecordedOptions
#streaming
# from deepgram import LiveOptions, LiveTranscriptionEvents
from dotenv import load_dotenv
from time import sleep
import logging

from deepgram.utils import verboselogs

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

#loading .env file
load_dotenv()

is_finals = []

#local file passing synchronous
def local_STT_test(path):
    response = deepgram.listen.rest.v("1").transcribe_file(
        source=open("path/to/your/audio.wav", "rb"),
        options=PrerecordedOptions(model="nova-3") # Apply other options
    )

#local file async
def local_STT_async(path):
    response = deepgram.listen.rest.v("1").transcribe_file_async(
        source=open(path, "rb"),
        callback_url="https://your-callback-url.com/webhook",
        options=PrerecordedOptions(model="nova-3") # Apply other options
    )

#streaming audio helpers
def on_open(open, **kwargs):
            print("Connection Open")

def on_message(result, **kwargs):
    global is_finals
    sentence = result.channel.alternatives[0].transcript
    if len(sentence) == 0:
        return
    if result.is_final:
        print(f"Message: {result.to_json()}")
        # We need to collect these and concatenate them together when we get a speech_final=true
        # See docs: https://developers.deepgram.com/docs/understand-endpointing-interim-results
        is_finals.append(sentence)

        # Speech Final means we have detected sufficient silence to consider this end of speech
        # Speech final is the lowest latency result as it triggers as soon an the endpointing value has triggered
        if result.speech_final:
            utterance = " ".join(is_finals)
            print(f"Speech Final: {utterance}")
            is_finals = []
        else:
            # These are useful if you need real time captioning and update what the Interim Results produced
            print(f"Is Final: {sentence}")
    else:
        # These are useful if you need real time captioning of what is being spoken
        print(f"Interim Results: {sentence}")

def on_metadata(metadata, **kwargs):
    print(f"Metadata: {metadata}")

def on_speech_started(speech_started, **kwargs):
    print("Speech Started")

def on_utterance_end(utterance_end, **kwargs):
    print("Utterance End")
    global is_finals
    if len(is_finals) > 0:
        utterance = " ".join(is_finals)
        print(f"Utterance End: {utterance}")
        is_finals = []

def on_close(close, **kwargs):
    print("Connection Closed")

def on_error(error, **kwargs):
    print(f"Handled Error: {error}")

def on_unhandled(unhandled, **kwargs):
    print(f"Unhandled Websocket Message: {unhandled}")

#streaming audio

def stream_audio_test():
    try:
        # example of setting up a client config. logging values: WARNING, VERBOSE, DEBUG, SPAM
        # config = DeepgramClientOptions(
        #     verbose=verboselogs.DEBUG, options={"keepalive": "true"}
        # )
        # deepgram: DeepgramClient = DeepgramClient("", config)
        # otherwise, use default config
        deepgram: DeepgramClient = DeepgramClient()

        dg_connection = deepgram.listen.websocket.v("1")


        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

        options: LiveOptions = LiveOptions(
            model="nova-3",
            language="en-US",
            # Apply smart formatting to the output
            smart_format=True,
            # Raw audio format details
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            # To get UtteranceEnd, the following must be set:
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            # Time in milliseconds of silence to wait for before finalizing speech
            endpointing=300,
        )

        addons = {
            # Prevent waiting for additional numbers
            "no_delay": "true"
        }

        print("\n\nPress Enter to stop recording...\n\n")
        if dg_connection.start(options, addons=addons) is False:
            print("Failed to connect to Deepgram")
            return

        # Open a microphone stream on the default input device
        microphone = Microphone(dg_connection.send)

        # start microphone
        microphone.start()

        # wait until finished
        input("")

        # Wait for the microphone to close
        microphone.finish()

        # Indicate that we've finished
        dg_connection.finish()

        print("Finished")
        # sleep(30)  # wait 30 seconds to see if there is any additional socket activity
        # print("Really done!")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return

# Create a websocket connection
connection = deepgram.listen.websocket.v("1")

# Handle transcription events
@connection.on(LiveTranscriptionEvents.Transcript)
def handle_transcript(result):
    print(result.channel.alternatives[0].transcript)

# Start connection with streaming options
connection.start(LiveOptions(model="nova-3", language="en-US"))

# Send audio data
connection.send(open("path/to/your/audio.wav", "rb").read())

# Close when done
connection.finish()