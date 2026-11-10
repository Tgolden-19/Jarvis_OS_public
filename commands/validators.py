from pydantic import BaseModel
from typing import Optional


class CommandModel(BaseModel):
    command:str

class WeatherModel(CommandModel):
    time_frame:str
    location:Optional[str]
    search_type:Optional[str]

class PlaybackModel(CommandModel):
    action:str
    media:Optional[str]
    artist:Optional[str]
    song:Optional[str]
    playlist:Optional[str]
    repeat:Optional[str]
    shuffle:Optional[str]
    volume:Optional[int]

class MusicSearchModel(CommandModel):
    album:str
    artist:str
    song:str
    playlist:Optional[str]

class TimerModel(CommandModel):
    second:int
    minute:Optional[int]
    hour:Optional[int]
    note:Optional[str]

class AlarmModelv1(CommandModel):
    second:int
    minute:int
    hour:int
    meridian:str
    note:Optional[str]

class AlarmModelv2(CommandModel):
    alarm_date:str
    note:Optional[str]

class CalendarModel(CommandModel):
    action:str
    title:str
    frequency:Optional[str]
    start_date:Optional[int]
    end_date:Optional[int]
    alert:Optional[int]
    second_alert:Optional[int]
    dow:Optional[list[bool]]
    description:Optional[str]

class NoteModel(CommandModel):
    action:str
    title:str
    content:Optional[str]
    extension:Optional[str]