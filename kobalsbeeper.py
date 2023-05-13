import os
import random
import json
import pprint

from uuid import UUID

import pygame
import pyttsx3
import asyncio

from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.pubsub import PubSub
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.helper import first
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand


Test = True

openMouth = "open.png"
closedMouth = "close.png"
backgroundColor = "#000000"

voiceID = ""

shakeAmount = "2"

display_width = 512
display_height = 512

talking = 0

twitchAppId = ""
twitchAppSecret = ""
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CHANNEL_READ_REDEMPTIONS]
channelName = ""

pointId = "tts"

class _TTS:
    
    engine = None
    rate = None
    
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("voice", voiceID)
    
    def start(self,text_):
        self.engine.say(text_)
        self.engine.runAndWait()

def configLine(name,value,comment):
    return "\n#"+comment+"\n"+name+"="+value

def createConfig():
    config = open("config.txt","w")
    config.write("[CONFIG]")
    config.write(configLine("twitchAppId",twitchAppId,"Put your App ID here"))
    config.write(configLine("twitchAppSecret",twitchAppSecret,"Put your App Secret here"))
    config.write(configLine("channelName",channelName,"Put your Channel Name here"))
    config.write(configLine("openMouth",openMouth,"This is the name + extension of the Open Mouth image, in the same folder as the file"))
    config.write(configLine("closedMouth",closedMouth,"This is the name + extension of the Closed Mouth image, in the same folder as the file"))
    config.write(configLine("shakeAmount",shakeAmount,"This determines how much the beeper will shake when talking"))
    config.write(configLine("backgroundColor",backgroundColor,"This determines the Background color for use with Greenscreening"))
    config.write(configLine("pointId",pointId,"The name of the point redeem, case sensitive"))
    config.write(configLine("voiceID",voiceID,"This is the ID of a TTS voice you want to use. To figure out what you have, run the TestTTSVoices.py script."))
    config.close()

def readConfig():
    config = open("config.txt","r")
    for x in config:
        readLine(x)

def readLine(line):
    global twitchAppId
    global twitchAppSecret
    global openMouth
    global closedMouth
    global channelName
    global shakeAmount
    global backgroundColor
    global voiceID
    splitLine = line.split("=")
    
    if splitLine[0] == "twitchAppId":
        twitchAppId = splitLine[1].replace("\n","")
    if splitLine[0] == "twitchAppSecret":
        twitchAppSecret = splitLine[1].replace("\n","")
    if splitLine[0] == "openMouth":
        openMouth = splitLine[1].replace("\n","")
    if splitLine[0] == "closedMouth":
        closedMouth = splitLine[1].replace("\n","")
    if splitLine[0] == "channelName":
        channelName = splitLine[1].replace("\n","")
    if splitLine[0] == "backgroundColor":
        backgroundColor = splitLine[1].replace("\n","")
    if splitLine[0] == "shakeAmount":
        shakeAmount = splitLine[1].replace("\n","")
    if splitLine[0] == "pointId":
        pointId = splitLine[1].replace("\n","")
    if splitLine[0] == "voiceID":
        voiceID = splitLine[1].replace("\n","")

async def on_ready(ready_event: EventData):
    print("Bot is running! Joining channels.")
    await ready_event.chat.join_room(channelName)
    
def saySmth(text):
    global talking
    talking = 1
    tts = _TTS()
    tts.start(text)
    del(tts)
    talking = 0
    
async def on_message(msg: ChatMessage):
    print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')
    saySmth(msg.text)
    
async def callback_whisper(uuid: UUID, data: dict) -> None:
    dataParse = data.get("data_object")
    if data.get("type") == "whisper_sent":
        print(dataParse.get("tags").get("display_name")+" just whispered "+dataParse.get("body"))
        saySmth(dataParse.get("body"))
        
async def callback_point(uuid: UUID, data: dict) -> None:
    dataParse = data.get("reward")
    if data.get("type") == "reward-redeemed":
        if dataParse.get("title") == pointId:
            print(dataParse.get("prompt"))
            saySmth(dataParse.get("prompt"))

try:
    config = open("config.txt","r+")
except:
    print("This is the first time you're running this! As such, you will have to enter your info into the config before the bot will work.\nAttempting to create config...")
    createConfig()
    print("Config created! Please input your data.")
    input("Press Any Key...")
    quit()

readConfig()

async def run():
    pygame.init()
    X = 600
    Y = 600
    
    DEFAULT_IMAGE_SIZE = (500,500)
    
    scrn = pygame.display.set_mode((X, Y))
    
    pygame.display.set_caption('Kobalsbeeper')
    
    cm = pygame.image.load(closedMouth)
    om = pygame.image.load(openMouth)
    
    cm = pygame.transform.scale(cm, DEFAULT_IMAGE_SIZE)
    om = pygame.transform.scale(om, DEFAULT_IMAGE_SIZE)
    
    DEFAULT_IMAGE_POSITION = (50,50)
    bgFill = pygame.Color(backgroundColor)
    
    print("Awaiting Twitch...")
    twitch = await Twitch(twitchAppId, twitchAppSecret)
    print("Awaiting User Authentication...")
    auth = UserAuthenticator(twitch, USER_SCOPE)
    print("Awaiting Tokens...")
    token, refresh_token = await auth.authenticate()
    print("Awaiting Final Authentication...")
    await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)
    user = await first(twitch.get_users(logins=[channelName]))
    
    
    chat = await Chat(twitch)
    
    chat.register_event(ChatEvent.READY, on_ready)
    
    if Test == True:
        print("WARNING: The bot is currently in test mode, and will read out every single chat message!")
        chat.register_event(ChatEvent.MESSAGE,on_message)
    
    chat.start()
    
    pubsub = PubSub(twitch)
    pubsub.start()
    
    uuid = await pubsub.listen_channel_points(user.id, callback_point)
    
    print("Starting the beeper renderer")
    
    clock = pygame.time.Clock()
    run = True
    
    while run:
        global talking
        scrn.fill(bgFill)
        if talking == 1:
            locX = 50+random.randint(-int(shakeAmount),int(shakeAmount))
            locY = 50+random.randint(-int(shakeAmount),int(shakeAmount))
            scrn.blit(om, (locX,locY))
        else:
            scrn.blit(cm, DEFAULT_IMAGE_POSITION)
        for i in pygame.event.get():
            if i.type == pygame.QUIT:
                run = False
                
        pygame.display.flip()
        clock.tick(30)
    print("Closing pygame...")
    pygame.quit()
    print("Closing Twitch listens...")
    await pubsub.unlisten(uuid)
    chat.stop()
    pubsub.stop()
    print("Waiting until Twitch connection closes...")
    await twitch.close()
    print("Goodbye!")
    quit()

config.close()

asyncio.run(run())