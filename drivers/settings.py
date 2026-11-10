import pygame 
from os.path import join, isfile 
import os
import json
from sounddevice import query_devices
from .game_button import Button


# self.WINDOW_WIDTH, self.WINDOW_HEIGHT = 1280, 720
class BMOSettings():
    def __init__(self):
        self.file_path = 'settings.json'
        self.settings = get_defaults()
        if isfile(self.file_path):
            self.load_from_file(self.file_path)

        self.general = self.settings['settings_general']
        self.audio =  self.settings['settings_audio']
        self.video = self.settings['settings_video']
        self.toggles = self.settings['settings_toggles']
        self.integrations = self.settings['settings_integrations']
        # self.window_width, self.window_height = self.get_window_size()
        # self.ref_rect = self.ref_rect = pygame.FRect((200, 150),(0,0))

        # vert_spacing = 40
        # start_y = self.WINDOW_HEIGHT // 2 - 1.5 * vert_spacing

        # self.main_buttons = [
        #     Button("Resume", font, (self.WINDOW_WIDTH // 2, start_y)),
        #     Button("Settings", font, (self.WINDOW_WIDTH // 2, start_y + vert_spacing)),
        #     Button("Restart", font, (self.WINDOW_WIDTH // 2, start_y + 2 * vert_spacing)),
        #     Button("Quit", font, (self.WINDOW_WIDTH // 2, start_y + 3 * vert_spacing)),
        #     Button("Shutdown", font, (self.WINDOW_WIDTH // 2, start_y + 4 * vert_spacing)),
        # ]

    def get_window_size(self):
        '''
        gets the window size dimensions from the settings/configs returns in W(width), H(height)
        '''
        screen_dim = self.video['Resolution']
        return screen_dim[0], screen_dim[1]

    def audio_output(self):
        '''
        return the index that the current audio output is set to
        '''
        return self.audio['output device']

    def audio_input(self):
        '''
        returns the index that the audio input is set to'''
        return self.audio['input_device']
    
    def convert_to_json(self):
        '''converts the current settings object to json format to be saved 
        to the settings.json file or whatever settings file the user chooses file'''
        settings = {'general':self.general,
                        'audio':self.audio,
                        'video':self.video,
                        'toggles':self.toggles,
                        'integrations':self.integrations}
        return settings
        
    def load_from_file(self, f_path='settings.json'):
        if isfile(f_path):
            with open('settings.json', 'r') as settings_file:
                base_menu = json.load(settings_file)
                self.settings = base_menu
                self.general = base_menu['settings_general']
                self.audio =  base_menu['settings_audio']
                self.video = base_menu['settings_video']
                self.toggles = base_menu['settings_toggles']
                self.integrations = base_menu['settings_integrations']
        else:
            print('this config preset/file does not exist or cannot be found where you have specified it try regenerating the default settings file and replaciing it directly')

    def save_to_file(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.settings, f)

    def generate_settings_file(self):
        '''
        creates the json file for all settings configs and saves defaults
        '''
        base_settings = get_defaults()
        with open(self.file_path, 'w') as f:
            json.dump(base_settings, f)

    def reset_defaults(self):
        '''
        resets the entire settings file to the defaults
        '''
        base_menu = get_defaults()
        self.general = base_menu['settings_general']
        self.audio =  base_menu['settings_audio']
        self.video = base_menu['settings_video']
        self.toggles = base_menu['settings_toggles']
        self.integrations = base_menu['settings_integrations']
        self.save_to_file()
    
    # def get_main_buttons(self):
    #     return self.main_buttons
    
    def get_font(self):
        return self.general['Font']
    
    def get_font_size(self):
        return self.general['Font Size']
    
    def get_general(self):
        return self.general
    
    def get_audio(self):
        return self.audio
    
    def get_video(self):
        return self.video
    
    def get_toggles(self):
        return self.toggles
    
    def get_integrations(self):
        return self.integrations
        
    def get_all_settings(self)->dict:
        return self.settings
    
    def get_menu(self, menu_id:str):
        return self.settings[menu_id]
    
    def get_value(self, menu:str, key:str):
        return self.settings[menu][key]
    
    def set_value(self, menu:str, key:str, value):
        self.settings[menu][key] = value
        #updates internal references to reflect new value because i tweaked out
        # when writing this class and i need to refactor it... 
        # I've been staring at this program too long T-T
        self.general = self.settings['settings_general']
        self.audio =  self.settings['settings_audio']
        self.video = self.settings['settings_video']
        self.toggles = self.settings['settings_toggles']
        self.integrations = self.settings['settings_integrations']


    def get_input_device(self):
        return self.get_audio()['Input Device']
    
    def get_output_device(self):
        return self.get_audio()['Output Device']
    
    def set_menu_to_defaults(self, menu):
        defaults = get_defaults()
        #return current menu to default options unsaved
        menu_defaults = defaults[menu]
        self.settings[menu] = menu_defaults
        #re-eveluate all class variables
        self.general = self.settings['settings_general']
        self.audio =  self.settings['settings_audio']
        self.video = self.settings['settings_video']
        self.toggles = self.settings['settings_toggles']
        self.integrations = self.settings['settings_integrations']

        


    
    # def event_handle(self, event):
    #     """
    #     DO NOT USE
    #     Ill remove it whenever I do a full refactor and make sure nothing breaks when its removed
        
    #     :param self: Description
    #     :param event: Description
    #     """
    #     bmo_paused, running = True
    #     select_button = False
    #     if event.key == pygame.K_DOWN:
    #         button_index = (button_index + 1) % len(buttons)
    #     if event.key == pygame.K_UP:
    #         button_index = (button_index - 1) % len(buttons)
    #     if event.key == pygame.K_RETURN:
    #         select_button = True
    #     for i in range(len(buttons)):
    #         button = buttons[i]
    #         if button.is_clicked(event) or (select_button and button_index == i):
    #             if button.text == "Resume":
    #                 print("resuming BMO")
    #                 bmo_paused = False
    #             elif button.text == "Settings":
    #                 print("Open settings")
    #             elif button.text == "Restart":
    #                 print("Restarting")
    #             elif button.text == "Quit":
    #                 running = False
    #                 #clean_exit.value = True
    #                 # sys.exit()
    #             elif button.text == "Shutdown":
    #                 print("shutting down system")
    #     return bmo_paused, running



