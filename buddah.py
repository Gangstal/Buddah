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

file = open("buddah/conf/admins.txt")
admins = file.read().split("\n")

reddit = praw.Reddit(user_agent='Comment Extraction (by /u/)'+name,
                     client_id=cid, client_secret=secret,
                     username=name, password=pwd)
if(sublist_acts_as_filter):
    subreddits = reddit.subreddit("all")
else:
    subreddits = reddit.subreddit(subs)
    
def searchForReposts():
    print("Creating stream...")
    stream = subreddits.stream.submissions()
    i=0
    print("Receiving posts...")
    for post in stream:
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
            
        if(i%50==0):
            print("Checking for new messages...")
            messages = reddit.inbox.unread()
            try:
                for m in messages:
                    if(m.author.name in admins and m.body=="STOP"):
                        m.mark_read()
                        m.reply("Sucessfully stoped!")
                        print("Recieved STOP instruction from "+m.author.name)
                        stream.close()
                        return True
            except AttributeError:
                print("No new messages")
            except StopIteration:
                print("End of new messages")

def idle():
    while True:
        messages = reddit.inbox.unread()
        try:
            for m in messages:
                print(m.author.name, m.body)
                if(m.author.name in admins and m.body=="START"):
                    m.mark_read()
                    m.reply("Starting")
                    print("Recieved START instruction from "+m.author.name)
                    stream.close()
                    return True
        except AttributeError:
            print("No new messages")
        except StopIteration:
            print("End of new messages")
        time.sleep(60)
        

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

idle()
