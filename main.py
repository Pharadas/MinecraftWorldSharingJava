from playerInfo_class import LeveldatWorldInfo, Player
import json
import subprocess
import os

print('Your worlds are:')
userName = str(subprocess.check_output('whoami', shell=True)).split('\\')[-3]
for i in os.listdir(f'C:/Users/{userName}/AppData/Roaming/.minecraft/saves'):
    print(f'    {i}')

print('')
absWorldPath = ''

while not os.path.exists(absWorldPath):
    worldName = input('Which world do you want to modify? ')
    absWorldPath = f'C:/Users/{userName}/AppData/Roaming/.minecraft/saves/{worldName}'
    if not os.path.exists(absWorldPath):
        print("This world doesn't exist, try another one ")

player = Player(worldName)

with open('Options.json') as options:
    jsonOptions = json.load(options)

if not jsonOptions['Remember UUID']:
    player.get_player_UUID()
else:
    player.get_player_metadata()

if player.is_player_in_world():
    player.move_existing_remote_player_to_local_player()
else:
    player.setup_template_for_player()
