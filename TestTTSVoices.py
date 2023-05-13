import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty("voices")
file = open("VoiceIDs.txt","w")
for voice in voices:
    file.write(voice.id+"\n")
    engine.setProperty("voice", voice.id)
    engine.say("This is voice called: "+voice.id+". And I am saying stuff in that voice.")
    print("This is voice called: "+voice.id+". And I am saying stuff in that voice.")
file.close()
engine.runAndWait()