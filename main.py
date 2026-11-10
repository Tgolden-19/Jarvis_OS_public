# import commands.command_center as commander
# import drivers.vosk_layer as STT
# import drivers.visual_driver as animator
import multiprocessing as mp
# import drivers.vosk_layer as STT
# import commands.command_center as cc
# import drivers.audio_driver as audio_player
from ctypes import c_double, c_int, c_bool
import time
from drivers.settings import BMOSettings
import subprocess
import drivers.visual_driver as animator

config = BMOSettings()
# import keyboard
# import nltk
# from mp_queues import ANIMATION_QUEUE, VOICE_QUEUE
# nltk.download()

# anim_q = mp.Queue()
# voice_q = mp.Queue()
# shared_timestamp = mp.Value(c_double, 0.0)
# mute_flag = mp.Value(c_int, 0)
# skip_flag = mp.Value(c_int, 0)

# #deploy shared memory for the current running animation so both processes are on the same page
# shared_anim = mp.Manager().dict()
# shared_anim["id"] = -1
# shared_anim["audio"] = None
# shared_anim["alignment"] = None

def run_all():
    import drivers.vosk_layer as STT
    import commands.command_center as cc
    import drivers.audio_driver as audio_player
    # Queues for inter-process communication
    anim_q = mp.Queue()
    voice_q = mp.Queue()

    # Shared synchronization and control primitives
    shared_timestamp = mp.Value(c_double, -1.0)
    mute_flag = mp.Value(c_int, 0)
    skip_flag = mp.Value(c_int, 0)
    clean_exit = mp.Event()
    pause_flag = mp.Event()
    restart_flag = mp.Event()
    shutdown_flag = mp.Event()
    game_index = mp.Value(c_int, -1)

    # Shared state for currently active animation/audio
    manager = mp.Manager()
    shared_anim = manager.dict()
    shared_anim["id"] = -1
    shared_anim["audio"] = None
    shared_anim["alignment"] = None

    # Launch concurrent subsystems
    # tts_process = mp.Process(
    #     target=TTS.run_process,
    #     args=(anim_q, shared_timestamp, shared_anim, clean_exit),
    #     name="TTS_Process"
    # )

    game_process = mp.Process(
        target=animator.run_process,
        args=(shared_timestamp, anim_q, shared_anim, clean_exit, pause_flag, skip_flag, mute_flag, restart_flag, shutdown_flag),
        name="game_process"
    )

    stt_process = mp.Process(target=STT.run_process, 
                             args=(voice_q, clean_exit, shared_timestamp, pause_flag), 
                             name="STT_Process")
    
    audio_process = mp.Process(target=audio_player.run_process,
                                args=(shared_timestamp, shared_anim, mute_flag, skip_flag, clean_exit, pause_flag),
                                  name="AudioPlayer_process")
                                  
    comm_center_process = mp.Process(target=cc.run_process,
                                     args=(voice_q, anim_q, clean_exit),
                                     name='CommandCenter_process')

    # Start all processes
    stt_process.start()
    game_process.start()
    audio_process.start()
    comm_center_process.start()

    print("[MAIN] TTS and Animator processes started.")
    print("[MAIN] Press Ctrl+C to stop...")

    try:
        running = True
        # Keep main thread alive while children run
        while running:
            time.sleep(0.5)
            if clean_exit.is_set():
                running = False
            if restart_flag.is_set():
                #do not need to forcefully terminate anymore
                # game_process.terminate()
                # stt_process.terminate()
                # audio_process.terminate()
                # comm_center_process.terminate()

                #tell all process to close cleanly
                clean_exit.set()

                game_process.join()
                stt_process.join()
                audio_process.join()
                comm_center_process.join()

                #unset the clean exit event before it closes the whole program
                clean_exit.clear()

                #stop from restarting again
                restart_flag.clear()

                #re-initialize the processes exactly as they were
                game_process = mp.Process(
                    target=animator.run_process,
                    args=(shared_timestamp, anim_q, shared_anim, clean_exit, pause_flag, skip_flag, mute_flag, restart_flag, shutdown_flag),
                    name="game_process"
                )

                stt_process = mp.Process(target=STT.run_process, 
                                        args=(voice_q, clean_exit, shared_timestamp, pause_flag), 
                                        name="STT_Process")
                
                audio_process = mp.Process(target=audio_player.run_process,
                                            args=(shared_timestamp, shared_anim, mute_flag, skip_flag, clean_exit, pause_flag),
                                            name="AudioPlayer_process")
                                            
                comm_center_process = mp.Process(target=cc.run_process,
                                                args=(voice_q, anim_q, clean_exit),
                                                name='CommandCenter_process')
                
                
                #re start all processes
                stt_process.start()
                game_process.start()
                audio_process.start()
                comm_center_process.start()

            if shutdown_flag.is_set() and config.get_value('settings_toggles', 'allow_system_shutdown'): 
                #TODO the second check is redundant and will be reevaluated at a later date
                print('shutting off hardware')
                subprocess.call(['shutdown', '-h', '45'], shell=False)
            else: 
                print('do not have permission to shutdown the whole system so only closing BMO')



            if not stt_process.is_alive() or not game_process.is_alive() or not audio_process.is_alive() or not comm_center_process.is_alive():
                print("a BMO process crashed and therefore so did BMO")
                running = False
                clean_exit.set()
        # while stt_process.is_alive() or game_process.is_alive() or audio_process.is_alive() or comm_center_process.is_alive():
        #     time.sleep(0.5)
        #     print("exiting cleanly and waiting for all process function to terminate normally to ensure no work is lost")
        #     # Optionally monitor shared state
        #     # print(f"[MAIN] Anim ID: {shared_anim['id']}, Timestamp: {shared_timestamp.value:.2f}")
        # game_process.terminate()
        # stt_process.terminate()
        # audio_process.terminate()
        # comm_center_process.terminate()

        game_process.join()
        stt_process.join()
        audio_process.join()
        comm_center_process.join()
        print("All processes closed")

    except KeyboardInterrupt:
        print("\n[MAIN] Shutdown signal received.")

        # Graceful termination
        game_process.terminate()
        stt_process.terminate()
        audio_process.terminate()
        comm_center_process.terminate()

        game_process.join()
        stt_process.join()
        audio_process.join()
        comm_center_process.join()
        print("[MAIN] All processes stopped cleanly.")
    except Exception as e:
        print("\n[MAIN] Shutdown signal received.")
        print('an error propogated in the program/process manager')

        # Graceful termination
        game_process.terminate()
        stt_process.terminate()
        audio_process.terminate()
        comm_center_process.terminate()

        game_process.join()
        stt_process.join()
        audio_process.join()
        comm_center_process.join()
        print("[MAIN] All processes stopped cleanly.")
    if not stt_process.is_alive() or not game_process.is_alive() or not audio_process.is_alive() or not comm_center_process.is_alive():
        print("a BMO process crashed and therefore so did BMO crashed")
        clean_exit.set()


