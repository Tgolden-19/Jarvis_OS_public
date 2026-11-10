
from .settings import *
import threading
from .audio_receiver import run_server, event_queue
from .face import FaceBase
# import queue
import multiprocessing
import time
from .game_button import Button
from .clock_driver import AlarmClock
import io

from sys import platform
from pygame._sdl2.video import Window
from pygame.locals import * #for the display flags

import os


#set to hardware option on system
# 1. Force SDL to use the ALSA audio driver backend
os.environ["SDL_AUDIODRIVER"] = "alsa"

# 2. Force ALSA to output directly to hardware card 0
os.environ["AUDIODEV"] = "plughw:0"

#THIS VERSION OF THE VISUAL DRIVER USES THE NATIVE PYGAME MIXER FOR AUDIO INSTEAD
# OF SYNCING ON A SEPARATE PROCESS IF IT WORKS THIS IS THE PRIMARY VISUAL AND AUDIO DRIVER
settingsOBJ = BMOSettings()
WINDOW_WIDTH, WINDOW_HEIGHT = settingsOBJ.get_window_size()
AUDIO_DESYNC = 15
recieve_audio = False
#launch the audio reciever server
#foundation code for running STT TTS LLM and Command center over the network instead of onboard
flask_thread = None
if recieve_audio:  
    flask_thread = threading.Thread(target=run_server)
    flask_thread.daemon = True
    flask_thread.start()


class FPSCounter:
    def __init__(self, avg_window=60):
        self.prev_time = time.perf_counter()
        self.fps = 0.0

        self.frame_times = []
        self.avg_window = avg_window

    def tick(self):
        now = time.perf_counter()
        dt = now - self.prev_time
        self.prev_time = now

        if dt > 0:
            self.fps = 1.0 / dt

        self.frame_times.append(self.fps)
        if len(self.frame_times) > self.avg_window:
            self.frame_times.pop(0)

    @property
    def avg_fps(self):
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) / len(self.frame_times)


