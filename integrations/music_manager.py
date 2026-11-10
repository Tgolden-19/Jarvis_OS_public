import requests
from dotenv import load_dotenv
import os
import json
import asyncio

load_dotenv()

spotify_key = os.getenv('SPOTIFY_API_KEY')

async def get_playback_status():
    endpoint = 'https://api.spotify.com/v1/me/player'
    header = {'Authorization': 'Bearer ' + spotify_key}
    response = requests.get(endpoint, headers=header)
    if response.status_code == 200:
        return response.json()
    else:
        print('Error occured: '+ response.status_code, response.text)
        return None
    
async def get_devices():
    endpoint = 'https://api.spotify.com/v1/me/player/devices'
    header = {'Authorization': 'Bearer ' + spotify_key}
    response = requests.get(endpoint, headers=header)
    if response.status_code == 200:
        device_list = []
        devices = response.json()['devices']
        for device in devices:
            device_list.append({'id': device['id'], 'name': device['name']})
        return device_list
    else:
        print('Error occured: '+ response.status_code, response.text)
        return None
    
async def change_devices(id):
    endpoint = 'https://api.spotify.com/v1/me/player'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {
    "device_ids": [
        id
        ]
    }
    response = requests.put(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("Changed device successfully!")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 
    
async def get_playing_track():
    endpoint = 'https://api.spotify.com/v1/me/player/currently-playing'
    header = {'Authorization': 'Bearer ' + spotify_key}
    response = requests.get(endpoint, headers=header)
    if response.status_code == 200:
        device= response.json()['device']
        track= response.json()['item']
        time= response.json()['progress_ms']
        album= track['album']
        artists= track['artists']
        names= []
        ids=[]
        for artist in artists:
            names.append(artist['name'])
            ids.append(artist['id'])

        values= {'device_id': device['id'],
                 'device_name': device['name'],
                 'time': time,
                 'song_name': track['name'],
                 'song_id': track['id'],
                 'artist_names': names,
                 'artist_ids':ids,
                 'album_name': album['name'],
                 'album_id': album['id']
                 }
    else:
        print('Error occured: '+ response.status_code, response.text)
        return None
    
async def pause_playback(id):
    endpoint = 'https://api.spotify.com/v1/me/player/pause'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {"device_id":id}
    response = requests.put(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("Paused playback successfully!")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 
    
async def start_playback(id, time=0):
    #leaving default time will restart current song
    endpoint = 'https://api.spotify.com/v1/me/player/play'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {"position_ms": time}
    response = requests.put(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("Started/resumed playback successfully!")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 
    
async def next_song(id):
    endpoint = 'https://api.spotify.com/v1/me/player/next'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {"device_id":id}
    response = requests.put(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("Started next song successfully!")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 
    
async def previous_song(id):
    endpoint = 'https://api.spotify.com/v1/me/player/previous'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {"device_id":id}
    response = requests.put(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("Started previous song successfully!")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 
    
async def set_repeat(id, repeat='context'):
    endpoint = 'https://api.spotify.com/v1/me/player/repeat'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {'state':repeat,"device_id":id}
    response = requests.put(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("set repeat to: " + repeat + " successfully!")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 
    
async def set_shuffle(id, shuffle=False):
    endpoint = 'https://api.spotify.com/v1/me/player/shuffle'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {'state':shuffle,"device_id":id}
    response = requests.put(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("set shuffle to: " + shuffle + " successfully!")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 

async def set_volume(id, percentage=60):
    endpoint = 'https://api.spotify.com/v1/me/player/volume'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {'volume_percent':percentage,"device_id":id}
    response = requests.put(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("set volume to: " + str(percentage/100) + " successfully!")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 

async def get_queue():
    endpoint = 'https://api.spotify.com/v1/me/player/queue'
    header = {'Authorization': 'Bearer ' + spotify_key}
    response = requests.get(endpoint, headers=header)
    if response.status_code == 200:
        song_queue = []
        queue = response.json()['queue']
        for song in queue:
            song_queue.append({'id': song['id'], 'name': song['name']})
        return song_queue
    else:
        print('Error occured: '+ response.status_code, response.text)
        return None   

async def set_volume(id, song_id):
    endpoint = 'https://api.spotify.com/v1/me/player/queue'
    header = {'Authorization': 'Bearer ' + spotify_key}
    body = {'uri':'spotify%3Atrack%3A'+ song_id,"device_id":id}
    response = requests.post(endpoint, headers=header, body=body)
    if response.status_code == 204:
        print("added song id: " + song_id + "to the queue")
        return
    else:
        print('Error occured: '+ response.status_code, response.text)
        return 

#@TODO    
async def cycle_shuffle():
    pass

async def change_shuffle():
    pass