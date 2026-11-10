# import commands.command_center as commands #not ready to test
# import integrations.calendar_mngr as calendar
from datetime import datetime, timedelta
import asyncio
# import keyboard
import signal
import sys

print("testing microphone")
import sounddevice as sd

sd.default.device = 0  # USB PnP Sound Device
sd.default.samplerate = 44100
# sd.check_input_settings()
print(f'devices: {sd.query_devices()}')

# def callback(indata, frames, time, status):
#     if status:
#         print(status)
#     print("Got audio chunk with shape:", indata.shape)

# try:
#     with sd.InputStream(callback=callback):
#         print("Listening for 5 seconds...")
#         sd.sleep(5000)
# except Exception as e:
#     print("Error:", e)

def handle_interrupt(sig, frame):
    print("\n[!] Exiting cleanly...")
    sys.exit(0)

def list_input_devices():
    print("Input devices:")
    for idx, device in enumerate(sd.query_devices()):
        if device['max_input_channels'] > 0:
            print(f"{idx}: {device['name']}")

def record_and_playback(duration=3, fs=44100):
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait()
    print("Recording complete! Playing back...")
    sd.play(recording, fs)
    sd.wait()
    print("Playback finished.")

# list_input_devices()
# record_and_playback()
def test_stt():
    import drivers.whisper_stt as STT
    print("testing microphone with faster whisper")
    speech = STT.stt_loop()
    print(speech)



print("testing LLM STT pipeline on loop")
# signal.signal(signal.SIGINT, handle_interrupt)
def test_stt_llm(stt_looping=False):
    import drivers.whisper_stt as STT
    import drivers.chat_driver as LLM

    print("testing microphone with faster whisper")
    speech = STT.stt_loop()

    print("testing LLM pipeline with stt once")
    response = LLM.generate_response(speech)
    print("ChatGPT says:" + response)
    while stt_looping:
        # if keyboard.is_pressed('Esc'):
        #         print("Exit signal received. Closing the program.")
        #         break 
        speech = STT.stt_loop()
        if speech:
            # LLM.incoming_msg(speech)
            response = LLM.generate_response(speech)
            print("ChatGPT says:" + response)
            
        print("looping again")

def test_anim_gen(stt_looping=False):
    import json
    import drivers.vosk_layer as vosk
    import drivers.chat_driver as LLM
    import drivers.TTS_Driver as TTS

    print("testing microphone with vosk")
    speech = vosk.vosk_stt()

    print("testing LLM pipeline with stt once")
    response = LLM.generate_response(speech)
    print("ChatGPT says:" + response)

    elabs_resp = TTS.gen_audio_timestamps(response)
    print(elabs_resp)
    print(type(elabs_resp))
    temp = elabs_resp.model_dump()
    print(temp)

    #convert the elvenlabs response to real json
    elabs_string = json.dumps(temp, indent=4)
    #save the json for future testing
    with open("/test_audio/elabs.json", "w") as f:
        f.write(elabs_string)

    while stt_looping:
        # if keyboard.is_pressed('Esc'):
        #         print("Exit signal received. Closing the program.")
        #         break 
        speech = vosk.vosk_stt()
        if speech:
            # LLM.incoming_msg(speech)
            response = LLM.generate_response(speech)
            print("ChatGPT says:" + response)
            
        print("looping again")

def test_audio():
    import json
    import drivers.TTS_Driver as TTS
    import drivers.audio_driver as speaker
    import multiprocessing as mp
    from ctypes import c_double, c_int, c_bool

    mute_flag = mp.Value(c_int, 0)
    skip_flag = mp.Value(c_int, 0)
    shared_timestamp = mp.Value(c_double, -1.0)

    with open('./test_audio/elabs.json', 'r') as f:
        elabs = json.load(f)
        anim_dict = TTS.convert_to_shared(elabs)
        timestamp = -1.0
        speaker.audio_playback(shared_timestamp, anim_dict['audio'], mute_flag, skip_flag)
        

