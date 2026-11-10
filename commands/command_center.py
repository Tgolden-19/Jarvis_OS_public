import requests
import keyboard
from dotenv import load_dotenv
import os
import json
import asyncio
import drivers.chat_driver as LLM
import drivers.TTS_Driver as TTS
from commands.validators import *
import multiprocessing

load_dotenv()

def file_path(file_name):
    dir_path = os.path.dirname(__file__)
    print(dir_path)
    full_path = os.path.join(dir_path, f"{file_name}.json")
    return full_path

with open(file_path('commands_format'), 'r') as file:
    commands = json.load(file)["commands"]

with open(file_path('triggers'), 'r') as file2:
    triggers =  json.load(file2)


# mic_lock = asyncio.Lock()
# speaker_lock = asyncio.Lock() moving to a hardware file

#both of these existing may be unnecessary
# button_lock = asyncio.Lock()
# input_lock= asyncio.Lock()  moving both to another file

async def get_command(speech):
    for structure in commands:
        for phrase in structure["phrases"]:
            if phrase in speech:
                return structure["commands"]
    return ""

async def activate_STT(speech):
    """I should have labelled this earlier but this was intended to activate a 
    more complex STT like going from vosk to whisper"""
    for phrase in triggers['phrases']:
        if phrase in speech:
            return True
    return False

async def do_command(command):
    print('running command:' + command)
    return

async def deep_talk():
    print('starting deep conversation...')
    return

async def change_lights():
    print('changing lights...')
    return

async def music_manage():
    print('initializing music player api...')

    return

def run_process(voice_queue: multiprocessing.Queue, anim_queue: multiprocessing.Queue, clean_exit):
    running = True
    print('command center ready...')
    while running:
        if not voice_queue.empty():
            command_text = voice_queue.get()
            deep_response = LLM.generate_response(command_text)
            shareable_dict = {'id': -1, 'audio': None, 'alignment': None}
            shareable_dict = TTS.command_to_anim(deep_response)
            # print(shareable_dict)
            anim_queue.put(shareable_dict)

            #TODO preproccess text before sending to LLM to see if LLM interaction can be minimized
        if clean_exit.is_set():
            running = False
    print('command center closing...')


#TODO add a log of every event/command that has completed processing uninterrupted
#TODO add bag of words base processing of commands via strict commands format parsing
    
