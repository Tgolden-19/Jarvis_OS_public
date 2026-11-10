import uuid
from datetime import datetime, timedelta
from pathlib import Path
from commands.validators import CalendarModel
from integrations.alarms import convert_to_datetime, Alarms

from icalendar import Calendar, Event

DEBUG = True


CALENDAR_DIR = Path("calendars")
CALENDAR_DIR.mkdir(exist_ok=True)

calendar_alarms = Alarms("calendar_alarms")
def create_calendar(name: str) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//My BMOS Calendar//mxm.dk//")
    cal.add("version", "2.0")
    save_calendar(name, cal)
    if DEBUG:
        print(f"Calendar '{name}.ics' created.")
    return cal

def get_date():
    now = datetime.now()
    return now.year, now.strftime("%B"), now.day

def get_date_str():
    year, month, day =  get_date
    return(f'today\'s date is {month}-{day}-{year}')

def get_dow():
    return datetime.now().strftime("%A")

def load_calendar(name: str) -> Calendar:
    path = CALENDAR_DIR / f"{name}.ics"
    if not path.exists():
        raise FileNotFoundError(f"Calendar '{name}' not found.")
    with open(path, "rb") as f:
        cal = Calendar.from_ical(f.read())
    return cal


def save_calendar(name: str, cal: Calendar):
    with open(CALENDAR_DIR / f"{name}.ics", "wb") as f:
        f.write(cal.to_ical())

#TODO add repeating events and debloat alarms maybe limit the number of you can add to alarms normally
def add_event(
    cal: Calendar,
    to_add:CalendarModel, alarms:Alarms = None
):
    event = Event()
    event.add("summary", to_add.title)
    event.add("dtstart", convert_to_datetime(to_add.start_date))
    event.add("dtend", convert_to_datetime(to_add.end_date))
    event.add("dtstamp", datetime.now())
    event.add("uid", str(uuid.uuid4()))
    event.add("description", to_add.description)
    if to_add.alert >= 0 and alarms != None:
        alarms.add_alarm_dt(convert_to_datetime(to_add.start_date) - timedelta(minutes=to_add.alert))
    if to_add.second_alert > 0 and alarms != None:
        alarms.add_alarm_dt(convert_to_datetime(to_add.start_date) - timedelta(minutes=to_add.second_alert))
    #not supported by BMOS yet
    # event.add("location", location)
    if to_add.frequency:
        rrule = {'freq': to_add.frequency.upper()}  # e.g., 'DAILY', 'WEEKLY'
        
        # Weekly recurrence with specific days of week
        if to_add.frequency.lower() == 'weekly' and to_add.dow:
            # Convert list of bools to weekday names (ICAL format)
            day_map = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
            byday = [day_map[i] for i, v in enumerate(to_add.dow) if v]
            if byday:
                rrule['byday'] = byday
        
        # Optional: limit number of recurrences
        if to_add.end_date:
            until = convert_to_datetime(to_add.end_date)
            rrule['until'] = until

        event.add('rrule', rrule)
        
    cal.add_component(event)
    if DEBUG:
        print(f"Event '{to_add.note}' added.")


def list_events(cal: Calendar):
    print("Events in calendar:")
    for component in cal.walk():
        if component.name == "VEVENT":
            print(f"- {component.get('summary')} ({component.get('dtstart').dt}) | UID: {component.get('uid')}")



def remove_event_by_uid(cal: Calendar, uid: str) -> bool:
    for component in list(cal.subcomponents):
        if component.name == "VEVENT" and str(component.get("uid")) == uid:
            cal.subcomponents.remove(component)
            if DEBUG:
                print(f"Event with UID {uid} removed.")
            return True
    if DEBUG:
        print(f"No event with UID {uid} found.")
    return False


#TODO ADD RECURRENT EVENTS
#TODO add icalendar alarms integration (maybe ignore this one)
#TODO add icloud sync without moving ics files
#TODO add google calendar support for the freaks who use google calendar instead of their phone calendar