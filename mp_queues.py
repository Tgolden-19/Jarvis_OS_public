import multiprocessing as mp
VOICE_QUEUE = mp.Queue()
ANIMATION_QUEUE  = mp.Queue()

def queue_command(speech: str):
    VOICE_QUEUE.put(speech)

def get_command()->str:
    if VOICE_QUEUE.empty():
        return None
    return VOICE_QUEUE.get()

def queue_animation(anim):
    ANIMATION_QUEUE.put()

def get_animation():
    if ANIMATION_QUEUE.empty():
        return None
    return ANIMATION_QUEUE.get()