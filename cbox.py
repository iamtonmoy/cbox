from websocket import create_connection
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import configparser
import os
import re
import sys
import json
from requests import Session


# Reading the configs
config = configparser.ConfigParser()
config.read('config.cfg')

SSL = False

# Patterns & Session Type [Defaults]
session_type = 'ws'
pattern0 = r'<title>([^<]+)</title>'
pattern1 = r"wsuri_alts:(\{[^\}]+\})"
pattern1a = 'ws'
pattern2 = r'flrqs:\s?\"([^\"]+)\",'


# Setting up max_connections count
try:
    max_connections = int(config.get('online', 'max_connections').strip())
except Exception as e:
    print('-> ERR_CONFIG_READ', e)
    print('\n\t(Setting Default connections limit to `300`)')
    max_connections = 300

# Session Type
try:
    SSL = config.get('session', 'ssl').strip() == 'True'
except Exception as e:
    print('-> ERR_CONFIG_READ', e)
    print('\n\t(Session is set not to use ssl config)')
    SSL = False

if SSL:
    session_type = 'wss'
    pattern1a = "wss"


# Command Line Args
try:
    if int(sys.argv[-1]):
        max_connections = int(sys.argv[-1])
except:
    pass

try:
    os.system(
        f'title CBox Online Users Utility v1.0.1 - MK [{max_connections}] [SSL: {"On" if SSL else "Off"}]')
except:
    pass


# Verify chcat_link
def check_ws(link: str, checked: bool = False) -> bool:
    try:
        ws = create_connection(link)
        _ = ws.recv()
        return True
    except Exception as e:
        if not checked:
            return check_ws(link, True)

    return False


# Retreives Chats
def retrieve_chats(chat_link: str, checked: bool = False) -> tuple[str, list]:
    with Session() as s:
        s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
        })
        try:
            res = s.get(chat_link)
            if finds1_text := re.findall(pattern1, res.text):
                finds1_data = json.loads(finds1_text[0])
                finds1 = finds1_data[pattern1a]

                if finds2 := re.findall(pattern2, res.text):
                    if title := re.findall(pattern0, res.text):
                        title = title[0]
                    else:
                        title = ""

                    return title, [
                        f'{session_type}://'+find + finds2[0]
                        for find in finds1
                    ]
        except Exception as e:
            print('-> ERR_RETRIEVE_CHAT ->', chat_link, '->', e)
            if not checked:
                print("Try again to retrieve chats for", chat_link)
                return retrieve_chats(chat_link, True)


# Spawns New User
def increase_state(chat_room_link: str, title: str = "", spawn_index: int = 0) -> None:
    # Tries to increase 10 times (In case of any exception)
    ERR_COUNT = 0
    ERRORS = []
    for i in range(20):
        try:
            ws = create_connection(chat_room_link)
            print(f'-> Spawned User -> {title} -> [{spawn_index+1}]')

            while True:
                _ = ws.recv()
                time.sleep(3)
        except Exception as e:
            ERR_COUNT += 1
            ERRORS.append(str(e))

        if ERR_COUNT > 10:
            break

        time.sleep(0.5)

    if ERRORS:
        print('ERR_SPAWN_FUNC', chat_room_link, spawn_index+1, ERRORS)


print('''
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#      I will not be responsible for any misuse of this tool.     #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
''')

time.sleep(2)

chats = []
chat_rooms = []

if not os.path.exists(os.path.join(os.getcwd(), 'urls.txt')):
    print('-> ERR_URLS_FILE_NOT_FOUND\n\t(Exiting in 3 secs...)')
    time.sleep(3)
    sys.exit()

with open('urls.txt', 'r', encoding='utf-8') as f:
    chats = [l.strip() for l in f.read().split(
        '\n') if l.strip() and not l.startswith('#')]

if not chats:
    print('-> Could not found chat urls\n\t(exiting in 2 seconds)')
    time.sleep(2)
    sys.exit()


print('-> Retrieving Chats ->', len(chats))
for chat_link in chats:
    if chat_room_info := retrieve_chats(chat_link):
        for ws_link in chat_room_info[1]:
            if check_ws(ws_link):
                print(f"-> {chat_link} -> {chat_room_info[0]} -> {ws_link}")
                chat_rooms.append([chat_room_info[0], ws_link])
                break

print('-> Retrieval Complete ->', len(chat_rooms))
time.sleep(1)

if chat_rooms:
    print('-> Setting up `anonymous` users')
    total_chats = [
        chat_room_info
        for chat_room_info in chat_rooms
        for i in range(0, max_connections)
    ]

    with ThreadPoolExecutor(max_workers=len(total_chats)) as exec:
        tasks = [
            exec.submit(increase_state,
                        chat_room_info[1], chat_room_info[0], spawn_index+1)
            for spawn_index, chat_room_info in enumerate(total_chats)
        ]

        for task in as_completed(tasks):
            try:
                _ = task.result()
            except Exception as e:
                pass
else:
    print("No chatrooms found!!")
