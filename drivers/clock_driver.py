import pygame
from .game_button import *
from .settings import *
import os
import random
import json
import datetime

settingsOBJ = BMOSettings()
WINDOW_WIDTH, WINDOW_HEIGHT = settingsOBJ.get_window_size()

# #set to hardware option on system
# # 1. Force SDL to use the ALSA audio driver backend
# os.environ["SDL_AUDIODRIVER"] = "alsa"

# # 2. Force ALSA to output directly to hardware card 0
# os.environ["AUDIODEV"] = "plughw:0"
class AlarmClock():
    # import datetime
    def __init__(self):
        pygame.mixer.init()
        self.bckgrnd_col = pygame.Color(206, 255, 218, 255)
        self.font = pygame.font.SysFont(settingsOBJ.get_font(), 20)
        self.text_col = pygame.Color(0, 0, 0)
        self.time_font = pygame.font.SysFont(settingsOBJ.get_font(), 50)

        self.time_x = WINDOW_WIDTH//2 - 20
        self.time_y = WINDOW_HEIGHT//2 - 40
        self.rect = pygame.FRect(self.time_x, self.time_y, 0, 0)
        self.alarms = []
        self.clock_mode = 0
        self.digit_index = 0

        self.perma_index = 0
        self.perma_alarms = []
        self.perma_buttons = []
        self.load_perma_alarms()
        self.gen_perma_buttons()

        self.alarm_error = False
        self.alarm_added = False
        self.message = None
        self.message_time = 0
        self.message_duration = 2500

        self.AM = False
        self.temp_alarm = True

        self.alarming = False

        self.alarm_sounds = self.load_sounds()

        self.curr_time = datetime.datetime.now()
        self.digits = []
        self.update_time()
        self.alarm_buttons = []
        self.gen_alarm_buttons()

    def event_handle(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:
                self.clock_mode = (self.clock_mode + 1) % 4

            #TODO pick a different key for this because this one opens settings
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_m:
                self.stop_alarm()

            # if (self.clock_mode == 1 or self.clock_mode == 2) and event.key == pygame.K_RETURN:
            #     if self.clock_mode == 1:
            #         self.digit_index = 0
            #         self.clock_mode = 2
            #     else: 
            #         self.digit_index = 0
            #         self.clock_mode = 1
                    
            if self.clock_mode == 2:
                if event.key == pygame.K_LEFT:
                    self.digit_index = (self.digit_index - 1) % 5

                elif event.key == pygame.K_RIGHT:
                    self.digit_index = (self.digit_index + 1) % 5

                #I know the below is over complicated I just did it once tested it and decided to copy paste rather than refactor
                highlighted_button = self.alarm_buttons[self.digit_index]
                if self.digit_index == len(self.alarm_buttons)-1:
                    if event.key in [pygame.K_UP, pygame.K_DOWN]:
                        self.temp_alarm = not self.temp_alarm
                    if event.key == pygame.K_RETURN:
                        self.add_alarm()
                        # if highlighted_button.text == 'TEMP':
                        #     self.add_alarm()
                        # if highlighted_button.text == 'PERMA':
                        #     #set alarm into current alarms
                        #     self.add_alarm()

                elif highlighted_button.text in ['AM', 'PM'] and event.key in [pygame.K_UP, pygame.K_DOWN]:
                    self.AM = not self.AM
                elif self.digit_index == 2  and event.key == pygame.K_UP:
                    self.digits[self.digit_index] = (self.digits[self.digit_index] + 1) % 10
                elif self.digit_index == 2  and event.key == pygame.K_DOWN:
                    self.digits[self.digit_index] = (self.digits[self.digit_index] - 1) % 10
                elif self.digit_index == 1  and event.key == pygame.K_UP:
                    self.digits[self.digit_index] = (self.digits[self.digit_index] + 1) % 6
                elif self.digit_index == 1  and event.key == pygame.K_DOWN:
                    self.digits[self.digit_index] = (self.digits[self.digit_index] - 1) % 6
                    
                # elif self.digit_index == 1  and event.key == pygame.K_UP:
                #     if self.digits[0] == 1:
                #         self.digits[self.digit_index] = (self.digits[self.digit_index] + 1) % 3
                #     else:
                #         self.digits[self.digit_index] = (self.digits[self.digit_index] + 1) % 10
                # elif self.digit_index == 1  and event.key == pygame.K_DOWN:
                #     if self.digits[0] == 1:
                #         self.digits[self.digit_index] = (self.digits[self.digit_index] - 1) % 3
                    # else:
                    #     self.digits[self.digit_index] = (self.digits[self.digit_index] - 1) % 10

                elif self.digit_index == 0  and event.key == pygame.K_UP:
                    self.digits[self.digit_index] = (self.digits[self.digit_index] + 1) % 12
                elif self.digit_index == 0  and event.key == pygame.K_DOWN:
                    self.digits[self.digit_index] = (self.digits[self.digit_index] - 1) % 12

            elif self.clock_mode == 3:
                if event.key == pygame.K_RETURN:
                    self.add_perma_alarm()
                elif event.key == pygame.K_UP:
                    self.perma_index = (self.perma_index - 1) % 5
                elif event.key == pygame.K_DOWN:
                    self.perma_index = (self.perma_index + 1) % 5
                

    def gen_alarm_buttons(self, debug=False):
        if debug:
            print(f'generating buttons for {len(self.digits)} digits')
        for i, digit in enumerate(self.digits):
            if i == 0:
                self.alarm_buttons.append(Button(str(digit), self.time_font, (self.time_x-200 + i*48, self.time_y)))
            else:
                self.alarm_buttons.append(Button(str(digit), self.time_font, (self.time_x-200 + 25 + i*35, self.time_y)))
        if self.AM:
            self.alarm_buttons.append(Button('AM', self.time_font, ((self.time_x-200 + (len(self.digits))*50, self.time_y))))
        else:
            self.alarm_buttons.append(Button('PM', self.time_font, ((self.time_x-200 + (len(self.digits))*50, self.time_y))))
        if self.temp_alarm:
            self.alarm_buttons.append(Button('TEMP', self.time_font, ((self.time_x-200 + (len(self.digits)+4)*45, self.time_y))))
        else:
            self.alarm_buttons.append(Button('PERMA', self.time_font, ((self.time_x-200 + (len(self.digits)+4)*45, self.time_y))))


    def update_alarm_buttons(self, debug=False):
        for i, digit in enumerate(self.digits):
            if debug:
                print('updating buttons')
                # print(f'indexing at: {i} but there are only {len(self.alarm_buttons)} buttons')
                print(f'digit: {digit}')
            button = self.alarm_buttons[i]
            button.update_text(str(digit))
        button = self.alarm_buttons[len(self.alarm_buttons)-2]
        meridian = 'AM'
        if not self.AM:
            meridian = 'PM'
        button.update_text(meridian)
        button = self.alarm_buttons[len(self.alarm_buttons)-1]
        alarm_type = 'TEMP'
        if not self.temp_alarm:
            alarm_type = 'PERMA'
        button.update_text(alarm_type)

    def update_time(self):
        self.digits = []
        hour = self.curr_time.hour
        if hour >= 12:
            self.AM = False
        else: 
            self.AM = True
        hour %= 12
        self.digits.append(hour)
        self.digits.append(self.curr_time.minute // 10)
        self.digits.append(self.curr_time.minute % 10)


    def update(self):
        self.curr_time = datetime.datetime.now()
        #test alarm sounds
        # if random.randint(0,50) in range(5):
        #     self.play_alarm()
        self.check_alarms()
        if self.alarm_error:
            self.message = 'invalid alarm time cannot add alarm'
            self.message_time = pygame.time.get_ticks()
            self.alarm_error = False

        elif self.alarm_added:
            self.message = f'alarm has been successfully added at {self.alarms[-1]}'
            self.message_time = pygame.time.get_ticks()
            self.alarm_added = False

        if self.clock_mode <= 1:
            self.update_time()
            self.update_alarm_buttons()
        if self.clock_mode == 2:
            self.update_alarm_buttons()
        # if self.clock_mode == 3:
        #     print('showing permanent alarms')

    def get_mode(self):
        if self.clock_mode == 1:
            return 'clock'
        if self.clock_mode == 2:
            return 'alarm'
        if self.clock_mode == 3:
            return 'permalarms'
        return 'normal'
    
    def digits_to_time(self, debug=False):
        # alarm = None
        hour = self.digits[0]
        if not self.AM:
            hour += 12
        minute = self.digits[1] * 10 + self.digits[2]
        return hour, minute
                



    #i dont think this will ever be used outside of testing in development
    # def draw_time(self, text, x, y):
    #     img = self.time_font.render(text, True, self.text_col)
    #     self.screen.blit(img, (x, y))

    def draw(self, surface):
        #if the clock section is 0 it should do nothing because BMO would just display the face
        if self.clock_mode == 1:
            #just display the time
            temp_time = self.curr_time.strftime('%l:%M%p on %b %d, %Y')
            self.text_surface = self.time_font.render(temp_time, True, self.text_col)
            text_rect = self.text_surface.get_rect(center=self.rect.center)
            surface.blit(self.text_surface, text_rect)
        elif self.clock_mode == 2:
            for i, button in enumerate(self.alarm_buttons):
                button.draw(surface, self.digit_index == i)
            self.draw_text(':', self.time_font, surface, self.time_x-200 + 25, self.time_y-20)

        if self.message:
            current_time = pygame.time.get_ticks()
            if current_time - self.message_time < self.message_duration:
                self.draw_text(self.message, self.font, surface, WINDOW_WIDTH//2-150, 30)
            else:
                self.message = None
        elif self.clock_mode == 3:
            for i, button in enumerate(self.perma_buttons):
                button.draw(surface, self.perma_index == i)

        

    #TODO add Alarms to BMO clock version
    def add_alarm(self, debug=True):
        alarm = None
        hour, minute = self.digits_to_time()

        if hour > 23:
            self.alarm_error = True
            print('invalid alarm time cannot add alarm')
            return

        # Build alarm for today
        alarm = self.curr_time.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

        # If alarm time already passed (or is now), move to tomorrow
        if alarm <= self.curr_time:
            if debug:
                print('alarm time has already passed today, scheduling for tomorrow')

            alarm += datetime.timedelta(days=1)

        self.alarm_added=True

        if not self.temp_alarm:
            self.perma_alarms.append(alarm)
            if len(self.perma_alarms) > 5:
                self.perma_alarms.pop()
            #regenerate buttons
            self.gen_perma_buttons()
        self.alarms.append(alarm)
        self.save_perma_alarms()


    def add_perma_alarm(self, debug=False):
        """add an alarm from the set permanent alarms options and sort by most 
        recent alarm that way generally the most used alarms will remain on the 
        list at all times this will fail to happen however in the case that 
        someone add 5 new alarms to the permanent section effectively clearing 
        all previous alarms"""
        #remove alarm from the list since the visual list is reversed so most 
        # recent is at the top the index needs to be reversed as well
        alarm = self.perma_alarms.pop(len(self.perma_alarms)-self.perma_index)

        # if self.curr_time.hour == alarm.hour:
        #     if self.curr_time.minute == alarm.minute:
        #         if debug:
        #             print('user set an alarm for right now which is impossible so I assume user means this time tomorrow')
        #         alarm = self.curr_time.replace(second=0,microsecond=0) + datetime.timedelta(day=1)
        #     elif self.curr_time.minute > alarm.minute:
        #         if debug:
        #             print('alarm minute is set prior to now so must be for tomorrow')
        #         alarm = self.curr_time.replace(hour=alarm.hour, minute=alarm.minute, second=0, microsecond=0) + datetime.timedelta(day=1)
        #     else:
        #         alarm = self.curr_time.replace(minute=alarm.minute, second=0, microsecond=0)

        # if self.curr_time.hour > alarm.hour:
        #     if debug:
        #         print('alarm hour is set prior to now so must be for tomorrow')
        #     alarm = self.curr_time.replace(hour=alarm.hour, minute=alarm.minute, second=0, microsecond=0) + datetime.timedelta(day=1)

        # else:
        #     alarm = self.curr_time.replace(hour=alarm.hour, minute=alarm.minute, second=0, microsecond=0)
        #repopulate it at the top of the list
        self.perma_alarms.append(alarm)
        self.alarm_added = True
        self.alarms.append(alarm)
        self.gen_perma_buttons()
        self.save_perma_alarms()

    def load_perma_alarms(self, path='perma_alarms.json'):
        """
        Loads permanent alarms from a JSON file.

        File structure example:
        {
            "permanent_alarms": [
                {
                    "time": "07:00",
                    "label": "Wake up"
                }
            ]
        }

        If the file does not exist, it will be created with
        an empty permanent_alarms list. These alarms load with no dependence on 
        what it is day so they always default to the current day barring 
        special conditions
        """

        default_data = {
            "permanent_alarms": []
        }

        # Create file if it doesn't exist
        if not os.path.exists(path):
            with open(path, 'w') as file:
                json.dump(default_data, file, indent=4)

            self.perma_alarms = []
            return

        try:
            with open(path, 'r') as file:
                data = json.load(file)

            alarms = data.get("permanent_alarms", [])

            # Convert ISO strings back to datetime objects
            today = datetime.date.today()

            self.perma_alarms = []

            for alarm in alarms:
                loaded_dt = datetime.datetime.fromisoformat(alarm)

                # Rebuild using today's date but original time
                new_dt = datetime.datetime.combine(
                    today,
                    loaded_dt.time()
                )

                # Optional: if the time already passed today, move to tomorrow
                if new_dt < datetime.datetime.now():
                    new_dt += datetime.timedelta(days=1)

                self.perma_alarms.append(new_dt)


        except (json.JSONDecodeError, IOError):
            print(f"Warning: '{path}' is corrupted or unreadable.")

            # Reset corrupted file
            with open(path, 'w') as file:
                json.dump(default_data, file, indent=4)

            self.perma_alarms = []

    def save_perma_alarms(self, path='perma_alarms.json'):
        """
        Saves permanent alarms to disk.
        Datetime objects are converted to ISO strings.
        """

        data = {
            "permanent_alarms": [
                alarm.isoformat()
                for alarm in self.perma_alarms
            ]
        }

        with open(path, 'w') as file:
            json.dump(data, file, indent=4)

    def gen_perma_buttons(self):
        for i, alarm in enumerate(reversed(self.perma_alarms)):
            self.perma_buttons.append(Button(alarm.strftime('%l:%M%p'),self.font, (WINDOW_WIDTH//2, 100+45*i), self.text_col))

    def check_alarms(self, debug=True):
        
        for alarm in self.alarms:
            if alarm <= datetime.datetime.now():
                if (debug):
                    print(f'alarm {alarm} triggered at {datetime.datetime.now()}')
                self.play_alarm()

        self.delete_alarm()
                
    def load_sounds(self, folder="sounds"):
        
        sounds = []
        supported_formats = (".wav", ".flac")

        for root, _, files in os.walk(folder):
            for file in files:
                # print(f'loaded sound: {file}')
                if file.lower().endswith(supported_formats):
                    full_path = os.path.join(root, file)
                    
                    try:
                        sound = pygame.mixer.Sound(full_path)
                        sounds.append(sound)
                    except pygame.error as e:
                        print(f"Could not load {full_path}: {e}")

        return sounds

    def play_alarm(self):
        if not self.alarming:
            # print('playing alarm audio')
            self.alarming = True
            random.choice(self.alarm_sounds).play(-1)


    def delete_alarm(self):
        self.alarms = [x for x in self.alarms if x >= datetime.datetime.now()]
                
    def stop_alarm(self):
        self.alarming = False
        pygame.mixer.stop()


    def draw_text(self, text, font, screen, x, y):
        img = font.render(text, True, self.text_col)
        # text_rect = 
        screen.blit(img, (x, y))

#I DONT KNOW WHY I HAVE THIS CLASS AND I CANT REMEMBER WHY I MADE IT
class DigitButton():
    def __init__(
        self,
        text,
        font,
        center_pos,
        text_color=(0, 0, 0),
        button_color=(206, 255, 218),
        hover_color=(100, 160, 210),
        border_color=(0, 0, 0),
        border_width=4,
        padding=10
    ):
        self.text = text
        self.font = font
        self.center_pos = center_pos

        self.text_color = text_color
        self.button_color = button_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.border_width = border_width
        self.padding = padding

        self._create_surfaces()

    def _create_surfaces(self):
        # Render text
        self.text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = self.text_surface.get_rect()

        # Button size = text size + padding
        width = text_rect.width + self.padding * 2
        height = text_rect.height + self.padding * 2

        # Create button rect
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = self.center_pos

        # Store inner rect (area inside border)
        self.inner_rect = pygame.Rect(
            self.rect.left + self.border_width,
            self.rect.top + self.border_width,
            self.rect.width - self.border_width * 2,
            self.rect.height - self.border_width * 2
        )

    def update_text(self, text):
        self.text = text
        self._create_surfaces()
    
    def draw(self, surface, highlighted:bool, x=-1, y=-1):
        if x != -1 and y != -1:
            self.center_pos = (x, y)
            self._create_surfaces()


        color = self.button_color
        if highlighted:
            color = self.border_color
        
         # Draw border (black box)
        pygame.draw.rect(surface, color, self.rect)

        # Draw inner button
        pygame.draw.rect(surface, self.button_color, self.inner_rect)

        # Draw text centered
        text_rect = self.text_surface.get_rect(center=self.rect.center)
        surface.blit(self.text_surface, text_rect)