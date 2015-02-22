## Twitch IRC Bot developed by Eleng555 (Emily Leng)

import sys
import socket
import string
import random
import json
import threading
import urllib2
from datetime import datetime, timedelta

bot_owner = 'Eleng555'
nick = 'KLBOT'
chan = 'eleng555'
channel = '#' + chan
server = 'irc.twitch.tv'
password = REDACTED
port = 6667


def upstream(c):
    try:
        url = 'https://api.twitch.tv/kraken/streams/' + c
        contents = urllib2.urlopen(url)

        j = json.loads(contents.read())
        json_string = json.dumps(j,sort_keys=True,indent=2)
        print json_string
        parent =  j["stream"]
        time = parent["created_at"].split("T")[1].split("Z")[0]
        hr = int(time.split(":")[0])
        timezone = -5
        hr = hr + timezone
        if hr < 0:
            hr = hr + 24
        start = datetime.strptime(str(hr) + ":" + time.split(":")[1],"%H:%M").strftime("%I:%M%p")
        dnow = str(datetime.utcnow()).split(" ")[1].split(".")[0]
        dnowint = int(dnow.split(":")[0]) + timezone
        if dnowint < 0:
            dnowint = dnowint + 24
        now = datetime.strptime(str(dnowint) + ":" + dnow.split(":")[1],"%H:%M").strftime("%I:%M%p")
        ##print start + " EST ", now + " EST"
        ret1 = "Stream Started at " + start + " EST. "
        uphr = dnowint - hr
        upmin = int(dnow.split(":")[1].split(":")[0]) - int(time.split(":")[1].split(":")[0])
        if upmin < 0:
            upmin = 60 + upmin
            uphr = uphr - 1
        ret2 = "Current Upstream Time on #" + c + " is: " + str(uphr) + " hour(s), " + str(upmin) + " min(s)."
        return ret1, ret2
    except Exception:
        return "Stream on #" + c + " is currently offline."
   
slots = 6 # for roulette

queue = 0
currentsong = ""
votecount = list()
options = list()
userlist = list()
results = list()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((server, port))

#connects to twitch chat
s.send('PASS ' + password + '\r\n')
s.send('USER ' + nick + ' 0 * :' + bot_owner + '\r\n')
s.send('NICK ' + nick + '\r\n')
print "Joining channel..."
s.send('JOIN ' + channel + '\r\n')
print "Joined!"
s.send('PRIVMSG ' + channel + ' :Hello!\r\n')

def ping(data):
    print data
    if data.find('PING') != -1:
        s.send(data.replace('PING', 'PONG'))
        
commands = ["help", "roll", "roulette", "leave", "upstream", "setcurrentsong", "poll", "pollreset", "pollresult",
            "vote", "checkstream"]
##commands = ["help", "leave", "upstream", "setcurrentsong", "poll", "pollreset", "vote"]


def msg(m):
    global queue
    queue += 1
    print queue
    if queue < 15: #ensures does not send >20 msgs per 30 seconds.
        s.send(m)
    else:
        print 'Message deleted', m

def queuetimer(): #function for resetting the queue every 30 seconds
    global queue
    ##print 'queue reset'
    queue = 0
    threading.Timer(30,queuetimer).start()
queuetimer()