class Beemo:
    '''this version of Beemo is intended to remove the use of the concurrent 
    audio system that was initially designed to not only be more time accurate 
    but also more accurate for timing animations which turns out is likely not 
    the case because python is just that ill performant'''
    def __init__(self, anim_queue:multiprocessing.Queue, playback_flag=True, clean_exit=False, pause_flag=True, skip_audio=False, mute_flag=False, restart_flag=False, shutdown_flag=False, local_timed=True):
        # setup
        pygame.init()
        pygame.mixer.init(buffer=256)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), SCALED + NOFRAME + FULLSCREEN, 32, vsync=1)
        self.clock = pygame.time.Clock()
        self.running = True
        self.bckgrnd_col = pygame.Color(206, 255, 218, 255)
        self.font = pygame.font.SysFont(settingsOBJ.get_font(), settingsOBJ.get_font_size())
        self.text_col = pygame.Color(0, 0, 0, 255)

        # time tracking for playback of audio
        # self.fps_counter = FPSCounter()
        self.playback = False
        self.local_timed = local_timed
        self.audio_timestamp = -1.0
        self.timestamp = -1.0
        self.anim_queue = anim_queue
        self.curr_anim = {
                'id': -1,
                'audio': None, 
                'alignment': None 
            }
        self.audio = None
        self.anim_start = None
        self.animation_ended = True
        self.channel = None
        self.curr_phoneme_index = 0
        self.prev_timestamp = -1.0
        self.settings_menu = settingsMenu(self.font)
        if pause_flag != None:
            self.pause_broadcast = pause_flag
        self.playback_state = playback_flag
        self.exit_flag = clean_exit
        self.skip_audio = skip_audio
        self.mute = mute_flag
        self.restart = restart_flag
        self.shutdown = shutdown_flag

        # self.button_spacing = 40
        # self.start_y = WINDOW_HEIGHT // 2 - 1.5 * self.button_spacing


        # self.menu_tree = settingsOBJ.get_all_settings()

        # self.main_buttons = self.build_buttons(self.menu_tree['main'])
        #TODO add always present buttons like home, back, save and apply
        #TODO add top banner settings carousel for 'general, video, audio, etc...

        #values only used for debugging
        self.prev_key = 'none'
        self.key_count = 0
        # sprites
        self.face_sprites = pygame.sprite.Group()

        self.face = FaceBase((WINDOW_WIDTH//2, WINDOW_HEIGHT//2), self.face_sprites)

    def run(self, debug_fps=False):
        dt = 0
        bmo_paused = False
        # button_index = 0
        # buttons = self.main_buttons
        # menu_path = [self.menu_tree]
        # current_menu = self.menu_tree
        while self.running:
            if self.exit_flag.is_set():
                self.running = False
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            # select_button = False
            for event in pygame.event.get():
                #TODO add section to allow a button press to clear the animation queue
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        #add physical controller ability to mute audio with button press
                        with self.mute.get_lock():
                            #set BMO to mute
                            self.mute.value = (self.mute.value + 1)%2 #cycle through mute states
                            if self.channel:
                                if self.mute.value == 1:
                                    self.channel.set_volume(0.0)
                                elif self.mute.value == 0:
                                    self.channel.set_volume(settingsOBJ.get_value('settings_audio','Master Volume')/100)
                            
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        print('paused')
                        bmo_paused = not bmo_paused
                        with self.skip_audio.get_lock():
                            self.skip_audio.value = 1
                        pygame.mixer.stop()
                        self.audio_timestamp = -1.0
                        if bmo_paused:
                                #flip mp pause flag to false so other processes wait
                                self.pause_broadcast.clear()
                        else:
                            #free processes from waiting because its not paused anymore
                            self.pause_broadcast.set()
                        
                #The more i write this project the less it makes sense to handle this logic here instead of the main thread
                if bmo_paused:
                    action = self.settings_menu.event_handle(event)
                    # print(action)
                    if type(action) == str:
                        if action == 'resume':
                            bmo_paused = False
                            if bmo_paused:
                                #flip mp pause flag to false
                                self.pause_broadcast.set()
                        if action == 'quit':
                            self.running = False #this may not be necessary because I already have the quit trigger set to self.exit_flag
                            self.exit_flag.set()
                        if action == 'shutdown':
                            print('shutting down whole system')
                            #set system to exit cleanly
                            self.exit_flag.set()
                            if settingsOBJ.get_value('settings_toggles', 'allow_system_shutdown'):
                            #spawn process to shutdown whole computer
                                self.shutdown.set()

                        if action == 'restart':
                            print('restarting bmo...')
                            self.restart.set()
                            #tell main thread to close then spawn new processes

            # fill the screen with a color to wipe away anything from last frame
            self.screen.fill(self.bckgrnd_col)
            self.check_anim_queue()
            mouth_key, eye_key = self.play_anim(dt)
            self.anim_playback_manager()
            # update
            # self.face_sprites.update(dt)
            if bmo_paused:
                self.settings_menu.update(dt)
                self.settings_menu.draw(self.screen)
                # for i in range(len(buttons)):
                #     #TODO change to only draw 5 buttons surrounding the current button index
                #     button = buttons[i]
                #     button.draw(self.screen, button_index == i)
            else:
                self.face.update(dt, eye_key, mouth_key)
                self.face_sprites.draw(self.screen)

            pygame.display.flip()
            if self.anim_start != None:
                self.audio_timestamp = max(0.0, (pygame.time.get_ticks() - self.anim_start - AUDIO_DESYNC)/1000) #current playback time converted to seconds
                # print(self.audio_timestamp)
                # print(self.audio_timestamp)
            if self.audio_timestamp > 0:
                # print('playing back audio activating mute mic...')
                self.playback_state.clear()
            else:
                self.playback_state.set()

            # limits FPS to 30
            # dt is delta time in seconds since last frame, used for framerate-
            # independent physics.
            dt = self.clock.tick(60) / 1000
            fps = self.clock.get_fps()
            if debug_fps:
                print(f"FPS: {fps:.1f}  dt: {dt:.2f} ms")

        self.exit_flag.set()
        pygame.quit()
        exit()

    def check_anim_queue(self):
        """if there are animations in the queue that need to be played it will
        play them in series until the queue is empty (NOTE this does not loop 
        through until the queue is empty it empties the animation queue at a rate
        of once per gameloop if where an animation is not already playing"""
        # assert isinstance(self.curr_anim, dict), "curr_anim must always be the shared dict!"
        if not self.anim_queue.empty() and self.curr_anim['id'] == -1:
            # print(self.anim_queue.qsize())
            temp = self.anim_queue.get()
            print('new animation loading...')
            # print(temp)
            safe_temp = {
                'id': int(temp['id']),
                'audio': temp['audio'],  # is audio bytes
                'alignment': temp['alignment']  # must be a plain list/dict
            }
            # print(safe_temp)
            self.curr_anim['audio'] = safe_temp['audio']
            self.curr_anim['alignment'] = safe_temp['alignment']
            self.curr_anim['id'] = safe_temp['id']
            #load audio to pygame for use in game system instead of concurrency
            self.audio = pygame.mixer.Sound(file=io.BytesIO(safe_temp['audio']))
            #start audio playback
            self.channel = self.audio.play()
            self.animation_ended = False
            self.audio_timestamp = 0.0
            self.anim_start = pygame.time.get_ticks()
    
    def anim_playback_manager(self):
        # print(f' current audio_timestamp: {self.audio_timestamp.value}')
        # temp = self.curr_anim['id']
        # print(f'current animation id: {temp}')

        if not self.animation_ended and self.channel and not self.channel.get_busy():
            self.animation_ended = True 

            #set all animation values to null/no animation
            self.curr_anim['id'] = -1
            self.curr_anim['audio'] = None
            self.curr_anim['alignment'] = None
            self.audio = None
            print("animation is over, removing it from player")
            self.key_count = 0
            self.prev_key = 'none'
            self.anim_start = None
            self.channel = None
            self.audio_timestamp = -1.0
            #stop audio playback
            pygame.mixer.stop()
    
    def play_anim(self, dt, transition_debug=False):
        # assert isinstance(self.curr_anim, dict), "curr_anim must always be the shared dict!"
        eye_key = 'none' #eye keys haven't been implemented yet
        mouth_key = 'none'
        # print(f'playback currently at: {self.audio_timestamp}')
        if self.audio_timestamp < 0:
            self.timestamp = -1.0

        if self.timestamp < 0 and self.prev_timestamp < 0 and self.audio_timestamp >= 0.0 and not self.animation_ended:
            self.timestamp = self.audio_timestamp

        if self.curr_anim['id'] > -1:
            self.timestamp += dt
            mouth_key = self.curr_anim_phon()
            
            # print(f'time ing animation: {self.timestamp}')
            # print(f'associated viseme: {mouth_key}')
            if not mouth_key == self.prev_key and transition_debug:
                print(f'time ing animation: {self.audio_timestamp}')
                print(f'associated viseme: {mouth_key}')
                self.prev_key = mouth_key
                self.key_count += 1
                print(self.key_count)

            if mouth_key == None:
                self.timestamp = -1.0
                self.audio_timestamp = -1.0
            # print(self.audio_timestamp.value)
            # self.anim_playback_manager()
            # if mouth_key == 'none':
            
        return mouth_key, eye_key

    def curr_anim_phon(self):
        if self.curr_anim['id'] == -1 or self.timestamp < 0 or self.audio_timestamp < 0:
            return None
        
        phonemes = self.curr_anim['alignment']['phonemes']
        starts = self.curr_anim['alignment']['starts']
        ends = self.curr_anim['alignment']['ends']

        # print(
        #     len(phonemes),
        #     len(starts),
        #     len(ends)
        # )

        for x in range(0, len(starts)-1):
            #debug for any gaps in the phonemes
            # if ends[x] < starts[x+1] and x < len(starts)-2:
            #     print("GAP", x, ends[x], starts[x+1]) 

            start = starts[x]
            end = ends[x]
            if self.local_timed:
                if self.timestamp >= start and self.timestamp < end:
                    return phonemes[x]
            else:
                if self.audio_timestamp >= start and self.audio_timestamp < end:
                    return phonemes[x]
        return 'none'

    def curr_anim_phon_new(self):
        if self.curr_anim['id'] == -1:
            self.prev_timestamp = None
            self.curr_phoneme_index = 0
            return None  # animation truly over

        phonemes = self.curr_anim['alignment']['phonemes']
        starts = self.curr_anim['alignment']['starts']
        ends = self.curr_anim['alignment']['ends']

        t = self.audio_timestamp

        # First frame of animation
        if self.prev_timestamp is None:
            self.prev_timestamp = t

        prev_t = self.prev_timestamp
        self.prev_timestamp = t

        i = self.curr_phoneme_index

        # Advance while we crossed phoneme boundaries
        while i < len(starts):
            # Did we ENTER this phoneme since last frame?
            if prev_t < starts[i] <= t:
                self.curr_phoneme_index = i
                return phonemes[i]

            # Did we fully CROSS this phoneme in one frame?
            if prev_t < ends[i] and t >= ends[i]:
                self.curr_phoneme_index = i
                return phonemes[i]

            # If time is still before this phoneme, stop
            if t < starts[i]:
                break

            i += 1

        # No new phoneme triggered → keep current
        if self.curr_phoneme_index < len(phonemes):
            return phonemes[self.curr_phoneme_index]

        return phonemes[-1]
    
    def curr_phoneme(self):
        """
        Returns the phoneme(s) whose time interval has been crossed
        """
        phonemes = self.curr_anim['alignment']['phonemes']
        starts = self.curr_anim['alignment']['starts']
        ends = self.curr_anim['alignment']['ends']

        # Find the first phoneme that crossed since last frame
        for i in range(len(starts)):
            if self.prev_timestamp < ends[i] and self.timestamp >= starts[i]:
                key = phonemes[i]
                if key != self.prev_key:
                    self.prev_key = key
                    return key
        return self.prev_key  # keep previous if nothing crossed
    
    def draw_text(self, text, x, y):
        img = self.font.render(text, True, self.text_col)
        self.screen.blit(img, x, y)

    def build_buttons(self, menu):
        buttons = []
        keys = list(menu.keys())

        for i, key in enumerate(keys):
            buttons.append(
                Button(key, self.font, (WINDOW_WIDTH//2, self.start_y + self.button_spacing*i))
            )

        return buttons
    
    def get_current_menu(self, tree, path):
        menu = tree
        for key in path:
            menu = menu[key]
        return menu


#start alarm clock only class
#----------------------------------------------------------------------------------
class ClockBMO:
    def __init__(self):
        # setup
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SCALED + pygame.NOFRAME + pygame.FULLSCREEN, 32, vsync=1)
        #reddit trick below was unsuccessful---------------------
        # fullscreensize = (pygame.display.Info().current_w, pygame.display.Info().current_h) #needs to be before display.set_mode()
        # screen = pygame.display.set_mode((640, 480), SCALED + RESIZABLE, 32) #vsync=1 is optional every time
        # window = Window.from_display_module() #this needs to always be available (not created in a loop)
        # fullscreen = False

        # #later when pressing enter or something in a menu
        # fullscreen = not fullscreen
        # if platform != 'linux':
        #     pygame.dispay.toggle_fullscreen() #works for entering and exiting fullscreen, except in linux
        #     window.position = (fullscreensize[i] / 2 - window.size[i] / 2 for i in range(2))#reset X and Y position of the window to original instead of top left

        # elif fullscreen:
        #     screen = pygame.display.set_mode((640, 480), SCALED + NOFRAME + FULLSCREEN, 32) #all flags are necessary

        # else: #so when exiting fullscreen on linux
        #     pygame.display.toggle_fullscreen() #does work for exiting fullscreen
        #     screen = pygame.display.set_mode((640, 480), SCALED + RESIZABLE, 32)
        #     window = Window.from_display_module() #needs to be done again
        #     window.position = (fullscreensize[i] / 2 - window.size[i] / 2 for i in range(2))#reset X and Y position of the window to original instead of top left
        # pygame.display.toggle_fullscreen()
        # end reddit trick -----------------------------------
        self.clock = pygame.time.Clock()
        self.running = True
        self.bckgrnd_col = pygame.Color(206, 255, 218, 255)
        self.font = pygame.font.SysFont(settingsOBJ.get_font(), settingsOBJ.get_font_size())
        self.text_col = pygame.Color(0, 0, 0, 255)
        # self.time_font = self.font = pygame.font.SysFont(settingsOBJ.get_font(), 50)

        #initialize native audio
        # pygame.mixer.init()
        # alarm_sound = pygame.mixer.Sound("alarm.wav")

        # time tracking for playback of audio
        # self.fps_counter = FPSCounter()
        self.settings_menu = settingsMenu(self.font)
        self.alarm_clock = AlarmClock()

        #values only used for debugging
        self.prev_key = 'none'
        self.key_count = 0
        # sprites
        self.face_sprites = pygame.sprite.Group()

        self.face = FaceBase((WINDOW_WIDTH//2, WINDOW_HEIGHT//2), self.face_sprites)

    def run(self, debug_fps=False):
        dt = 0
        bmo_paused = False
        # button_index = 0
        # buttons = self.main_buttons
        # menu_path = [self.menu_tree]
        # current_menu = self.menu_tree
        while self.running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            # select_button = False
            for event in pygame.event.get():
                #TODO add section to allow a button press to clear the animation queue
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print('paused')
                        bmo_paused = not bmo_paused
                self.alarm_clock.event_handle(event)
                    
                        
                #The more i write this project the less it makes sense to handle this logic here instead of the main thread
                if bmo_paused:
                    action = self.settings_menu.event_handle(event)
                    # print(action)
                    if type(action) == str:
                        if action == 'resume':
                            bmo_paused = False
                        if action == 'quit':
                            self.running = False #this may not be necessary because I already have the quit trigger set to self.exit_flag
                        if action == 'shutdown':
                            print('shutting down whole system(in this version the button has no function different than quit)')
                            #set system to exit cleanly
                            self.running = False
                            if settingsOBJ.get_value('settings_toggles', 'allow_system_shutdown'):
                                #spawn subprocess to shutdown whole computer
                                print('shutting down raspi')

        

                        if action == 'restart':
                            print('restarting bmo...')
                            self.running = False
                            #tell main thread to close then spawn new processes

            # fill the screen with a color to wipe away anything from last frame
            self.screen.fill(self.bckgrnd_col)
            mouth_key, eye_key = self.play_anim(dt)
            # update
            # self.face_sprites.update(dt)
            time_mode = self.alarm_clock.get_mode()

            self.alarm_clock.update()

            # elif time_mode == 2:
            #     self.draw_text('Times are represented in 24hr format')
            if time_mode == 'normal':
                if bmo_paused:
                    self.settings_menu.update(dt)
                    self.settings_menu.draw(self.screen)
                    # for i in range(len(buttons)):
                    #     #TODO change to only draw 5 buttons surrounding the current button index
                    #     button = buttons[i]
                    #     button.draw(self.screen, button_index == i)
                else:
                    self.face.update(dt, eye_key, mouth_key)
                    self.face_sprites.draw(self.screen)
            else:
                # print(time_mode)
                self.alarm_clock.draw(self.screen)

            pygame.display.flip()

            # limits FPS to 30
            # dt is delta time in seconds since last frame, used for framerate-
            # independent physics.
            dt = self.clock.tick(60) / 1000
            fps = self.clock.get_fps()
            if debug_fps:
                print(f"FPS: {fps:.1f}  dt: {dt:.2f} ms")

        pygame.quit()
        exit()

    def play_anim(self, dt, transition_debug=True):
        # assert isinstance(self.curr_anim, dict), "curr_anim must always be the shared dict!"
        eye_key = 'none' #eye keys haven't been implemented yet
        mouth_key = 'none'
        # print(f'playback currently at: {self.audio_timestamp}')

        # print(f'time ing animation: {self.timestamp}')
        # print(f'associated viseme: {mouth_key}')
        if not mouth_key == self.prev_key and transition_debug:
            print(f'time ing animation: {self.audio_timestamp.value}')
            print(f'associated viseme: {mouth_key}')
            self.prev_key = mouth_key
            self.key_count += 1
            print(self.key_count)
            
        return mouth_key, eye_key
    
    def draw_text(self, text, x, y):
        img = self.font.render(text, True, self.text_col)
        self.screen.blit(img, (x, y))

    
# pygame setup
def run_process(anim_queue:multiprocessing.Queue, playback_flag, clean_exit, pause_flag, skip_flag, mute_flag, restart_flag, shutdown_flag):
    enviro = Beemo(anim_queue=anim_queue, playback_flag=playback_flag, clean_exit=clean_exit, 
                   pause_flag=pause_flag, skip_audio=skip_flag, mute_flag=mute_flag,
                   restart_flag=restart_flag, shutdown_flag=shutdown_flag)
    enviro.run()

if __name__ == '__main__':
    run_process()