def run_all_new():
    import drivers.vosk_layer as STT
    import commands.command_center as cc
    import drivers.vis_audio_driver_alt as game
    # Queues for inter-process communication
    anim_q = mp.Queue()
    voice_q = mp.Queue()

    # Shared synchronization and control primitives
    shared_timestamp = mp.Value(c_double, -1.0)
    mute_flag = mp.Value(c_int, 0)
    skip_flag = mp.Value(c_int, 0)
    clean_exit = mp.Event()
    pause_flag = mp.Event()
    pause_flag.set()# set it by default to applications know to continue
    restart_flag = mp.Event()
    shutdown_flag = mp.Event()
    playback_flag = mp.Event()
    playback_flag.set()
    game_index = mp.Value(c_int, -1)

    # Shared state for currently active animation/audio
    manager = mp.Manager()
    shared_anim = manager.dict()
    shared_anim["id"] = -1
    shared_anim["audio"] = None
    shared_anim["alignment"] = None

    # Launch concurrent subsystems
    # tts_process = mp.Process(
    #     target=TTS.run_process,
    #     args=(anim_q, shared_timestamp, shared_anim, clean_exit),
    #     name="TTS_Process"
    # )

    game_process = mp.Process(
        target=game.run_process,
        args=(anim_q, playback_flag, clean_exit, pause_flag, skip_flag, mute_flag, restart_flag, shutdown_flag),
        name="game_process"
    )

    stt_process = mp.Process(target=STT.run_process, 
                             args=(voice_q, playback_flag, clean_exit, pause_flag), 
                             name="STT_Process")
    
    # audio_process = mp.Process(target=audio_player.run_process,
    #                             args=(shared_timestamp, shared_anim, mute_flag, skip_flag, clean_exit, pause_flag),
    #                               name="AudioPlayer_process")
                                  
    comm_center_process = mp.Process(target=cc.run_process,
                                     args=(voice_q, anim_q, clean_exit),
                                     name='CommandCenter_process')

    # Start all processes
    stt_process.start()
    game_process.start()
    # audio_process.start()
    comm_center_process.start()

    print("[MAIN] TTS and Animator processes started.")
    print("[MAIN] Press Ctrl+C to stop...")

    try:
        running = True
        # Keep main thread alive while children run
        while running:
            time.sleep(0.5)
            if clean_exit.is_set():
                running = False
            if restart_flag.is_set():
                #do not need to forcefully terminate anymore
                # game_process.terminate()
                # stt_process.terminate()
                # audio_process.terminate()
                # comm_center_process.terminate()

                #tell all process to close cleanly
                clean_exit.set()

                game_process.join()
                stt_process.join()
                # audio_process.join()
                comm_center_process.join()

                #unset the clean exit event before it closes the whole program
                clean_exit.clear()

                #stop from restarting again
                restart_flag.clear()

                #re-initialize the processes exactly as they were
                game_process = mp.Process(
                    target=game.run_process,
                    args=(anim_q, playback_flag, clean_exit, pause_flag, skip_flag, mute_flag, restart_flag, shutdown_flag),
                    name="game_process"
                )

                stt_process = mp.Process(target=STT.run_process, 
                                        args=(voice_q, playback_flag, clean_exit, pause_flag), 
                                        name="STT_Process")
                
                # audio_process = mp.Process(target=audio_player.run_process,
                #                             args=(shared_timestamp, shared_anim, mute_flag, skip_flag, clean_exit, pause_flag),
                #                             name="AudioPlayer_process")
                                            
                comm_center_process = mp.Process(target=cc.run_process,
                                                args=(voice_q, anim_q, clean_exit),
                                                name='CommandCenter_process')
                
                
                #re start all processes
                stt_process.start()
                game_process.start()
                # audio_process.start()
                comm_center_process.start()

            if shutdown_flag.is_set() and config.get_value('settings_toggles', 'allow_system_shutdown'): 
                #TODO the second check is redundant and will be reevaluated at a later date
                print('shutting off hardware')
                subprocess.call(['shutdown', '-h', '45'], shell=False)
            elif shutdown_flag.is_set(): 
                print('do not have permission to shutdown the whole system so only closing BMO')



            if not stt_process.is_alive() or not game_process.is_alive() or not comm_center_process.is_alive():
                print("a BMO process crashed and therefore so did BMO")
                running = False
                clean_exit.set()
        # while stt_process.is_alive() or game_process.is_alive() or audio_process.is_alive() or comm_center_process.is_alive():
        #     time.sleep(0.5)
        #     print("exiting cleanly and waiting for all process function to terminate normally to ensure no work is lost")
        #     # Optionally monitor shared state
        #     # print(f"[MAIN] Anim ID: {shared_anim['id']}, Timestamp: {shared_timestamp.value:.2f}")
        # game_process.terminate()
        # stt_process.terminate()
        # audio_process.terminate()
        # comm_center_process.terminate()

        game_process.join()
        stt_process.join()
        # audio_process.join()
        comm_center_process.join()
        print("All processes closed")

    except KeyboardInterrupt:
        print("\n[MAIN] Shutdown signal received.")

        # Graceful termination
        game_process.terminate()
        stt_process.terminate()
        # audio_process.terminate()
        comm_center_process.terminate()

        game_process.join()
        stt_process.join()
        # audio_process.join()
        comm_center_process.join()
        print("[MAIN] All processes stopped cleanly.")
    except Exception as e:
        print("\n[MAIN] Shutdown signal received.")
        print('an error propogated in the program/process manager')

        # Graceful termination
        game_process.terminate()
        stt_process.terminate()
        # audio_process.terminate()
        comm_center_process.terminate()

        game_process.join()
        stt_process.join()
        # audio_process.join()
        comm_center_process.join()
        print("[MAIN] All processes stopped cleanly.")
    if not stt_process.is_alive() or not game_process.is_alive() or not comm_center_process.is_alive():
        print("a BMO process crashed and therefore so did BMO crashed")
        clean_exit.set()


