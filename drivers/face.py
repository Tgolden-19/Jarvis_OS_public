from .settings import *
from random import randrange, randint
from os import walk

settings = BMOSettings()
WINDOW_WIDTH, WINDOW_HEIGHT = settings.get_window_size()
WINDOW_CENTER = pygame.math.Vector2((WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
WINDOW_RADIUS = pygame.math.Vector2(WINDOW_WIDTH, WINDOW_HEIGHT) - WINDOW_CENTER
ZERO_VECTOR = pygame.math.Vector2((0,0))
EYE_SCALE_BASE = [0.7, 0.7]
MOUTH_SCALE_BASE = [0.7, 0.9]
MOUTH_OFFSET_BASE = [10, 20]
EYE_OFFSET_SCALE = [0.9, 0.9]
SCALE_EYES_ON_MOVE = False
SCALE_MOUTH_ON_MOVE = False
OFFSET_MOUTH_ON_MOVE = False
OFFSET_EYES_ON_MOVE = False
SEPERATE_EYE_SCALING = False
FACE_SCALING=2.5


class FaceBase():
    def __init__(self, pos, groups):
        self.eyes = Eyes(pos, groups, True, FACE_SCALING)
        self.mouth = Mouth(pos, groups, True, FACE_SCALING)
        self.ref_rect = pygame.FRect(pos,(0,0))
        self.direction = pygame.math.Vector2(0,0)
        self.speed = 20
        self.head_cool_mult = 3
        self.head_move_cooldown = False
        self.timestamp = 0.0
        self.time_since_event = 0.0
        self.move_to = None
        self.interp_val = 0.0
        self.reached_loc = False

    def head_move(self, dt):
        if not(self.head_move_cooldown) and settings.get_value('settings_toggles', 'head_move'):
            temp = randint(0, 10000)
            if temp >= 9990 and temp <= 10000:
                # print('smooth moving head to')
                self.move_to = pygame.math.Vector2((randrange(150, WINDOW_WIDTH-150), randrange(100, WINDOW_HEIGHT-100)))
                # print(self.move_to)
                self.head_move_cooldown = True
        #NOTE I hope there was a better way to do this but man was this the only way I could get it to work
        #interpolate location of head to new random location
        if self.move_to != None and not self.reached_loc:
            self.interp_val += dt * self.speed
            step = WINDOW_CENTER.smoothstep(self.move_to, self.interp_val)
            self.ref_rect.center = step
            if self.ref_rect.center == self.move_to:
                self.reached_loc = True
                self.time_since_event = 0.0
            # if step == self.move_to:
            #     self.reached_loc = True
        #end interpolation away to new location
        #start interpolation from away location back to center
        elif self.ref_rect.center != WINDOW_CENTER and self.reached_loc and self.time_since_event > 60 * 0.5:
            self.interp_val -= dt * self.speed
            step = WINDOW_CENTER.smoothstep(self.move_to, self.interp_val)
            self.ref_rect.center = step
            if step == WINDOW_CENTER:
                self.move_to = None
                self.interp_val = 0
                self.head_move_cooldown = True
                self.time_since_event = 0
                self.reached_loc = False
        #end interpolation back to center and start cooldown for face movement

        if self.time_since_event > 60 * self.head_cool_mult:
            self.head_move_cooldown = False

    def move(self, dt, direction=pygame.math.Vector2(0,0), speed=1):
        self.direction = pygame.math.Vector2(direction)
        self.speed = speed
        self.ref_rect.center += self.direction * self.speed * dt
        #Check if should move face to random location
        self.head_move(dt)
        self.eyes.move(self.ref_rect.center)
        self.mouth.move(self.ref_rect.center)

    def animate(self, dt,eye_key='none', mouth_key='none'):
        #A debug to make sure animation keys are feeding through
        # if not eye_key == 'none' or not mouth_key == 'none' or not eye_key == None or not mouth_key == None:
        #     print(f'eye animation key: {eye_key}, mouth animation key: {mouth_key}')
        self.eyes.animate(eye_key, dt)
        self.mouth.animate(mouth_key, dt)

    def update(self, dt, eye_key='none', mouth_key='none'):
        self.time_since_event += dt
        self.animate(dt, eye_key, mouth_key)
        self.move(dt)
        self.eyes.update(dt)
        self.mouth.update(dt)

class Mouth(pygame.sprite.Sprite):
    def __init__(self, pos, groups, alt=False, full_resize=5):
        super().__init__(groups)
        self.use_alt_img_format = alt
        self.def_resize = 1.75
        self.full_resize = full_resize
        self.load_images()
        self.anim_cooldown = False
        self.elapsed_time = 0.0
        self.linger_expressions = {
            'happy': 3.0,   # linger 3 seconds
            'frown': 2.5,
            'shock': 2.0,
            'pout': 2.5,
            'smile': 2.5
        }
        #TODO add frequency changes from a setting/config file so users can control it
        self.cooldown_mult = 2
        self.image = pygame.image.load(join('animations', 'mouth', 'default', '1.png')).convert_alpha()
        if alt:
            self.alt_offsets()
            self.image = pygame.transform.scale(pygame.image.load(join('animations', 'mouth_alt', 'default', '1.png')).convert_alpha(), (28*self.def_resize, 6*self.def_resize))
        self.state, self.frame_index = 'default', 0
        self.rect = self.image.get_frect(center = pos)
        self.anim_rate = 24
        self.timestamp = 0.0

    def load_images(self):
        self.frames = {'aa': [], 'eh_ay': [], 'oh': [], 'oo': [], 'sh_ch': [],
                        'bmp': [], 'ee': [],'f': [], 'l': [], 'th': [], 'happy': [], 'pout': [], 'smile': [],
                          'frown': [], 'shock': [], 'default': []}
        fold_name = 'mouth'
        if self.use_alt_img_format:
            fold_name = 'mouth_alt'
        for state in self.frames.keys():
            for folder_path, _, file_names in walk(join('animations', fold_name, state)):
                    if file_names:
                        for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                            full_path = join(folder_path, file_name)
                            # print(full_path)
                            surf = pygame.image.load(full_path).convert_alpha()
                            if state == 'ee':
                                surf = pygame.transform.flip(surf,flip_x=True, flip_y=False)
                            if state == 'default' and self.use_alt_img_format:
                                surf = pygame.transform.scale_by(surf, self.def_resize)

                            surf = pygame.transform.scale_by(surf, self.full_resize)
                            self.frames[state].append(surf)


    def scale_mouth(self):
        offset_vector = WINDOW_CENTER - pygame.math.Vector2(self.rect.center)
        offset_dist = pygame.math.Vector2(abs(offset_vector.x), abs(offset_vector.y))
        scale_factor = offset_dist.elementwise() / WINDOW_RADIUS
        # scale_inv = pygame.math.Vector2((1,1))-scale_factor
        # scale_mag = pygame.math.Vector2((pygame.math.lerp(0.7, 1, scale_inv.x, True), pygame.math.lerp(0.7, 1, scale_inv.y, True)))
        scale_mag = pygame.math.Vector2((pygame.math.smoothstep(1, MOUTH_SCALE_BASE[0], scale_factor.x), pygame.math.smoothstep(1, MOUTH_SCALE_BASE[1], scale_factor.y)))
        # print(scale_inv)
        # print(scale_mag)

        #TODO look into the funky warping of scaling may have to separate the individual eyes
        self.image = pygame.transform.scale_by(self.image, scale_mag)
        # self.image = pygame.transform.scale_by(self.image, 1.1)

        # print(window_radius)

        # self.image = pygame.transform.scale_by(self.image,)
        # print(offset_norm)

    def offset_mouth(self):
        offset_vector = WINDOW_CENTER - pygame.math.Vector2(self.rect.center)
        # y_offset = 60
        # x_offset = 100
        # offset_dist = pygame.math.Vector2(abs(offset_vector.x), abs(offset_vector.y))
        y_factor = abs(offset_vector.y) / WINDOW_RADIUS.y
        x_factor = offset_vector.x / WINDOW_RADIUS.x
        # scale_factor = offset_dist.elementwise() / WINDOW_RADIUS
        #S-Lerp version of mouth movement below
        # temp =  pygame.math.smoothstep(0, MOUTH_OFFSET_BASE[0], x_factor)
        # offset_vec = pygame.math.Vector2((temp*-1 if x_factor >= 0 else temp, pygame.math.smoothstep(0, MOUTH_OFFSET_BASE[1], y_factor)*-1))
        # end S-lerp version of mouth move
        temp =  pygame.math.lerp(0, MOUTH_OFFSET_BASE[0], x_factor, True)
        offset_vec = pygame.math.Vector2((temp*-1 if x_factor >= 0 else temp, pygame.math.lerp(0, MOUTH_OFFSET_BASE[1], y_factor, True)*-1))
        self.rect.center += offset_vec

    def move(self, pos):
        self.rect.center = pos
        if self.use_alt_img_format:
            self.rect.center += pygame.math.Vector2(self.offsets[self.state])
        if OFFSET_MOUTH_ON_MOVE:
            self.offset_mouth()
        if SCALE_MOUTH_ON_MOVE:
            self.scale_mouth()

    def gen_rand_anim(self):
        if not(self.anim_cooldown) and settings.get_value('settings_toggles', 'random_expressions'):
            temp = randint(0, 10000)
            if temp == 5000:
                return 'happy'
            elif temp == 2500:
                return 'frown'
            elif temp == 7500:
                return 'pout'
            elif temp == 1000:
                return 'shock'
        
        if self.frame_index > 3600*self.cooldown_mult:#has a 1 minute cooldown on random events multiplied
            self.anim_cooldown = False

        
        return 'default'

    def animate(self, key, dt):
        """Update animation state based on phoneme key and expressions, using absolute time for lingering."""
        # Track time instead of frames
        self.elapsed_time += dt  # accumulate time in seconds
        prev_state = self.state
        skip_state_change = False

        # Expressions that should linger for a fixed duration

        if self.state in self.linger_expressions:
            if self.elapsed_time <= self.linger_expressions[self.state]:
                skip_state_change = True
                self.anim_cooldown = True
            else:
                self.anim_cooldown = False

        # Only map phonemes if we are allowed to change state
        if not skip_state_change and key is not None:
            self.state = self.map_phon_to_anim(key)
            self.elapsed_time = 0.0  # reset elapsed time for new animation

        # If the state changed (e.g., phoneme overrides expression), reset elapsed time
        if prev_state != self.state:
            self.elapsed_time = 0.0
        #used below line to enforce certain frames for testing
        # self.state = 'default'
        # print("playing anim: " + self.state)
        
        self.image = self.frames[self.state][pygame.math.clamp(int(self.frame_index), 0, len(self.frames[self.state])-1)]
        if self.rect.centerx > WINDOW_CENTER.x:
            self.image = pygame.transform.flip(self.image, flip_x=True, flip_y=False)
        # self.image = self.frames['default'][0]
    
    def map_phon_to_anim(self, key):
        match key:
                case 'AA':
                    return 'aa'
                case 'AE':
                    return 'aa'
                case 'AH':
                    return 'aa'
                case 'AO':
                    return'aa'
                case 'AW':
                    return 'oh'
                case 'AY':
                    return 'eh_ay'
                case 'B':
                    return 'bmp'
                case 'CH':
                    return 'sh_ch'
                case 'D':
                    #@TODO look for better animation to map
                    return 'sh_ch'
                case 'DH':
                    #@TODO look for better animation to map
                    return 'sh_ch'
                case 'EH':
                    return 'eh_ay'
                case 'ER':
                    #@TODO look for better animation to map
                    return 'eh_ay'
                case 'F':
                    return 'f'
                case 'G':
                    return 'eh_ay'
                case 'HH':
                    return 'eh_ay'
                case 'IH':
                    return 'ee'
                case 'IY':
                    return 'ee'
                case 'JH':
                    #@TODO look for better animation to map
                    return 'sh_ch'
                case 'K':
                    return 'eh_ay'
                case 'L':
                    return 'l'
                case 'M':
                    return 'bmp'
                case 'N':
                    #@TODO look for better animation to map
                    return 'th'
                case 'NG':
                    #@TODO look for better animation to map
                    return 'th'
                case 'OW':
                    return 'oh'
                case 'OY':
                    return 'eh_ay'
                case 'P':
                    return 'bmp'
                case 'R':
                    #@TODO look for better animation to map
                    return 'eh_ay'
                case 'S':
                    #@TODO look for better animation to map
                    return 'sh_ch'
                case 'SH':
                    return 'sh_ch'
                case 'T':
                    #@TODO look for better animation to map
                    return 'sh_ch'
                case 'TH':
                    return 'sh_ch'
                case 'UH':
                    #@TODO look for better animation to map
                    return "eh_ay"
                case 'UW':
                    return 'oo'
                case 'V':
                    return 'f'
                case 'W':
                    return 'oo'
                case 'Y':
                    return 'eh_ay'
                case 'Z':
                    #@TODO look for better animation to map
                    return 'sh_ch'
                case 'ZH':
                    #@TODO look for better animation to map
                    return 'sh_ch'
                case _:
                    return 'default'

    def alt_offsets(self):
        #offsets designed for default image scaling of 2.5x
        self.offsets = {'aa': [-130, 20], 'eh_ay': [-130, 40], 'oh': [-40, 50], 
                        'oo': [5, 50], 'sh_ch': [-120, 40],'bmp': [-80, 75], 
                        'ee': [-160, 40],'f': [-160, 60], 'l': [-140, 30], 
                        'th': [-140, 40], 'happy': [-80, 40], 'pout': [-80, 50],
                          'smile': [-80, 50], 'frown': [-85, 50], 'shock': [-140, 40], 
                          'default': [-30, 80]}
        
    def update(self, dt):
        # self.timestamp += dt
        # self.animate('none', dt)
        pass

class Eyes():
    def __init__(self, pos, groups, alt=False, full_resize=5):
        self.use_alt_img_format = alt
        self.state, self.frame_index = 'default', 0
        self.ref_rect = pygame.FRect(pos,(0,0))
        self.eye_l = EyeL(pos, groups, alt, full_resize)
        self.eye_r = EyeR(pos, groups, alt, full_resize)
        self.anim_rate = 24
        self.timestamp = 0.0
        if alt:
            self.alt_offsets()



    def alt_offsets(self):
        self.offsets = {'blink': pygame.math.Vector2((0, -12)), 'default': pygame.math.Vector2((0, -25))}

    def move(self, pos):
        self.ref_rect.center = pos + self.offsets[self.state] if self.use_alt_img_format else pos
        self.eye_l.move(self.ref_rect.center)
        self.eye_r.move(self.ref_rect.center)

    def gen_rand_anim(self):
        #and settings.get_value('settings_toggles', 'random_expressions') #this is an additional condition statement for when and if random animations are added to the eyes
        if randint(0, 360) == 360:
            return 'blink'
        return 'default'
    
    def animate(self, key, dt):
        self.frame_index += dt * self.anim_rate
        skip_state_change = False
        prev_state = self.state
        match self.state:
            case 'blink':
                if self.frame_index <= 4:
                    skip_state_change = True
        if not(skip_state_change):
            match key:
                case 'SUS':
                    # print('displaying ' + key + ' anim')
                    self.state = 'SUS'
                case _:
                    self.state = self.gen_rand_anim()
                    
                        # print('blinking')
                    # print('displaying base/default anim')
        if self.state != prev_state:
            self.frame_index = 0
        # print(len(self.frames[self.state])-1)

        self.eye_l.animate(self.state, dt)
        self.eye_r.animate(self.state, dt)
    
    def update(self, dt):
        pass

#------------------------below is an olf functioning implementation of the animated eyes--------------------------
# class Eyes(pygame.sprite.Sprite):
#     def __init__(self, pos, groups, alt=False):
#         super().__init__(groups)
#         self.use_alt_img_format = alt
#         self.load_images()
#         # print(join('animations', 'eyes', 'default', '1'))
#         self.image = pygame.image.load(join('animations', 'eyes', 'default', '1.png')).convert_alpha()
#         if alt:
#             self.alt_offsets()
#             self.image = pygame.image.load(join('animations', 'eyes_alt', 'default', '1.png')).convert_alpha()
#         self.state, self.frame_index = 'default', 0
#         self.rect = self.image.get_frect(center = pos)
#         self.anim_rate = 24
#         self.timestamp = 0.0

#     def load_images(self):
#         self.frames = {'blink': [], 'default': []}
#         fold_name = 'eyes'
#         if self.use_alt_img_format:
#             fold_name = 'eyes_alt'
#         for state in self.frames.keys():
#             for folder_path, _, file_names in walk(join('animations', fold_name, 'combined', state)):
#                     if file_names:
#                         for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
#                             full_path = join(folder_path, file_name)
#                             # print(full_path)
#                             surf = pygame.image.load(full_path).convert_alpha()
#                             self.frames[state].append(surf)
#     def alt_offsets(self):
#         self.offsets = {'blink': [0, -20], 'default': [0, -20]}

#     def scale_eyes(self):
#         offset_vector = WINDOW_CENTER - pygame.math.Vector2(self.rect.center)
#         offset_dist = pygame.math.Vector2(abs(offset_vector.x), abs(offset_vector.y))
#         scale_factor = offset_dist.elementwise() / WINDOW_RADIUS
#         # scale_inv = pygame.math.Vector2((1,1))-scale_factor
#         # scale_mag = pygame.math.Vector2((pygame.math.lerp(0.7, 1, scale_inv.x, True), pygame.math.lerp(0.7, 1, scale_inv.y, True)))
#         scale_mag = pygame.math.Vector2((pygame.math.smoothstep(1, 0.7, scale_factor.x), pygame.math.smoothstep(1, 0.7, scale_factor.y)))
#         # print(scale_inv)
#         # print(scale_mag)

#         #TODO look into the funky warping of scaling may have to separate the individual eyes
#         self.image = pygame.transform.scale_by(self.image, scale_mag)
#         # self.image = pygame.transform.scale_by(self.image, 1.1)

#         # print(window_radius)

#         # self.image = pygame.transform.scale_by(self.image,)
#         # print(offset_norm)
#     def move(self, pos):
#         self.rect.center = pos + pygame.math.Vector2(self.offsets[self.state])
#         if SCALE_FACE_ON_MOVE:
#             self.scale_eyes()
#             self.rect = self.image.get_frect(center = pos + pygame.math.Vector2(self.offsets[self.state]))

#     def gen_rand_anim(self):
#         if randint(0, 360) == 360:
#             return 'blink'
#         return 'default'

#     def animate(self, key, dt):
#         self.frame_index += dt * self.anim_rate
#         skip_state_change = False
#         prev_state = self.state
#         match self.state:
#             case 'blink':
#                 if self.frame_index <= 4:
#                     skip_state_change = True
#         if not(skip_state_change):
#             match key:
#                 case 'SUS':
#                     print('displaying ' + key + ' anim')
#                     self.state = 'SUS'
#                 case _:
#                     self.state = self.gen_rand_anim()
                    
#                         # print('blinking')
#                     # print('displaying base/default anim')
#         if self.state != prev_state:
#             self.frame_index = 0
            
#         self.image = self.frames[self.state][pygame.math.clamp(int(self.frame_index), 0, len(self.frames[self.state])-1)]

#     def update(self, dt):
#         # self.timestamp += dt
#         # self.animate('none', dt)
#         pass
#--------------------END OLD IMPLEMENTATION -------------------------------------------

class EyeL(pygame.sprite.Sprite):
    def __init__(self, pos, groups, alt=False, full_resize=1):
        super().__init__(groups)
        self.use_alt_img_format = alt
        self.full_resize = full_resize

        self.load_images()
        # print(join('animations', 'eyes', 'default', '1'))
        self.alt_offsets()
        self.image = pygame.image.load(join('animations', 'eyes_alt', 'default', 'L', '1.png')).convert_alpha()
        self.state, self.frame_index = 'default', 0
        self.rect = self.image.get_frect(center = pos)
        self.anim_rate = 24
        self.timestamp = 0.0

    def load_images(self):
        # print('loading images:')
        self.frames = {'blink': [], 'default': []}
        fold_name = 'eyes_alt'
        for state in self.frames.keys():
            for folder_path, _, file_names in walk(join('animations', fold_name, state, 'L')):
                    if file_names:
                        for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                            full_path = join(folder_path, file_name)
                            # print(full_path)
                            surf = pygame.image.load(full_path).convert_alpha()
                            if self.full_resize > 1:
                                surf = pygame.transform.scale_by(surf, self.full_resize)
                            self.frames[state].append(surf)
    def alt_offsets(self):
        self.offsets = {'blink': pygame.math.Vector2((170, -30)), 'default': pygame.math.Vector2((170, -60))}
        self.turn_offset = pygame.math.Vector2((50, 10))
    
    def head_turn(self, pos):
        offset_vector = WINDOW_CENTER - pygame.math.Vector2(pos)
        offset_dist = pygame.math.Vector2(abs(offset_vector.x), abs(offset_vector.y))
        # move_factor = offset_dist.elementwise() / WINDOW_RADIUS
        # move_mag = pygame.math.Vector2((pygame.math.smoothstep(1, 0, move_factor.x), pygame.math.smoothstep(1, 0, move_factor.y)))
        move_mag = offset_vector.elementwise() / WINDOW_RADIUS
        actual_offset = pygame.math.Vector2((0,0))
        if offset_dist.x < 0:
            # print("face is on the right side so left eye is on the inside")
            actual_offset.x = self.turn_offset.x * -1

        elif offset_dist.x > 0:
            # print("face is on the left side so left eye is on the outside")
            actual_offset.x  = self.turn_offset.x *EYE_OFFSET_SCALE[0]

        if offset_dist.y < 0:
            actual_offset.y = self.turn_offset.y * -1
        
        return actual_offset.elementwise() * move_mag
        


    def scale_eyes(self, pos=pygame.math.Vector2((0,0))):
        if SEPERATE_EYE_SCALING:
            pos = self.rect.center
        offset_vector = WINDOW_CENTER - pygame.math.Vector2(pos)
        offset_dist = pygame.math.Vector2(abs(offset_vector.x), abs(offset_vector.y))
        scale_factor = offset_dist.elementwise() / WINDOW_RADIUS
        # scale_inv = pygame.math.Vector2((1,1))-scale_factor
        # scale_mag = pygame.math.Vector2((pygame.math.lerp(0.7, 1, scale_inv.x, True), pygame.math.lerp(0.7, 1, scale_inv.y, True)))
        scale_mag = pygame.math.Vector2((pygame.math.smoothstep(1, EYE_SCALE_BASE[0], scale_factor.x), pygame.math.smoothstep(1, EYE_SCALE_BASE[1], scale_factor.y)))
        # print(scale_inv)
        # print(scale_mag)

        #TODO look into the funky warping of scaling may have to separate the individual eyes
        self.image = pygame.transform.scale_by(self.image, scale_mag)
        # self.image = pygame.transform.scale_by(self.image, 1.1)

        # print(window_radius)

        # self.image = pygame.transform.scale_by(self.image,)
        # print(offset_norm)

    def move(self, pos):
        self.rect.center = pos + self.offsets[self.state] 
        if OFFSET_EYES_ON_MOVE:
            self.rect.center += self.head_turn(pos)
        if SCALE_EYES_ON_MOVE:
            self.scale_eyes(pos)
            self.rect = self.image.get_frect(center = pos + self.offsets[self.state])


    def animate(self, key, dt):
        self.state = key
        self.image = self.frames[self.state][pygame.math.clamp(int(self.frame_index), 0, len(self.frames[self.state])-1)]

    def update(self, dt):
        # self.timestamp += dt
        # self.animate('none', dt)
        pass

class EyeR(pygame.sprite.Sprite):
    def __init__(self, pos, groups, alt=False, full_resize=1):
        super().__init__(groups)
        self.use_alt_img_format = alt
        self.full_resize = full_resize

        self.load_images()
        # print(join('animations', 'eyes', 'default', '1'))
        self.alt_offsets()
        self.image = pygame.image.load(join('animations', 'eyes_alt', 'default', 'R', '1.png')).convert_alpha()
        self.state, self.frame_index = 'default', 0
        self.rect = self.image.get_frect(center = pos)
        self.anim_rate = 24
        self.timestamp = 0.0


    def load_images(self):
        self.frames = {'blink': [], 'default': []}
        fold_name = 'eyes_alt'
        for state in self.frames.keys():
            for folder_path, _, file_names in walk(join('animations', fold_name, state, 'R')):
                    if file_names:
                        for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                            full_path = join(folder_path, file_name)
                            # print(full_path)
                            surf = pygame.image.load(full_path).convert_alpha()
                            if self.full_resize > 1:
                                surf = pygame.transform.scale_by(surf, self.full_resize)
                            self.frames[state].append(surf)
    def alt_offsets(self):
        self.offsets = {'blink': pygame.math.Vector2((-170, -30)), 'default': pygame.math.Vector2((-170, -60))}
        self.turn_offset = pygame.math.Vector2((50, 10))

    def head_turn(self, pos=pygame.math.Vector2((0,0))):
        offset_vector = WINDOW_CENTER - pygame.math.Vector2(pos)
        offset_dist = pygame.math.Vector2(abs(offset_vector.x), abs(offset_vector.y))
        # move_factor = offset_dist.elementwise() / WINDOW_RADIUS
        # move_mag = pygame.math.Vector2((pygame.math.smoothstep(1, 0, move_factor.x), pygame.math.smoothstep(1, 0, move_factor.y)))
        move_mag = offset_vector.elementwise() / WINDOW_RADIUS
        actual_offset = pygame.math.Vector2((0,0))
        if offset_dist.x < 0:
            # print("face is on the right side so the right eye is on the outside")
            actual_offset.x = (self.turn_offset.x * -1)*EYE_OFFSET_SCALE[0]

        # elif offset_dist.x > 0:
        #     print("face is on the left side so the right eye is on the inside")
        #     actual_offset.x  = self.turn_offset.x /2

        if offset_dist.y < 0:
            actual_offset.y = self.turn_offset.y * -1
        
        return actual_offset.elementwise() * move_mag


    def scale_eyes(self, pos):
        if SEPERATE_EYE_SCALING:
            pos = self.rect.center
        offset_vector = WINDOW_CENTER - pygame.math.Vector2(pos)
        offset_dist = pygame.math.Vector2(abs(offset_vector.x), abs(offset_vector.y))
        scale_factor = offset_dist.elementwise() / WINDOW_RADIUS
        # scale_inv = pygame.math.Vector2((1,1))-scale_factor
        # scale_mag = pygame.math.Vector2((pygame.math.lerp(0.7, 1, scale_inv.x, True), pygame.math.lerp(0.7, 1, scale_inv.y, True)))
        scale_mag = pygame.math.Vector2((pygame.math.smoothstep(1, EYE_SCALE_BASE[0], scale_factor.x), pygame.math.smoothstep(1, EYE_SCALE_BASE[1], scale_factor.y)))
        # print(scale_inv)
        # print(scale_mag)

        #TODO look into the funky warping of scaling may have to separate the individual eyes
        self.image = pygame.transform.scale_by(self.image, scale_mag)
        # self.image = pygame.transform.scale_by(self.image, 1.1)

        # print(window_radius)

        # self.image = pygame.transform.scale_by(self.image,)
        # print(offset_norm)
    def move(self, pos):
        self.rect.center = pos + self.offsets[self.state] 
        if OFFSET_EYES_ON_MOVE:
            self.rect.center += self.head_turn(pos)
        if SCALE_EYES_ON_MOVE:
            self.scale_eyes(pos)
            self.rect = self.image.get_frect(center = pos + self.offsets[self.state])


    def animate(self, key, dt):
        self.state = key   
        self.image = self.frames[self.state][pygame.math.clamp(int(self.frame_index), 0, len(self.frames[self.state])-1)]

    def update(self, dt):
        # self.timestamp += dt
        # self.animate('none', dt)
        pass