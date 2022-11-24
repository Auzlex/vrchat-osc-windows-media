# original base script forked from o0F-0oF, modified by Auzlex, then massacred by Tatzie and cleaned up again by Auzlex translation fixed by Hypezz
import os
import sys
import ctypes
import time
import asyncio

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name)

from pythonosc.udp_client import SimpleUDPClient
from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    SessionsChangedEventArgs,
)

spotifyName = ""
a = ["", True]
b = [f"{spotifyName}", True]
ip = "127.0.0.1"
port = 9000
client = SimpleUDPClient(ip, port)
EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
gatekeep_send = False
last_b = b

async def get_media_info():
    sessions = await MediaManager.request_async()

    info_dict = None # information is none until we get it
    playback_info = None

    # This source_app_user_model_id check and if statement is optional
    # Use it if you want to only get a certain player/program's media
    # (e.g. only chrome.exe's media not any other program's).

    # To get the ID, use a breakpoint() to run sessions.get_current_session()
    # while the media you want to get is playing.
    # Then set TARGET_ID to the string this call returns.

    current_session = sessions.get_current_session()

    if current_session:  # there needs to be a media session running
        #if current_session.source_app_user_model_id == TARGET_ID:
        # TODO crashes here sometimes - not ready
        info = await current_session.try_get_media_properties_async()

            # song_attr[0] != '_' ignores system attributes
        info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}

            # converts winrt vector to list
        info_dict['genres'] = list(info_dict['genres'])

        playback_info = current_session.get_playback_info()

    return info_dict, playback_info

    # It could be possible to select a program from a list of current
    # available ones. I just haven't implemented this here for my use case.
    # See references for more information.

def send_m(b):
    """Send media info to OSC server."""
    if last_b != b[0]:
        last_b = b[0]
        client.send_message("/chatbox/input", b) # force send the message again because it is stopped by the boolean gatekeep_send

while(True):

    current_media_info, playback_info = asyncio.run(get_media_info())

    #print(playback_info)

    # we check if we have media to check the media type is music
    if current_media_info is None or playback_info is None:
            b[0] = "[No Media]"
            print("all info is not available, please start playing something on your computer through windows media controls")
    else:

        media_playback_type = 0 # 1 = music, 2 = video, 3 = image

        try:
            media_playback_type = int(current_media_info['playback_type'])
        except Exception as e:
            print("An error occured when trying to get the media playback type, defaulting to 0, please play and pause media content on your computer through windows media controls to possibly fix this issue.. else report this issue to the developer")
            print(e)

        # we check if the media type is music
        if media_playback_type != 1:
            
            print("this is not music -> please play music through windows media controls")
            b[0] = "[Media is playing but not music]"

        else:

            print(f"all info is available -> status isplaying: {playback_info.playback_status == PlaybackStatus.PLAYING}")

            if playback_info.playback_status == PlaybackStatus.PLAYING:
                b[0] = f"{current_media_info.get('artist')} - {current_media_info.get('title')}"
                gatekeep_send = False # send message
            else:
                
                # check if we can send the message
                if gatekeep_send == False:
                    
                    gatekeep_send = True # stop sending messages

                    # combines the artist and title into one string
                    msg = f"{current_media_info.get('artist')} - {current_media_info.get('title')}"

                    # we add the pause message to the list
                    b[0] = f"[PAUSED] {msg}"

                    send_m(b) # invoke our send message procedure

        # check if we can send the message
        if gatekeep_send is False:
            send_m(b) # invoke our send message procedure

    time.sleep(2)