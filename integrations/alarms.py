import datetime
import os
import asyncio
import json
from commands.validators import AlarmModelv2 as AlarmModel
from safe_shutdown import shutdown


def convert_to_datetime(event_str:str):

    format_string = "%Y-%m-%d %H:%M:%S"

    datetime_object = datetime.strptime(event_str, format_string)

    return datetime_object

async def spawn_timer(hours: int, minutes: int, seconds: int, description: str = ""):
    print(f"Started timer for {description}")
    duration = convert_timer(hours, minutes, seconds)

    try:
        await asyncio.wait_for(shutdown.wait(), timeout=duration)
        print(f"Timer '{description}' was cancelled by shutdown.")
    except asyncio.TimeoutError:
        print(f"Timer '{description}' completed after {duration} seconds.")

    # #wait for speaker to finish queued tasks
    # async with speaker_lock:
    #     print("Playing something through the speakers")

    return description

def convert_timer(hours, minutes, seconds):
    assert(seconds < 60)
    assert(minutes < 60)
    duration = seconds + minutes * 60 + hours * 60 * 60
    return duration

class Alarms:
    #should i change all to async withs?
    def __init__(self, file_name="alarms"):
        self.alarms_spawned = 0
        self.alarm_list = {}
        self.id = 0
        self.alarm_lock = asyncio.Lock()
        
        self.load_alarm_file(self.path_alarm_file(file_name))
        self.check_alarms()
        #self.previous_check = datetime.datetime.now()

    async def add_alarm(self, alarm_model:AlarmModel):
        await self.alarm_lock.acquire()
        # self.alarm_list[self.id] = [self.fix_alarm(self.convert_24hr_model(alarm_model)), alarm_model.note] #for alarm model v1
        self.alarm_list[self.id] = [convert_to_datetime(alarm_model.alarm_date), alarm_model.note]
        self.id += 1
        self.alarm_lock.release()

    async def add_alarm_dt(self, alarm_dt, note=""):
        await self.alarm_lock.acquire()
        # self.alarm_list[self.id] = [self.fix_alarm(self.convert_24hr_model(alarm_model)), alarm_model.note] #for alarm model v1
        self.alarm_list[self.id] = [alarm_dt, note]
        self.id += 1
        self.alarm_lock.release()

    async def check_alarms(self):
        if self.alarms_spawned >= 1:
            print("Already spawned the alarm thread, closing this one.")
            return

        async with self.alarm_lock:
            self.alarms_spawned += 1

        while not shutdown.is_set():
            print("Checking alarms...")
            
            async with self.alarm_lock:
                if len(self.alarm_list.keys()) < 1:
                    print("No alarms, closing alarm thread.")
                    break

                for id in list(self.alarm_list.keys()):
                    alarm_obj = self.alarm_list[id]
                    if self.check_alarm(alarm_obj[0]):
                        alarm_message = f"Your alarm at {alarm_obj[0].hour}:{alarm_obj[0].minute} is finished and your note was: {alarm_obj[1]}"
                        print(alarm_message)
                        # Call hardware function here
                        self.remove_alarm(id)

                self.autosave_alarms()

            try:
                await asyncio.wait_for(shutdown.wait(), timeout=30)
            except asyncio.TimeoutError:
                continue

    
    async def remove_alarm(self, id):
        await self.alarm_lock.acquire()
        del self.alarm_list[id]
        self.alarm_lock.release()

#TODO offload check_alarms to the init function because the file is open and doesn't get closed before autosaving
    def load_alarm_file(self, path:str):
        with open(path, 'r') as alarm_file:
            alarms_saved = json.load(alarm_file)['alarms']
            if len(alarms_saved) > 0:
                for alarm_json in alarms_saved:
                    #i believe I can just use the add function and await it to finish but I'd rather just initialize everything linearly without locking
                    self.alarm_list[self.id] = [self.convert_datetime(alarm_json), alarm_json['note']]
                    self.id += 1
            alarm_file.close()

    def path_alarm_file(self, file_name):
        dir_path = os.path.dirname(__file__)
        full_path = os.path.join(dir_path, f"{file_name}.json")
        return full_path

    def convert_24hr_json(alarm_json):
        return {
            'hour': alarm_json['hour'] + (12 if alarm_json['meridian'] in ['PM', 'pm'] else 0),
            'minute': alarm_json['minute'],
            'second': alarm_json['second'],
            'note': alarm_json['note']
        }
    
    def convert_24hr_model(alarm_model:AlarmModel):
        alarm_model.hour = alarm_model.hour + (12 if alarm_model.meridian in ['PM', 'pm'] else 0)
        return alarm_model
    
    def convert_datetime(alarm_json):
        now = datetime.datetime.now()
        alarm_obj = datetime.datetime(now.year, now.month, now.day, alarm_json['hour'], alarm_json['minute'], alarm_json['seconds'])
        return alarm_obj

    def fix_alarm(alarm):
        if(alarm < datetime.datetime.now()):
            return datetime.datetime(alarm.year, alarm.month, alarm.day+1, alarm.hour, alarm.minute, alarm.second)
        
    def autosave_alarms(self, path="~/alarms.json"):
        alarms_json = []
        for id in self.alarm_list.keys():
            alarm_obj = self.alarm_list[id]
            alarms_json.append(self.convert_json(alarm_obj[0], alarm_obj[1]))

        alarms ={'alarms':alarms_json}
        with open(path, 'w') as alarm_file: 
            alarm_file.write(json.dumps(alarms, indent=4))
            alarm_file.close()

             

    def check_alarm(self, alarm):
        #checks if the time for the alarm to go off has passed
        #has_passed = False
        if(alarm < datetime.datetime.now()):
            return True
            #has_passed = True
            #self.previous_check = datetime.datetime.now()
        return False
    
    def convert_json(alarm, note):
        return {'year':alarm.year,
                'month':alarm.month,
                'day': alarm.day,
                'hour':alarm.hour,
                'minute': alarm.minute,
                'second': alarm.second,
                'note': note}
    
    def convert_from_validator(self, alarm_model:AlarmModel):
        assert alarm_model.hour < 12 & alarm_model.hour >= 0, 'alarm hour is outside of bounds, failed to spawn alarm'
        assert alarm_model.minute < 60 & alarm_model.minute >= 0, 'alarm minute is not within proper bounds, failed to spawn alarm'
        assert alarm_model.meridian in ['AM','am','PM','pm'], 'not a valid meridian'
        alarm_model = self.convert_24hr_model(alarm_model)
        now = datetime.datetime.now()
        alarm_obj = datetime.datetime(now.year, now.month, now.day, alarm_model.hour, alarm_model.minute, alarm_model.second)
        return alarm_obj
    
    def snooze(hours=0, minutes=10, seconds=0):
        spawn_timer(hours, minutes, seconds)


