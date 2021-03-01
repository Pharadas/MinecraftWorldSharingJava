import subprocess
import python_nbt.nbt as nbt
import os.path
from os import path
import requests
import json
from bs4 import BeautifulSoup
from leveldat_class import LeveldatWorldInfo
import struct

class LeveldatWorldInfo:
    def __init__(self, worldName):
        self.worldName = worldName
        userName = str(subprocess.check_output('whoami', shell=True)).split('\\')[-3]
        self.absPath = f'C:/Users/{userName}/AppData/Roaming/.minecraft/saves/{worldName}' # get absolute path of world to be modified
        self.worldLeveldat = nbt.read_from_nbt_file(f'{self.absPath}/level.dat')
        self.gameType = 0
        self.spawnCoords = 0

    def get_default_gamershit(self): # get data needed to create new player from a template
        self.gameType = self.worldLeveldat['Data']['GameType']
        self.spawnCoords = nbt.TAG_List([
            self.worldLeveldat['Data']['SpawnX'], 
            self.worldLeveldat['Data']['SpawnY'], 
            self.worldLeveldat['Data']['SpawnZ']], )

        spawnCoordJson = self.spawnCoords.json_obj(full_json=True)
        spawnCoordJson['tag_type_id'] = 6
        self.spawnCoords = nbt.from_json(spawnCoordJson)

class Player:
    def __init__(self, worldName):
        self.worldName = worldName
        self.userName = str(subprocess.check_output('whoami', shell=True)).split('\\')[-3]
        self.absWorldPath = f'C:/Users/{self.userName}/AppData/Roaming/.minecraft/saves/{worldName}' # get absolute path of world to be modified
        self.absPlayerPath = ''
        self.playerUUID = ''

    def parse_to_UUID_array(self, hex_UUID):
        hex_UUID = hex_UUID.replace('-', '') # convert hex to array uuid
        result = [hex_UUID[0:8], hex_UUID[8:16], hex_UUID[16:24], hex_UUID[24:32]]
        return [struct.unpack('>i', bytes.fromhex(i))[0] for i in result]

    def unparse_UUID_array(self, UUID_array): # convert array to hex uuid  
        result = ''
        for i in UUID_array:
            negative = False if i >= 0 else True
            num = abs(i)
            binaryResult = ''

            while num >= 1:
                num = num / 2
                if int(num) != num:
                    binaryResult += '1'
                else:
                    binaryResult += '0'
                num = int(num)

            binaryResult = '0' * (32 - len(binaryResult)) + binaryResult[::-1]
            if negative: binaryResult = ''.join(['0' if i == '1' else '1' for i in binaryResult])
            result += hex(int(binaryResult, 2) + 1)[2:] if negative else hex(int(binaryResult, 2))[2:]

        return f'{result[0:8]}-{result[8:12]}-{result[12:16]}-{result[16:20]}-{result[20:32]}'

    def get_player_UUID(self):
        while self.playerUUID == '': # look name up in mcuuid
            lookUpName = input('what is your nickname? ')
            uuidRequest = requests.get(f'https://mcuuid.net/?q={lookUpName}')
            soup = BeautifulSoup(uuidRequest.text, 'lxml')
            self.playerUUID = soup.find(id="results_id")['value']
            if self.playerUUID == '':
                print('name not found')

        self.playerUUIDArray = self.parse_to_UUID_array(self.playerUUID)

        with open('localUUID.txt', mode='w') as saveUUID:
            saveUUID.write(f'{self.playerUUID}\n{str(self.playerUUIDArray)}') # save player uuid and uuid array to 'localUUID.txt'

    def get_player_metadata(self):
        with open('localUUID.txt') as savedPlayerUUID:
            playerUUIDRead = savedPlayerUUID.read()
            if playerUUIDRead == '':
                get_player_UUID()
            else:
                playerUUIDRead = playerUUIDRead.split('\n')
                self.playerUUID = playerUUIDRead[0]
                self.playerUUIDArray = playerUUIDRead[1].replace(',', '')
                self.playerUUIDArray = [int(i) for i in self.playerUUIDArray[1:-1].split(' ')]

        self.absPlayerPath = f'{self.absWorldPath}/playerdata/{self.playerUUID}.dat'

    def is_player_in_world(self):
        if path.exists(f'{self.absWorldPath}/playerdata/{self.playerUUID}'):
            return True
        else:
            return False

    def move_existing_remote_player_to_local_player(self):
        world = LeveldatWorldInfo(self.worldName)

        # get remoter player's data
        remotePlayerData = nbt.read_from_nbt_file(self.absPlayerPath)
        
        # overwrite local player's data with remote player's
        world.worldLeveldat['Data']['Player'] = remotePlayerData
        nbt.write_to_nbt_file(f'{self.absWorldPath}/level.dat', world.worldLeveldat)

    def move_local_player_to_remote_player(self): # probably wont use this function
        world = LeveldatWorldInfo(self.worldName)

        # get current local player's data
        currLocalPlayer = world.worldLeveldat['Data']['Player']
        currLocalPlayerUUID = self.unparse_UUID_array(currLocalPlayer['UUID'].json_obj(full_json=True)['value'])

        # move current local player's data to it's player remote data
        nbt.write_to_nbt_file(f'{self.absWorldPath}/playerdata/{currLocalPlayerUUID}.dat', currLocalPlayer)

    def setup_template_for_player(self):
        playerTemplate = nbt.read_from_nbt_file('GamerJuice.dat')
        world = LeveldatWorldInfo(self.worldName)
        world.get_default_gamershit()

        playerTemplate['playerGameType'] = world.gameType
        playerTemplate['Pos'] = world.spawnCoords
        playerTemplate['UUID'] = nbt.TAG_Int_Array(self.playerUUIDArray)
        world.worldLeveldat['Data']['Player'] = playerTemplate

        nbt.write_to_nbt_file(f'{self.absWorldPath}/level.dat', world.worldLeveldat)
        nbt.write_to_nbt_file(f'{self.absWorldPath}/level.dat_old', world.worldLeveldat)