def parse(line):
    message, username = "", ""
    exclude = set(string.punctuation)
    strippedline = line
    strippedline = ''.join(ch for ch in strippedline if ch not in exclude)
    if line.find("JOIN %s" % (channel)) != -1:
        username = line.split(":")[1].split("!")[0]
        ##if username.lower() != "klbot":
            ##msg("PRIVMSG %s :Welcome, %s!\n" % (channel, username))
    if len(line.split(":")) == 3:
        username = line.split(":")[1].split("!")[0]
        message = line.split(":")[2]
        if line.lower().find("lol") != -1:
            r = random.randint(1,500)
            print r
            if r < 5:
                msg("PRIVMSG %s :%s, but did you actually laugh out loud?\n" % (channel, username))
        elif line.lower().find("mic?") != -1:
                msg("PRIVMSG %s :Kyle's microphone is currently being used by the keyboard (it is a direct line-in connection),"  % (channel) + 
                       " so Kyle cannot talk during piano streams. However, he does occasionally do Q&A sessions after streams.\n")
        elif line.lower().find("has just subscribed") != -1:
                msg("PRIVMSG %s : %s, welcome to Kyle's channel! We hope you enjoy all the piano madness!~ \n" % (channel, username))
        elif line.lower().find("du?") != -1 or line.lower().find("dudu") != -1:
                msg("PRIVMSG %s :DUDUDUDUDU!\n" % (channel))
        elif strippedline.lower().find("hello klbot") != -1 or strippedline.lower().strip(",").find("hi klbot") != -1 or strippedline.lower().strip(",").find("hey klbot") != -1:
                msg("PRIVMSG %s :Hey %s!\n" % (channel, username))
        if message.find("`") != -1:
            actual = message[1:].split(" ")
            try: 
                text = message[message.find(" ")+1:]
            except Exception:
                print "Cannot split"
            command = actual[0]
            if command.find("roll") != -1:
                highest = 1000
                try:
                    if len(actual) == 2:
                        highest = int(actual[1])
                        if highest < 1:
                            raise Exception()
                    msg("PRIVMSG %s :%s rolled %d\n" % (channel, username, random.randint(1, highest)))
                except Exception:
                    a = 0
                    msg("PRIVMSG %s :Enter a valid number, %s. :C \n" % (channel, username))
            if command.find("help") != -1:
                msg("PRIVMSG %s :My commands are: %s. To use a command, type ` (backwards quote) followed by the command. For example, `roll 1000. \n" % (channel, ", ".join(sorted(commands))))
            elif command.find("roulette") != -1:
                global slots
                rang = random.random()
                if rang < (1.0 / slots):
                    slots = 6
                    msg("PRIVMSG %s :%s, you died! D:\n" % (channel, username))
                    msg("PRIVMSG %s :*reloads the chambers*, there are %s untouched slots. You have a %s%% chance to die\n" % (channel, slots, "{0:.2f}".format(100.0 / slots)))
                else:
                    slots -= 1
                    msg("PRIVMSG %s :*click*, there are %s untouched slots. You have a %s%% chance to die.\n" % (channel, slots, "{0:.2f}".format(100.0 / slots)))
            elif command.find("leave") != -1 and username.lower() == bot_owner.lower():
                msg("PRIVMSG %s :Fine, I'll leave... \n" % (channel))
                msg("PART " + channel + "\r\n")
                sys.exit()
            elif command.find("upstream") != -1:
                ##print upstream(), len(upstream())
                if len(upstream(chan)) == 2:
                    msg("PRIVMSG %s :" % (channel) + str(upstream(chan)[0]) + str(upstream(chan)[1]) + "\n")
                else:
                    msg("PRIVMSG %s :" % (channel) + str(upstream(chan)) + "\n")
            elif command.find("checkstream") != -1:
                checkchan = text.strip()
                if len(upstream(checkchan)) == 2:
                    msg("PRIVMSG %s :" % (channel) + str(upstream(checkchan)[0]) + str(upstream(checkchan)[1]) + "\n")
                else:
                    msg("PRIVMSG %s :" % (channel) + str(upstream(checkchan)) + "\n")
            elif command.find("poll") != -1 and command.find("pollreset") == -1 and command.find("pollresult") == -1 and command.find("vote") == -1:
                global votecount, options
                options = text.strip().split(",")
                for x in range (0,len(options)):
                    votecount.append(0)
                print options, votecount
                msg("PRIVMSG %s :Poll has been created with the following options: %s\n" % (channel, options))
            elif command.find("pollreset") != -1:
                global userlist, results
                votecount = list()
                options = list()
                userlist = list()
                results = list()
                print votecount, options, userlist, results
            elif command.find("pollresult") != -1:
                for x in range (0,len(options)):
                    results.append(str(options[x]) + ": " + str(votecount[x]))
                msg("PRIVMSG %s :Poll Results: %s\n" % (channel, results))
            elif command.find("vote") != -1 and command.find("poll") == -1:
                for x in range (0,len(options)):
                    if username not in userlist:
                        if text.lower().strip().find(options[x].lower().strip()) != -1:
                            votecount[x] = votecount[x] + 1
                            userlist.append(username)
                print userlist, options, votecount
            elif command.find("setcurrentsong") != -1:
                global currentsong
                currentsong = text
                print currentsong   
                msg("PRIVMSG %s :Current Song is: %s.\n" % (channel, currentsong))
        if (line.lower().find("current song?") != -1 or line.lower().find("song name?") != -1) and currentsong != "":
            msg("PRIVMSG %s :Current Song is: %s, @%s.\n" % (channel, currentsong, username))

while True:
    line = s.recv(1024)
    ##print line
    if line.find("PRIVMSG %s" % channel) != 1:
        parse(line)
    if line.find("PING") != -1:
        ping(line)
