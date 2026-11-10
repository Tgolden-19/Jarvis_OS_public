import multiprocessing as mp
import base64, time, io
from ctypes import c_double
from pydub import AudioSegment
import sounddevice as sd
import numpy as np
from .settings import *

sd.default.device = 1
config = BMOSettings()

def audio_playback(shared_timestamp, audio_bytes, mute_flag, skip_flag, audio_format="wav"):
    """This function is a streamed realtime audio playback manager and 
    is only designed to work in multiprocessing and concurrency
    if you want to use one built for sequential use use the _seq version because
    the parameters of this function are all the concurrent/multiprocessing equivalents
    of sequential/native types and definitions which are not intercompatible nor interchangeable
    """
    print('audio started...')
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format)
    samples = np.array(audio.get_array_of_samples()).astype(np.int16)
    if audio.channels == 2:
        samples = samples.reshape((-1, 2))

    # print(sd.query_devices())
    sample_rate = audio.frame_rate
    # print(audio.channels)

    playback_stream = sd.OutputStream(
        samplerate=sample_rate, 
        device=config.get_output_device(), 
        channels=audio.channels, 
        dtype='int16')
    
    playback_stream.start()
    start = time.perf_counter()
    blocksize = 4096
    idx = 0
    muted_block = np.zeros((blocksize, audio.channels), dtype=np.int16) \
                  if audio.channels > 1 else np.zeros(blocksize, dtype=np.int16)

    while idx < len(samples):
        # print(shared_timestamp)
        if skip_flag.value == 1 or skip_flag.value == 2:
            print("[Audio] Skip signal received — ending playback early.")
            break
        
        end = idx + blocksize
        block = samples[idx:end]

        if mute_flag.value == 1:
            playback_stream.write(muted_block[:len(block)])
        else:
            playback_stream.write(block)

        idx = end
        shared_timestamp.value = time.perf_counter() - start

    playback_stream.stop()
    playback_stream.close()
    shared_timestamp.value = -1.0
    with skip_flag.get_lock():
        skip_flag.value = 0
    print('audio ended...')

def audio_playback_seq_old(shared_timestamp:float, audio_bytes, mute_flag:int=0, skip_flag:int=0):
    """this is a realtime audio playback system designed to take in audio in 
    bytes and play them to the default outpu device set since its sequential all
    native types are used since concurrency and race conditions are not a concern"""

    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format='mp3')
    samples = np.array(audio.get_array_of_samples()).astype(np.int16)
    if audio.channels == 2:
        samples = samples.reshape((-1, 2))

    # print(sd.query_devices())
    sample_rate = audio.frame_rate
    print(audio.channels)

    playback_stream = sd.OutputStream(samplerate=sample_rate, device=1, channels=audio.channels, dtype='int16')
    playback_stream.start()
    start = time.perf_counter()
    blocksize = 4096
    idx = 0
    muted_block = np.zeros((blocksize, audio.channels), dtype=np.int16) \
                  if audio.channels > 1 else np.zeros(blocksize, dtype=np.int16)

    while idx < len(samples):
        # print(shared_timestamp)
        if skip_flag == 1:
            print("[Audio] Skip signal received — ending playback early.")
            break
        
        end = idx + blocksize
        block = samples[idx:end]

        if mute_flag == 1:
            playback_stream.write(muted_block[:len(block)])
        else:
            playback_stream.write(block)

        idx = end
        with shared_timestamp.get_lock():
            shared_timestamp = time.perf_counter() - start

    playback_stream.stop()
    playback_stream.close()
    shared_timestamp = -1.0
    skip_flag = 0

def audio_playback_new(shared_timestamp, audio_np: np.ndarray, 
                       mute_flag, skip_flag,
                       sample_rate: int = 16000, channels: int = 1):
    """
    Real-time sequential audio playback system.
    Accepts a float32 numpy array (audio_np) instead of bytes.
    Plays in blocks, supports mute and skip flags.
    """

    # Ensure correct dtype
    audio = audio_np.astype(np.float32)

    # Handle mono/stereo
    if channels == 2 and audio.ndim == 1:
        audio = np.stack([audio, audio], axis=-1)
    elif channels == 1 and audio.ndim == 2 and audio.shape[1] == 2:
        audio = audio.mean(axis=1)

    blocksize = 4096
    idx = 0

    # Precompute muted block
    muted_block = np.zeros((blocksize, channels), dtype=np.float32) if channels > 1 else np.zeros(blocksize, dtype=np.float32)

    with sd.OutputStream(samplerate=sample_rate, channels=channels, dtype='float32') as playback_stream:
        start = time.perf_counter()
        while idx < len(audio):
            if skip_flag.value == 1:
                print("[Audio] Skip signal received — ending playback early.")
                break

            end = idx + blocksize
            block = audio[idx:end]

            if mute_flag.value == 1:
                playback_stream.write(muted_block[:len(block)])
            else:
                playback_stream.write(block)

            idx = end

            # Update shared timestamp
            with shared_timestamp.get_lock():
                shared_timestamp.value = time.perf_counter() - start

    # Mark finished
    with shared_timestamp.get_lock():
        shared_timestamp.value = -1.0
    with skip_flag.get_lock():
        skip_flag.value = 0

def manage_playback():
    pass


def audio_to_float32(audio_source, target_sr=16000):
    """
    Convert audio to mono float32 waveform at target sample rate.
    
    Parameters:
        audio_source: str, Path to file OR BytesIO
        target_sr: int, desired sampling rate (default 16 kHz)
        
    Returns:
        np.ndarray: 1D float32 array in range [-1, 1]
    """
    # Load audio
    audio_segment = AudioSegment.from_file(audio_source)
    
    # Convert to mono
    audio_segment = audio_segment.set_channels(1)
    
    # Convert sample rate
    audio_segment = audio_segment.set_frame_rate(target_sr)
    
    # Convert to numpy float32
    audio_np = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
    
    # Normalize to [-1, 1]
    max_val = np.iinfo(audio_segment.array_type).max
    audio_np /= max_val
    
    return audio_np


def run_process(shared_timestamp, shared_anim, mute_flag, skip_flag, clean_exit, pause_flag):
    running = True
    while running:
        pause_flag.wait()
        if not shared_anim['id'] == -1:
            # print(shared_anim['id'])
            audio_np = shared_anim['audio']
            print("loading audio from current animation")
            # print(audio_bytes)
            audio_playback(shared_timestamp, audio_np, mute_flag, skip_flag)
            shared_anim['id'] = -1
            shared_anim['audio'] = None
            shared_anim['alignment'] = None
        if clean_exit.is_set():
            running = False
            with skip_flag.get_lock():
                skip_flag.value = 1