def get_defaults():
    #TODO flatten into a table instead of tree
    default_settings = {"main": {
                                    "Resume": 'resume',
                                    "Settings": "settings",
                                    'Games':'game_library',
                                    "Restart": 'restart',
                                    "Shutdown": 'shutdown',
                                    "Quit": 'quit'
                                },

                        "settings": {
                                    "General": "settings_general",
                                    "Audio": "settings_audio",
                                    "Video": "settings_video",
                                    "Toggles":"settings_toggles",
                                    "Integrations":"settings integrations",
                                },

                        "settings_general": {
                                    "Font": "settings_font",
                                    "Font Size": 14
                                },

                        "settings_audio": {
                                    "Input Device": 0,
                                    "Output Device": 1,
                                    "Master Volume": 100
                                },

                        "settings_video": {
                                    "Fullscreen": 0,
                                    "Resolution": [640, 480]
                                },
                        "settings_toggles":{
                            "eye_scaling":False,
                            "local_llm":False,
                            "allow_system_shutdown":False,
                            'clock_only':True,
                            'head_move':True,
                            'random_expressions':True
                            #TODO add other visual toggles
                            #TODO add toggles for local vs disributed system for each process/thread
                        },
                        "settings_integrations":{
                            "HomeKit":"homekit_settings",
                            "LLM":"model name and path to your choice of local LLM"
                            #TODO add integration settings references here
                        },
                        'game_library':{
                            'example_lib':'your/path/here'
                        }
}
    return default_settings