def test_animator_elabs():
    import json
    import drivers.visual_driver as animator
    import multiprocessing as mp
    import drivers.vosk_layer as STT
    import commands.command_center as cc
    import drivers.audio_driver as audio_player
    from ctypes import c_double, c_int, c_bool
    import time

    import drivers.TTS_Driver as TTS

    print("testing animator with test data")
    anim_q = mp.Queue()
    # voice_q = mp.Queue()

    # Shared synchronization and control primitives
    shared_timestamp = mp.Value(c_double, 0.0)
    mute_flag = mp.Value(c_int, 0)
    skip_flag = mp.Value(c_int, 0)
    clean_exit = mp.Value(c_bool, False)

    # Shared state for currently active animation/audio
    manager = mp.Manager()
    shared_anim = manager.dict()
    shared_anim["id"] = -1
    shared_anim["audio"] = None
    shared_anim["alignment"] = None

    with open('./test_audio/elabs.json', 'r') as f:
        elabs = json.load(f)
        anim_dict = TTS.command_to_anim(elabs)
        animator_process = mp.Process(
        target=animator.run_process,
        args=(shared_timestamp, anim_q, shared_anim, clean_exit),
        name="Animator_Process"
        )
        audio_process = mp.Process(target=audio_player.run_process,
                                args=(shared_timestamp, shared_anim, mute_flag, skip_flag, clean_exit),
                                  name="AudioPlayer_process")
        animator_process.start()
        audio_process.start()
        anim_q.put(anim_dict)

        try:
            running = True
            # Keep main thread alive while children run
            while running:
                time.sleep(0.5)
                if clean_exit.value:
                    running = False
            while animator_process.is_alive() or audio_process.is_alive():
                time.sleep(0.5)
                print("exiting cleanly and waiting for all process function to terminate normally to ensure no work is lost")
                # Optionally monitor shared state
                # print(f"[MAIN] Anim ID: {shared_anim['id']}, Timestamp: {shared_timestamp.value:.2f}")
            animator_process.terminate()
            audio_process.terminate()

            animator_process.join()
            audio_process.join()
            print("All processes closed")

        except KeyboardInterrupt:
            print("\n[MAIN] Shutdown signal received.")

            # Graceful termination
            animator_process.terminate()
            audio_process.terminate()

            animator_process.join()
            audio_process.join()
            print("[MAIN] All processes stopped cleanly.")

def test_animator():
    import json
    import drivers.visual_driver as animator
    import multiprocessing as mp
    # import drivers.vosk_layer as STT
    # import commands.command_center as cc
    import drivers.audio_driver as audio_player
    from ctypes import c_double, c_int, c_bool
    import time
    import base64

    # import drivers.TTS_Driver as TTS

    print("testing animator with test data")
    anim_q = mp.Queue()
    # voice_q = mp.Queue()

    # Shared synchronization and control primitives
    shared_timestamp = mp.Value(c_double, 0.0)
    mute_flag = mp.Value(c_int, 0)
    skip_flag = mp.Value(c_int, 0)
    clean_exit = mp.Value(c_bool, False)

    # Shared state for currently active animation/audio
    manager = mp.Manager()
    shared_anim = manager.dict()
    shared_anim["id"] = -1
    shared_anim["audio"] = None
    shared_anim["alignment"] = None

    with open('./test_audio/local_tts.json', 'r') as f:
        anim_dict = json.load(f)
        anim_dict['audio'] = base64.b64decode(anim_dict['audio'])
        # print(anim_dict)
        # anim_q.put(anim_dict)
        animator_process = mp.Process(
        target=animator.run_process,
        args=(shared_timestamp, anim_q, shared_anim, clean_exit),
        name="Animator_Process"
        )
        audio_process = mp.Process(target=audio_player.run_process,
                                args=(shared_timestamp, shared_anim, mute_flag, skip_flag, clean_exit),
                                  name="AudioPlayer_process")
        animator_process.start()
        audio_process.start()
        anim_q.put(anim_dict)

        try:
            running = True
            # Keep main thread alive while children run
            while running:
                time.sleep(0.5)
                if clean_exit.value:
                    running = False
            while animator_process.is_alive() or audio_process.is_alive():
                time.sleep(0.5)
                print("exiting cleanly and waiting for all process function to terminate normally to ensure no work is lost")
                # Optionally monitor shared state
                # print(f"[MAIN] Anim ID: {shared_anim['id']}, Timestamp: {shared_timestamp.value:.2f}")
            animator_process.terminate()
            audio_process.terminate()

            animator_process.join()
            audio_process.join()
            print("All processes closed")

        except KeyboardInterrupt:
            print("\n[MAIN] Shutdown signal received.")

            # Graceful termination
            animator_process.terminate()
            audio_process.terminate()

            animator_process.join()
            audio_process.join()
            print("[MAIN] All processes stopped cleanly.")


