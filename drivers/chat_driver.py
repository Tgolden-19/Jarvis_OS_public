from openai import OpenAI
import json
import os
import aiofiles
import asyncio
from dotenv import load_dotenv
from .settings import *
import ollama

config = BMOSettings()
model_path = config.get_value('settings_integrations', 'LLM')
use_local=config.get_value('settings_toggles', 'local_llm')

load_dotenv()#load the dot env into the file may want to import into one file 
             #then access as global vars
client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))

DEBUG_MODE = os.getenv("DEBUG_CHAT", 'False').lower() in ('true', '1', 't')

msg_history= []
HISTORY_LENGTH= int(os.getenv("HISTORY_LENGTH"))
MAX_TOKENS= int(os.getenv("MAX_TOKENS"))

# file_lock = asyncio.Lock()
log_queue = asyncio.Queue()

def incoming_msg(text):
    formatted_msg=  {"role": "user", "content": text}
    add_msg(formatted_msg)

def add_msg(msg):
    global msg_history
    if(not DEBUG_MODE ):
        trim_history()
    msg_history.append(msg)
    log_msg(msg)

def trim_history():
    global msg_history
    msg_history = msg_history[-HISTORY_LENGTH:]

def start_long_chat():
    global DEBUG_MODE 
    DEBUG_MODE  = True

def end_long_chat():
    global DEBUG_MODE 
    DEBUG_MODE = False

def generate_response_GPT(user_in:str,system_in:str = "", char_in:str = "", max_tkns:int = MAX_TOKENS):
    global msg_history
    incoming_msg(user_in)
    gpt_in = msg_history
    if system_in !=  "":
        system_msg = {'role': 'system', "content": system_in}
        gpt_in = msg_history + [system_msg]
    if system_in !=  "":
        char_msg = {'role': 'system', "content": char_in}
        gpt_in = gpt_in + [char_msg]
        
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=gpt_in,
        max_tokens=max_tkns,
    )
    add_msg({"role": "assistant", "content": str(response.choices[0].message.content)})

    return str(response.choices[0].message.content)

def load_history():
    global msg_history
    with open(path_chat_log("chat_logs"), 'r') as log_file:
        chat_log = json.load(log_file)
        msg_history.clear()
        recent = chat_log[-HISTORY_LENGTH:]
        msg_history.extend(recent)
        

async def save_to_chat_log():
    log_path = path_chat_log("chat_logs")
    while True:
        msg = await log_queue.get()
        if msg is None:  # Signal to stop
            break

        try:
            async with aiofiles.open(log_path, 'r') as f:
                content = await f.read()
                chat_log = json.loads(content)
        except FileNotFoundError:
            chat_log = []
        except json.JSONDecodeError:
            chat_log = []

        chat_log.append() 

        async with aiofiles.open(log_path, 'w') as f:
            await f.write(json.dumps(chat_log, indent=4))

        log_queue.task_done()

     
    

def path_chat_log(file_name):
        dir_path = os.path.dirname(__file__)
        full_path = os.path.join(dir_path, f"{file_name}.json")
        return full_path

async def log_msg(message):
    await log_queue.put(message)

def generate_response_local(user_in:str,system_in:str = "", char_in:str = "", max_tkns:int = MAX_TOKENS):
    global msg_history
    global model_path
    incoming_msg(user_in)
    gpt_in = msg_history
    if system_in !=  "":
        system_msg = {'role': 'system', "content": system_in}
        gpt_in = msg_history + [system_msg]
    if system_in !=  "":
        char_msg = {'role': 'system', "content": char_in}
        gpt_in = gpt_in + [char_msg]
    response = ollama.chat(model=model_path, messages=msg_history)
    # print(response['message']['content'])
    add_msg({"role": "assistant", "content": str(response['message']['content'])})
    return str(response['message']['content'])

def generate_response(user_in:str,system_in:str = "", char_in:str = "", max_tkns:int = MAX_TOKENS):
    global use_local
    if use_local:
        return generate_response_local(user_in,  system_in, char_in, max_tkns)
    else:
        return generate_response_GPT(user_in, system_in, char_in, max_tkns)

load_history()#loads conversation history