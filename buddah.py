import praw
import time
from pykarma import find

file = open("buddah/conf/userdata.txt")
data = file.read().split("\n")

name   = data[0]
pwd    = data[1]
cid    = data[2]
secret = data[3]

file = open("buddah/conf/sublist.txt")
subs = file.read().replace("\n","+")

file = open("buddah/conf/filters.txt")
filters = file.read().split("\n")

file = open("buddah/conf/config.txt")
data = file.read().split("\n")

minimum_karma = int(data[0])
sublist_acts_as_filter = data[1]=="True"
message_refresh= int(data[2])   #Message refresh rate can be a bit longer than wanted if Buddah is processing a post
balise = data[3]

file = open("buddah/conf/admins.txt")
admins = file.read().split("\n")

RUNNING, STOPPED, PAUSED = "Running", "Stopped", "Paused"
status = RUNNING

reddit = praw.Reddit(user_agent='Comment Extraction (by /u/)'+name,
                     client_id=cid, client_secret=secret,
                     username=name, password=pwd)

if(sublist_acts_as_filter):
    subreddits = reddit.subreddit("all")
else:
    subreddits = reddit.subreddit(subs)
    
def searchForReposts():
    last_checked = time.time() - message_refresh
    print("Creating stream...")
    stream = subreddits.stream.submissions()
    i=0
    print("Receiving posts...")
    for post in stream:

        if time.time()-last_checked >= message_refresh:
            checkForCommands()
            last_checked = time.time()
        
        i+=1
        url = post.url.replace("https", "http")
        if (not sublist_acts_as_filter or not postedInFilteredSub(post)):
            if containsFilter(url):
                print("["+str(i)+"]"+url)
                results = find(url, fetch_praw=True)
                posts = []
                try:
                    for e in results:
                        posts.append(e)
                except AttributeError:
                    pass
                else:
                    print(str(len(posts))+" matching posts !")
                    if (len(posts) > 0 and posts[0].score >= minimum_karma):
                        posts = quickSort(posts)
                        top_post = posts[0]
                        coms = top_post.comments
                        for e in coms:
                            if e.body not in ["[deleted]", "[removed]"] and not e.stickied:
                                top_com = e
                                break
                        if top_com is not None:
                            text = top_com.body
                            post.reply(text)
                            post.upvote()
                            print("Replied: \n"+text+"\nTo post:\n"+getPostUrl(post)+"\nFrom post:\n"+getPostUrl(top_post))

                    else:
                        print("Best score ("+str(posts[0].score)+") is lesser than required ("+str(minimum_karma)+")")




def checkForCommands(arg = -1):
    print("Checking for new messages...")
    messages = reddit.inbox.unread()
    global status
    try:
        for m in messages:
            if m.author.name in admins:

                command = m.body.lower().split(" ")
                instruction = command[0]
                author = m.author.name

                # Stops Buddah until newt START instruction
                # Takes no parameters
                if instruction == "stop" and status == RUNNING:
                    m.mark_read()
                    m.reply("Sucessfully stoped!")
                    print("Recieved STOP instruction from "+author)
                    status = STOPPED
                    idle()
                    break

                # Pauses Buddah for a defined time (seconds by default)
                # PAUSE [time] *[s, m, h]
                elif instruction == "pause" and status == RUNNING:
                    if len(command)>1:
                        try:
                            t=int(command[1])
                            if len(command)>2:
                                t*= 1*(command[2]=="s") + 60*(command[2]=="m") + 3600*(command[2]=="h")
                                if t <= 0:
                                    messageError(m, "PAUSE", "wrong time formating")
                            if t<=0:
                                messageError(m, "PAUSE", "time must be greater than 0")

                            m.reply("Sucessfully paused")
                            m.mark_read()
                            print("Recieved PAUSE instruction from "+author)
                            status = PAUSED
                            idle(t)
                        except ValueError:
                            messageError(m, "PAUSE", "no integer")
                        
                    else:
                       messageError(m, "PAUSE", "command too short") 

                # Asks Buddah what status it is in (RUNNING, STOPPED, or PAUSED)
                # Takes no parameters
                elif instruction == "status":
                    m.reply("Current status: " + status  + (arg>=0 and status == PAUSED)*(" ("+str(arg)+" s remaining)"))
                    m.mark_read()
                    print("Sent status information to " + author)

                # Restarts Buddah
                # Takes no parameters
                elif instruction == "start":
                    if status in [STOPPED, PAUSED]:
                        m.reply("Sucessfully started")
                        m.mark_read()
                        print("Recieved START instruction from "+author)
                        return "RESTART"
                    else:
                        messageError(m, "START", "Buddah is already running !")
                    
                # Clears command queue
                # Takes no parameters
                elif instruction == "clear":
                    queue = reddit.inbox.unread()
                    for e in queue:
                        e.mark_read()
                    m.reply("Sucessfully cleared queue")
                    print("Recieved CLEAR instruction from "+author)
                    break

                     
    except AttributeError:
        pass
    except StopIteration:
        pass


def idle(t=-1):
    global status
    while True:
        restart = checkForCommands(t)
        if restart == "RESTART":
            status=RUNNING
            return True
        if t==-1:
            time.sleep(message_refresh)
        else:
            if t>=message_refresh:
                time.sleep(message_refresh)
                t-=message_refresh
            else:
                time.sleep(t)
                status = RUNNING
                return True
        

def quickSort(lst):
    n=len(lst)
    if n>1:
        Li, x, Ls = split(lst)
        Lit, Lst = quickSort(Li), quickSort(Ls)
        return Lit+[x]+Lst
    else:
        return lst

def split(lst):
    x = lst.pop()
    Li, Ls = [], []
    for e in lst:
        if e.score > x.score:
            Li.append(e)
        else:
            Ls.append(e)
    return Li, x, Ls

def getPostUrl(post):
    return "https://www.reddit.com/r/"+post.subreddit.display_name+"/comments/"+post.id

def containsFilter(string):
    for f in filters:
        if f in string:
            return True
    return False

def postedInFilteredSub(post):
    return post.subreddit.display_name in subs

def messageError(m, s, t):  #MST lol
                        m.reply("Failed to execute "+ s + "instruction: " +t)
                        m.mark_read()
                        print("Failed to execute "+ s + " instruction from "+m.author.name+ ": "+t)