def run_animator():
    # import drivers.visual_driver as animator
    # Queues for inter-process communication
    anim_q = mp.Queue()
    voice_q = mp.Queue()

    # Shared synchronization and control primitives
    shared_timestamp = mp.Value(c_double, -1.0)
    mute_flag = mp.Value(c_int, 0)
    skip_flag = mp.Value(c_int, 0)
    clean_exit = mp.Event()
    pause_flag = mp.Event()
    restart_flag = mp.Event()
    shutdown_flag = mp.Event()
    game_index = mp.Value(c_int, -1)

    # Shared state for currently active animation/audio
    manager = mp.Manager()
    shared_anim = manager.dict()
    shared_anim["id"] = -1
    shared_anim["audio"] = None
    shared_anim["alignment"] = None

    game_process = mp.Process(
        target=animator.run_process,
        args=(shared_timestamp, anim_q, shared_anim, clean_exit, pause_flag, skip_flag, mute_flag, restart_flag, shutdown_flag),
        name="game_process"
    )
    game_process.start()

    try:
        running = True
        # Keep main thread alive while children run
        while running:
            time.sleep(0.5)
            if clean_exit.is_set():
                running = False
            if not game_process.is_alive():
                print("animator crashed")
                running = False
                clean_exit.set()
            if restart_flag.is_set():
                print("restarting the animator")
                #tell all processes to stop
                clean_exit.set()
                #close the processes with a clean stop
                game_process.join()
                #stop event from ending main program
                clean_exit.clear()
                #stop from restarting again
                restart_flag.clear()

                #reinitialize process
                game_process = mp.Process(
                    target=animator.run_process,
                    args=(shared_timestamp, anim_q, shared_anim, clean_exit, pause_flag, skip_flag, mute_flag, restart_flag, shutdown_flag),
                    name="game_process"
                )
                #restart process
                game_process.start()
        #redundant code on the function of multiprocessing join
        # while game_process.is_alive():
        #     time.sleep(0.5)
        #     print("exiting cleanly and waiting for all process function to terminate normally to ensure no work is lost")
        #     # Optionally monitor shared state
        #     # print(f"[MAIN] Anim ID: {shared_anim['id']}, Timestamp: {shared_timestamp.value:.2f}")
        # game_process.terminate()
        if shutdown_flag.is_set() and config.get_value('settings_toggles', 'allow_system_shutdown'): 
                #TODO the second check is redundant and will be reevaluated at a later date
                print('shutting off hardware')
                subprocess.call(['shutdown', '-h', '45'], shell=False)
        else: 
            print('do not have permission to shutdown the whole system so only closing BMO')



        game_process.join()
        print("All processes closed")

    except KeyboardInterrupt:
        print("\n[MAIN] Shutdown signal received.")

        # Graceful termination
        game_process.terminate()
        

        game_process.join()
        print("[MAIN] All processes stopped cleanly.")

    except Exception as e:
        print("\n[MAIN] Unexpected error occurred:")
        # traceback.print_exc()

        # Graceful termination on error
        if game_process.is_alive():
            game_process.terminate()
            game_process.join()

        print("[MAIN] Processes terminated due to error. Exiting cleanly.")

    if not game_process.is_alive():
        print("animator crashed")
        # running = False
        clean_exit.set()

if __name__ == "__main__":
    if config.get_value('settings_toggles', 'clock_only'):
        print('only displaying the clock version of BMO')
        clock = animator.ClockBMO()
        clock.run()
        
    else:
        # Using 'spawn' for cross-platform compatibility
        mp.set_start_method("spawn", force=True)
        # run_all() #old deprecated version of the main run and manager
        run_all_new()
        # run_animator()
#This file will be used to spawn processes and run all the necessary features 
# "locally" entirely in python

#TODO add ability to use the config to change to the use of a golang server instead 
# of python multiprocessing