def test_aligner():
    print("testing aligner")
    # import drivers.phoneme_aligner as phons
    import json
    import drivers.TTS_Driver as TTS
    import drivers.audio_driver as speaker
    import multiprocessing as mp
    from ctypes import c_double, c_int, c_bool

    mute_flag = mp.Value(c_int, 0)
    skip_flag = mp.Value(c_int, 0)
    shared_timestamp = mp.Value(c_double, -1.0)

    with open('./test_audio/elabs.json', 'r') as f:
        elabs = json.load(f)
        anim_dict = TTS.convert_to_shared(elabs)
        # timestamp = -1.0
        # speaker.audio_playback(shared_timestamp, anim_dict['audio'], mute_flag, skip_flag)

def test_local_tts(text="", stt_looping=False):
    import json
    import drivers.vosk_layer as vosk
    import drivers.chat_driver as LLM
    import drivers.TTS_Driver as TTS
    import base64

    response = text
    if text == "":
        print("testing microphone with vosk")
        speech = vosk.vosk_stt()

        print("testing LLM pipeline with stt once")
        response = LLM.generate_response(speech)
        print("ChatGPT says:" + response)

    tts_resp = TTS.command_to_anim(response)
    # print(tts_resp)
    # print(type(tts_resp))
    tts_resp['audio'] = base64.b64encode(tts_resp['audio']).decode("utf-8")
    # print(tts_resp)
    # print(type(tts_resp))

    #convert the elvenlabs response to real json
    anim_string = json.dumps(tts_resp, indent=4)
    #save the json for future testing
    with open("test_audio/local_tts.json", "w") as f:
        f.write(anim_string)

    while stt_looping:
        # if keyboard.is_pressed('Esc'):
        #         print("Exit signal received. Closing the program.")
        #         break 
        speech = vosk.vosk_stt()
        if speech:
            # LLM.incoming_msg(speech)
            response = LLM.generate_response(speech)
            print("ChatGPT says:" + response)
            
        print("looping again")
print("testing speaker")
print("testing commands")

# def test_calendar():
#     cal_name = "personal"

#     try:
#         cal = calendar.load_calendar(cal_name)
#     except FileNotFoundError:
#         cal = calendar.create_calendar(cal_name)

#     now = datetime.now()

#     cal.add_event(
#         cal,
#         summary="Team Meeting",
#         start=now + timedelta(days=1, hours=3),
#         duration_minutes=45,
#         description="Discuss project roadmap",
#         location="Zoom"
#     )

#     calendar.add_event(
#         cal,
#         summary="Doctor Appointment",
#         start=now + timedelta(days=2, hours=9),
#         duration_minutes=30,
#         description="Regular check-up",
#         location="Clinic"
#     )

#     calendar.list_events(cal)

#     calendar.save_calendar(cal_name, cal)

    # Remove an event by UID (copy-paste a real UID from above)
    # remove_event_by_uid(cal, "paste-uid-here")
    # save_calendar(cal_name, cal)

def test_tts():
    import drivers.TTS_Driver as TTS
    print("testing text tts alignment transformer")
    alignment = {
    "characters": ["H","e","l","l","o"," "," ","w","o","r","l","d","!"],
    "character_start_times_seconds": [0,0.1,0.2,0.3,0.4,0.45,0.5,0.6,0.7,0.8,0.9,1.0,1.1],
    "character_end_times_seconds":   [0.1,0.2,0.3,0.4,0.45,0.5,0.55,0.7,0.8,0.9,1.0,1.1,1.2]
    }

    print(TTS.word_alignment(alignment))
    # print(TTS.)

    # Example usage
def test_bmo_vis():
    #function doesnt work due to interaction with multiprocessing
    print("testing BMO visuals and interactions")
    import drivers.visual_driver as vd
    import queue

    vd.run_process(0.0, queue.Queue(10), None, None)



async def note_test():
    print("testing notes integration")
    import integrations.notes as notes
    await notes.list_notes()
    await notes.create_note("meeting", "Don't forget the 2PM meeting", ".txt")
    await notes.create_note("styled", r"{\rtf1\ansi This is \b bold\b0}", ".rtf")
    await notes.list_notes()
    await notes.read_note("meeting.txt")
    await notes.update_note("meeting.txt", "Meeting rescheduled to 3PM")
    await notes.read_note("meeting.txt")
    await notes.delete_note("styled.rtf")
    await notes.list_notes()

if __name__ == "__main__":
    print("running test suite")
    # test_local_tts("testing the local version of TTS options. Here is an example of the quality.")
    test_local_tts("")
    # test_aligner()
    # test_animator()
    # asyncio.run(note_test)
    # test_calendar() #im not sure this is ready yet