class settingsMenu():
    """
    An object for managing interaction and visuals of the settings menu
    """
    def __init__(self, font):
        self.settingsObj = BMOSettings()
        settings_directory = self.settingsObj.get_all_settings()
        self.menus = settings_directory #flat menu directory
        self.curr_menu = self.settingsObj.get_menu('main')
        self.menu_path = ['main']
        self.button_index = 0
        self.carousel_index = 0
        self.nav_index = 0
        self.in_carousel = False
        self.in_nav = False
        self.WINDOW_WIDTH, self.WINDOW_HEIGHT = self.settingsObj.get_window_size()
        self.font = font
        self.options = []

        self.popup_open = False
        self.popup = Popup(font,'nothing to see here yet', center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))

        #create bar to separate carousel menu from regular menu
        self.bottom_bar = pygame.FRect(0,0, 600, 4)
        self.bottom_bar.center = (self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT-60)

        #create bar to separate regular menu from navbar
        self.top_bar = pygame.FRect(0,0, 600, 4)
        self.top_bar.center = (self.WINDOW_WIDTH//2, 60)

        
        self.vert_spacing = 40
        self.start_y = self.WINDOW_HEIGHT // 2 - 2.5 * self.vert_spacing
        
        self.horiz_spacing = 60
        self.nav_start_x = self.WINDOW_WIDTH // 2 - 1.5 * self.horiz_spacing

        self.carousel_start_x = self.WINDOW_WIDTH // 2 - (len(self.menus['main'])-1)/2 * self.horiz_spacing

        #Start building out menu buttons for visuals and interactions

        #make the bottom menu navigator
        self.nav_buttons = []
        self.gen_nav_buttons()

        #build carousel buttons
        self.menu_carousel = []
        self.gen_carousel()

        #build menu buttons
        self.menu_buttons = self.build_buttons(self.curr_menu)


    def draw_text(self, text, x, y):
        img = self.font.render(text, True, self.text_col)
        self.screen.blit(img, x, y)


    def build_buttons(self, menu, debug=False):
        """
        function to build all buttons from the given menu where menu is a dictionary/key:value set
        """
        #TODO build buttons that are used to alter value and not traverse to show the value with the text
        buttons = []
        keys = list(menu.keys())
        if debug:
            print(keys)

        for i, key in enumerate(keys):
            value = ''
            temp = type(menu[key])
            if temp == int:
                value = f': {(menu[key])}'
            elif temp == bool:
                if menu[key]:
                    value = ': T'
                else:
                    value = ': F'
            elif temp == str:
                value = ''


            buttons.append(
                Button(key+value, self.font, (self.WINDOW_WIDTH//3, self.start_y + self.vert_spacing*i))
            )

        return buttons
    
    def update_buttons(self, debug=False):
        """
        function to build all buttons from the given menu where menu is a dictionary/key:value set
        """
        if debug:
            print(f'available keys: {len(self.curr_menu)}, available buttons: {len(self.menu_buttons)}')

        for i, key in enumerate(self.curr_menu.keys()):
            if debug:
                print(f'{i}, {key}')

            value = ''
            temp = type(self.curr_menu[key])
            if temp == int:
                value = f': {(self.curr_menu[key])}'
            elif temp == bool:
                if self.curr_menu[key]:
                    value = ': T'
                else:
                    value = ': F'
            elif temp == str:
                value = ''        
            temp_text = key+value
            button = self.menu_buttons[i]
            if debug:
                print(f'old text: {button.text}')
                print(f'new text: {temp_text}')
            button.update_text(temp_text)

    def update_menus(self, debug=False):
        if debug:
            print(f'old menu: {self.curr_menu}')
        self.curr_menu = None
        self.menus = None
        self.curr_menu = self.settingsObj.get_menu(self.menu_path[-1])
        self.menus = self.settingsObj.get_all_settings()
        if debug:
            print(f'new menu: {self.curr_menu}')

    def gen_options_buttons(self, options, debug=True):
        options_buttons = []
        for x, option in enumerate(options):
            text = f'option {x}: {option}'
            if debug:
                print(text)
            options_buttons.append(Button(text, self.font, ((self.WINDOW_WIDTH//3)*2, self.start_y+self.vert_spacing*x)))
        return options_buttons
    
    def build_game_menu(self, debug=False):
        menu = self.settingsObj.get_menu('game_library')
        paths = list(menu.keys())
        print(paths)
        #TODO add walk through all directories in the library settings and create buttons from them
        pass

    
    def get_current_menu_tree(self, tree, path):
        """
        (DEPRECATED) using flattened directories
        function for getting menus from a tree directory rather than a flat one
        
        :param self: this object
        :param tree: the menu tree
        :param path: path to selected menu
        """
        menu = tree
        for key in path:
            menu = menu[key]
        return menu
    
    @staticmethod
    def get_output_devices_list(debug=False):
        """
        Returns a list of names for all available audio output devices.
        """
        # Get a list of all available audio devices as a DeviceList object
        devices = query_devices()
        
        output_devices = []
        # Iterate through the devices and check if they have output channels
        for device in devices:
            if device['max_output_channels'] > 0:
                if debug:
                    print('device has no channels you have been warned')
                # Append the device name to the list
                output_devices.append(device['name'])
        return output_devices
    
    def event_handle(self, event):
        """
        function to handle events/menu interaction
        
        :param self: Description
        :param event: Description
        """
        #i way overcomplicated this logic but rather than start over I stubbornly locked in and made it work T-T
        select_button = False
        choice = None
        if event.type == pygame.KEYDOWN:
            if self.popup_open:
                #i think this should essentially result in a "freeze" of the system until a choice is picked
                choice = self.popup.handle_event(event)
                if choice != None:
                    self.popup_open = False
                else:
                    return 'wait'
            if event.key == pygame.K_DOWN:
                self.button_index = (self.button_index + 1)
                if self.button_index >= len(self.menu_buttons):
                    self.in_nav = True
                if self.in_carousel:
                    self.in_nav = False
                    self.button_index = 0
                self.in_carousel = False
            if event.key == pygame.K_UP:
                self.button_index = (self.button_index - 1)
                if self.button_index < 0:
                    self.in_carousel = True
                if self.in_nav:
                    self.button_index = len(self.menu_buttons)-1
                    self.in_carousel = False
                self.in_nav = False
                self.nav_index = 0
            if event.key == pygame.K_RETURN:
                print('select this button')
                select_button = True
            if self.button_index >= 0:
                self.in_carousel = False
            if self.button_index < len(self.menu_buttons):
                self.in_nav = False
            if event.key == pygame.K_LEFT:
                #TODO make it capable of navigating out of options menu

                #move in horizontal menus
                if self.in_nav:
                    self.nav_index = (self.nav_index - 1) % len(self.nav_buttons)
                if self.in_carousel:
                    self.carousel_index = (self.carousel_index - 1) % len(self.menu_carousel)
            if event.key == pygame.K_RIGHT:
                #TODO make it capable of navigating into options menu

                #move in horizontal menus
                if self.in_nav:
                    self.nav_index = (self.nav_index + 1) % len(self.nav_buttons)
                if self.in_carousel:
                    # self.menu_path = []
                    self.carousel_index = (self.carousel_index + 1) % len(self.menu_carousel)
        #TODO when changing values using button change menu to only hold 1 button and its value
        #TODO add capability to change values without typing it (this may conflict with menu navigation)
        if self.in_nav:
            # print('using nav menu')
            for i in range(len(self.nav_buttons)):
                button = self.nav_buttons[i]
                button_label = button.text.lower()
                if button.is_clicked(event) or (select_button and self.nav_index == i):
                    if button_label == 'back':
                        print('going to previous menu')

                        if len(self.menu_path) > 1:
                            print(self.menu_path[-1])
                            self.menu_path.pop()
                            print(self.menu_path[-1])
                            self.curr_menu = self.menus[self.menu_path[-1]]
                            self.menu_buttons = self.build_buttons(self.curr_menu)
                            self.button_index = 0
                        else:
                            print('user hasnt changed menus yet and keeps trying to go back :/')
                    if button_label == 'home':
                        print('going to main menu')
                        self.button_index = 0
                        self.curr_menu = self.menus['main']
                        self.menu_path.append('main')
                    if button_label == 'save':
                        # print('saving all current settings please restart to apply them')
                        self.popup_open = True
                        self.popup.update_text('this will save all current settings \n please restart to apply them...\n Do you understand?')
                        if choice == 'yes':
                            self.settingsObj.save_to_file()
                            self.popup_open = False
                        elif choice == 'no':
                            print('updated settings not saved')
                            self.popup_open = False
                        #TODO display that in order to update settings in active use BMO needs to restart
                    if button_label == 'defaults':
                        # print('reseting page settings to defaults if youve modified this page in any way please save the settings file as a backup before hitting save')
                        self.popup_open = True
                        self.popup.update_text('reseting just this page to default settings \n I recommend backing up your config file before saving \n in the event of undesired results\n Confirm?')
                        if choice == 'yes':
                            menu_key = self.menu_path[-1]
                            self.settingsObj.set_menu_to_defaults(menu_key)
                            self.update_menus()
                            self.update_buttons()
                            self.popup_open = False
                        elif choice == 'no':
                            self.popup_open = False



        elif(self.in_carousel):
            # print('in menu shorcut carousel')
            shortcuts = self.settingsObj.get_menu('main')
            for i in range(len(self.menu_carousel)):
                button = self.menu_carousel[i]
                button_label = button.text.lower()
                if button.is_clicked(event) or (select_button and self.carousel_index == i):
                    if button_label == 'resume': #in ["resume","restart", "quit", "shutdown"]:
                            return button_label
                    if button_label == 'shutdown':
                        self.popup_open = True
                        self.popup.update_text('If the toggle is set, this will result in the entire system shutting down\n Are you sure this is the deired result?')
                        if choice == 'yes':
                            self.popup_open = False
                            return button_label
                        else:
                            return 'wait'
                    if button_label == 'quit':
                        self.popup_open = True
                        self.popup.update_text('if you accept this will close BMO entirely and revery any unsaved changes.\n Is that ok?')
                        if choice == 'yes':
                            self.popup_open = False
                            return button_label
                        else:
                            return 'wait'
                    if button_label == 'restart':
                        self.popup_open = True
                        self.popup.update_text('if you accept this will close BMO entirely.\n This will revert any unsaved changes.\n It will then relaunch normally.\n Is that ok?')
                        if choice == 'yes':
                            self.popup_open = False
                            return button_label
                        else:
                            return 'wait'

                    # print(f'going to menu {shortcuts[button.text]}')
                    self.menu_path.append(shortcuts[button.text])
                    self.curr_menu = self.menus[self.menu_path[-1]]

                    #rebuild buttons an regular menu
                    self.menu_buttons = self.build_buttons(self.curr_menu)
                    self.button_index = 0
                    

        else:
            for i in range(len(self.menu_buttons)):
                button = self.menu_buttons[i]
                #normalize text (this didnt end up having any real purpose but was used in implementation anyways)
                button_label = button.text.lower()
                key = list(self.curr_menu.keys())[i]
                curr_value = self.curr_menu[key]

                #the purpose of this area is to enable savvy users to implement 
                # displayable options buttons when a button is hovered 
                # IN THE CASE IT HAS OPTIONS INSTEAD OF A PRIMITIVE VALUE
                # feel free to use the options area otherwise but im not a sociopath so I wont
                if self.button_index == i:
                    # print(key)
                    if key.lower() in ['input device', 'output device']:
                        #display device options
                        # print('initializing options for input and output devices')
                        #generating them every refresh seems stupid
                        #TODO figure out how to generate them once then delete them when you switch
                        if len(self.options) <= 0:
                            # print('options have not already been made available to display so now adding them')
                            temp_options = self.get_output_devices_list()
                            # print(len(temp_options))
                            self.options = self.gen_options_buttons(temp_options)
                            # print(len(self.options))
                    else:
                        self.options = []
                    # else:
                    #     self.options = []
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            #should I add a cooldown so It doesnt jump really far?
                            curr_value -= 1

                            #set lower limits to value changes
                            if key.lower() == 'font size':
                                curr_value = max(10, curr_value)
                            if key.lower() == 'master volume':
                                curr_value = max(0, curr_value)
                            #end lower limits

                            self.settingsObj.set_value(self.menu_path[-1], key, curr_value)
                            #update current menu and all menus
                            self.update_menus()
                            #update button display
                            self.update_buttons()

                        if event.key == pygame.K_RIGHT:
                            curr_value += 1
                            #set upper limits to values
                            if key.lower() == 'font size':
                                curr_value = min(40, curr_value)
                            if key.lower() == 'master volume':
                                curr_value == min(100, curr_value)
                            #end upper limits

                            self.settingsObj.set_value(self.menu_path[-1], key, curr_value)
                            #update current menu and all menus
                            self.update_menus()
                            #update button display
                            self.update_buttons()
                        
                    if button.is_clicked(event) or (select_button):
                        if type(self.curr_menu[key]) == int:
                            print('change integer value')
                            curr_value += 1
                            self.settingsObj.set_value(self.menu_path[-1], key, curr_value)
                            #update current menu and all menus
                            self.update_menus()
                            #update button display
                            self.update_buttons()

                        elif type(self.curr_menu[key]) == bool:
                            print('toggling value')
                            self.settingsObj.set_value(self.menu_path[-1], key, not self.curr_menu[button.text])
                            #update current menu and all menus
                            self.update_menus
                            #update button display
                            self.update_buttons()

                        elif type(self.curr_menu[key]) == str:
                            # print(button_label)
                            if button_label == 'resume': #in ["resume","restart", "quit", "shutdown"]:
                                return button_label
                            if button_label == 'shutdown':
                                self.popup_open = True
                                self.popup.update_text('If the toggle is set, this will result in the entire system shutting down\n Are you sure this is the deired result?')
                                if choice == 'yes':
                                    self.popup_open = False
                                    return button_label
                                else:
                                    return 'wait'
                            if button_label == 'quit':
                                self.popup_open = True
                                self.popup.update_text('if you accept this will close BMO entirely.\n This will revert any unsaved changes.\n Is that ok?')
                                if choice == 'yes':
                                    self.popup_open = False
                                    return button_label
                                else:
                                    return 'wait'
                            if button_label == 'restart':
                                self.popup_open = True
                                self.popup.update_text('if you accept this will close BMO entirely and revery any unsaved changes.\n It will then relaunch normally.\n Is that ok?')
                                if choice == 'yes':
                                    self.popup_open = False
                                    return button_label
                                else:
                                    return 'wait'


                            print('go to next menu')
                            self.menu_path.append(self.curr_menu[key])
                            self.curr_menu = self.menus[self.menu_path[-1]]
                            # print(self.curr_menu)
                            self.menu_buttons = self.build_buttons(self.curr_menu)
                            self.button_index = 0
                            return 'wait'
            if len(self.options) > 0:
                # print('options are available to click')
                for i, button in enumerate(self.options):
                    if button.is_clicked(event):
                        #use clicked/selected value to overwrite current value
                        key = list(self.curr_menu.keys())[self.button_index]
                        self.settingsObj.set_value(self.menu_path[-1], key, i)

                        #update menus
                        self.update_menus()
                        #update button display
                        self.update_buttons()
        return 'wait'
    
    def gen_nav_buttons(self):
        _, win_h = self.settingsObj.get_window_size()
        self.nav_buttons = [
            Button('back', self.font, (self.nav_start_x, win_h - 30)),
            Button('home', self.font, (self.nav_start_x + self.horiz_spacing, win_h - 30)),
            Button('save', self.font, (self.nav_start_x + self.horiz_spacing*2, win_h - 30)),
            Button('defaults', self.font, (self.nav_start_x + self.horiz_spacing*3, win_h - 30))
        ]

    def gen_carousel(self):
        _, win_h = self.settingsObj.get_window_size()
        #TODO add buttons for general, audio, video, toggles, integrations
        shortcuts = self.settingsObj.get_menu('main')
        for i in range(len(shortcuts.keys())):
            key = list(shortcuts.keys())[i]
            button = Button(key, self.font, (self.carousel_start_x + i*self.horiz_spacing, 30))
            self.menu_carousel.append(button)

    def update(self, dt, debug=False):
       #i dont think theres anything to update every frame its all conditional so event handle would do it
       pass

    def draw(self, screen, debug= False):
        #draw the bars to seperate the carousel and navbar
        pygame.draw.rect(screen, (0,0,0), self.bottom_bar)

        pygame.draw.rect(screen, (0,0,0), self.top_bar)

        #draw the nav bar
        for i in range(len(self.nav_buttons)):
            button = self.nav_buttons[i]
            button.draw(screen, i == self.nav_index and self.in_nav)
        
        #draw the carousel
        for i in range(len(self.menu_carousel)):
            button = self.menu_carousel[i]
            button.draw(screen, i == self. carousel_index and self.in_carousel)

        #this makes sense but looks convoluted and counter intuitive. what is fix?
        # print(len(self.menu_path))
        # print(self.menu_path[0])

        #draw options if button has options
        if len(self.options) > 0:
            if debug:
                print('options are available, now displaying them')
            for i, button in enumerate(self.options):
                button.draw(screen, False)

        if self.menu_path[-1] != 'main' and len(self.menu_buttons) > 5:
            if debug:
                print('menu has more buttons than 5 using pages to represent buttons')
            page_num = self.button_index // 5
            for i in range(page_num*5, (page_num*5)+5):
                button_to_disp = self.menu_buttons[i]
                button_to_disp.draw(screen, self.button_index == i)
        else:
            for i in range(len(self.menu_buttons)):
                if debug:
                    print('menu is a normal menu displaying it normally')
                self.menu_buttons[i].draw(screen, self.button_index == i)
        if self.popup_open:
            self.popup.draw(screen)


class Popup:

    def __init__(self, font, text, width=320, height=180, center=(0,0), 
        popup_color=(206, 255, 218), 
        border_color=(0, 0, 0),
        border_width=4,
        padding=10):
        self.text = text
        self.font = font
        self.popup_color = popup_color
        self.border_color = border_color
        self.border_width = border_width
        self.padding = padding
        self.text_color = (0,0,0)
        self.center_pos = center
        self.on_yes = True
        # self.font = pygame.font.SysFont(None, 36)

        self.rect = pygame.FRect(0,0,width,height)
        self.rect.center = center

        self.yes_button = Button('yes', self.font, (self.rect.bottomleft[0]+80, self.rect.bottomleft[1]-40))
        self.no_button  = Button('no', self.font, (self.rect.bottomright[0]-80, self.rect.bottomright[1]-40))

    def update_text(self, text):
        self.text = text
        self._create_surfaces()
    
    def _create_surfaces(self):
        # Render text
        self.text_surface = self.font.render(self.text, True, self.text_color)
        # text_rect = self.text_surface.get_rect()

        width = self.rect.width
        height = self.rect.height

        # Create popup rect
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = self.center_pos

        # Store inner rect (area inside border)
        self.inner_rect = pygame.Rect(
            self.rect.left + self.border_width,
            self.rect.top + self.border_width,
            self.rect.width - self.border_width * 2,
            self.rect.height - self.border_width * 2
        )
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            print("doing inner popup navigation")
            if event.key == pygame.K_RIGHT:
                self.on_yes = not self.on_yes
            if event.key == pygame.K_LEFT:
                self.on_yes = not self.on_yes
            if event.key == pygame.K_RETURN:
                if self.on_yes:
                    return 'yes'
                else: 
                    return 'no'
        if self.yes_button.is_clicked(event):
            return 'yes'

        if self.no_button.is_clicked(event):
            return 'no'

        return None

    def draw(self, screen):

        # overlay
        # overlay = pygame.Surface(self.screen.get_size())
        # # overlay.set_alpha(150)
        # overlay.fill((0,0,0))
        # self.screen.blit(overlay,(0,0))

        # popup box border
        pygame.draw.rect(screen,self.border_color,self.rect)
        pygame.draw.rect(screen,self.popup_color, self.inner_rect)

        # text
        text_surface = self.font.render(self.text, True, (0,0,0))
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.y + 50))
        screen.blit(text_surface, text_rect)

        # buttons
        self.yes_button.draw(screen, self.on_yes)
        self.no_button.draw(screen, not self.on_yes)


class GameLibrary:
    def __init__(self, library_dict, font,
                 start_x=20, center_start_y=200,
                 item_height=40, indent=20, visible_slots=6):

        self.library_dict = library_dict
        self.font = font

        self.start_x = start_x
        self.center_start_y = center_start_y
        self.item_height = item_height
        self.indent = indent

        self.visible_slots = visible_slots

        self.scroll_index = 0
        self.libraries = []
        self.ui_elements = []

    # ------------------------
    # LOAD LIBRARIES
    # ------------------------
    def load_libraries(self):
        self.libraries.clear()

        for lib_name, path in self.library_dict.items():
            lib_data = {
                "name": lib_name,
                "expanded": True,
                "items": []
            }

            if not os.path.exists(path):
                continue

            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith((".exe", ".lnk")):
                        full_path = os.path.join(root, file)

                        lib_data["items"].append({
                            "name": os.path.splitext(file)[0],
                            "path": full_path
                        })

            self.libraries.append(lib_data)

    # ------------------------
    # BUILD FLAT LIST
    # ------------------------
    def build_flat_list(self):
        flat_list = []

        for i, lib in enumerate(self.libraries):
            flat_list.append({
                "type": "header",
                "name": lib["name"],
                "index": i,
                "expanded": lib["expanded"]
            })

            if lib["expanded"]:
                for item in lib["items"]:
                    flat_list.append({
                        "type": "item",
                        "name": item["name"],
                        "path": item["path"]
                    })

        return flat_list

    # ------------------------
    # SCROLLING (BY SLOT)
    # ------------------------
    def scroll(self, direction):
        flat_list = self.build_flat_list()
        max_index = max(0, len(flat_list) - self.visible_slots)

        self.scroll_index += direction
        self.scroll_index = max(0, min(self.scroll_index, max_index))

    # ------------------------
    # DRAW (ONLY 6 SLOTS)
    # ------------------------
    
    # ------------------------
    # EVENTS
    # ------------------------
    def event_handle(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll(-event.y)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            for element in self.ui_elements:
                if element["button"].check_click(mouse_pos):
                    data = element["data"]

                    if data["type"] == "header":
                        self.toggle_library(data["index"])

                    elif data["type"] == "item":
                        self.launch(data["path"])

                    break

    # ------------------------
    # ACTIONS
    # ------------------------
    def toggle_library(self, index):
        self.libraries[index]["expanded"] = not self.libraries[index]["expanded"]

    def update(self, dt):
        pass

    def draw(self, screen):
        self.ui_elements.clear()

        flat_list = self.build_flat_list()
        visible_items = flat_list[self.scroll_index:self.scroll_index + self.visible_slots]

        y = self.center_start_y

        for element in visible_items:
            if element["type"] == "header":
                text = f"[{'-' if element['expanded'] else '+'}] {element['name']}"
                x = self.start_x
            else:
                text = element["name"]
                x = self.start_x + self.indent

            btn = Button(text, self.font, (x, y))
            btn.draw(screen)

            self.ui_elements.append({
                "button": btn,
                "data": element
            })

            y += self.item_height




if __name__ == '__main__':
    from game_button import Button


    print('testings settings menu')
    # print(pygame.font.get_fonts())
    running = True
    pygame.init()
    font = pygame.font.SysFont('sourcecodepro', 16)
    WINDOW_WIDTH, WINDOW_HEIGHT = 640, 420
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    bckgrnd_col = pygame.Color(206, 255, 218, 255)
    text_color = pygame.Color(0,0,0)

    def draw_text(text, font, text_col, x, y):
        img = font.render(text, True, text_col)
        screen.blit(img, (x, y))

    bmo_paused = False
    button_index = 0
    while running:
        screen.fill(bckgrnd_col)

        vert_spacing = 40
        start_y = WINDOW_HEIGHT // 2 - 1.5 * vert_spacing

        buttons = [
            Button("Resume", font, (WINDOW_WIDTH // 2, start_y)),
            Button("Settings", font, (WINDOW_WIDTH // 2, start_y + vert_spacing)),
            Button("Restart", font, (WINDOW_WIDTH // 2, start_y + 2 * vert_spacing)),
            Button("Quit", font, (WINDOW_WIDTH // 2, start_y + 3 * vert_spacing)),
            Button("Shutdown", font, (WINDOW_WIDTH // 2, start_y + 4 * vert_spacing)),
        ]
        select_button = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                    print('paused')
                    bmo_paused = not bmo_paused
            if bmo_paused:
                if event.key == pygame.K_DOWN:
                    button_index = (button_index + 1) % len(buttons)
                if event.key == pygame.K_UP:
                    button_index = (button_index - 1) % len(buttons)
                if event.key == pygame.K_RETURN:
                    select_button = True
                for i in range(len(buttons)):
                    button = buttons[i]
                    if button.is_clicked(event) or (select_button and button_index == i):
                        if button.text == "Resume":
                            print("resuming BMO")
                            bmo_paused = False
                        elif button.text == "Settings":
                            print("Open settings")
                        elif button.text == "Restart":
                            print("Restarting")
                        elif button.text == "Quit":
                            running = False
                            #clean_exit.value = True
                            # sys.exit()
                        elif button.text == "Shutdown":
                            print("shutting down system")

        if bmo_paused:
            for i in range(len(buttons)):
                button = buttons[i]
                button.draw(screen, button_index == i)
        else:
            draw_text("press esc or space to open menu", font, text_color, 200, 100)
        pygame.display.flip()
    pygame.quit()
    exit()
