import praw
from pykarma import find

file = open("buddah/conf/userdata.txt")
data = file.read().split("\n")

name   = data[0]
pwd    = data[1]
cid    = data[2]
secret = data[3]

file = open("buddah/conf/sublist.txt")
subs = file.read().replace("\n","+")


reddit = praw.Reddit(user_agent='Comment Extraction (by /u/)'+name,
                     client_id=cid, client_secret=secret,
                     username=name, password=pwd)

subreddits = reddit.subreddit(subs)


def getPosts(n=0):
    print("Creating stream...")
    stream = subreddits.stream.submissions()
    posts = []
    i = 0
    print("Receiving posts...")
    for post in stream:
        if i==n:
            break
        i+=1
        posts.append(post)

    stream.close()
    return posts

def filterPosts(posts):
    for post in posts:
        if not (post.url.endswith("jpg") or post.url.endswith("png")):
            posts.remove(post)
    return posts

def fetchPosts(n=10):
        posts = filterPosts(getPosts(n))
        return posts
    
def searchForReposts():
    print("Creating stream...")
    stream = subreddits.stream.submissions()
    i=0
    print("Receiving posts...")
    for post in stream:
        i+=1
        url = post.url.replace("https", "http")
        if not "www.reddit.com/r/" in url:
            print(url)
            results = find(url, fetch_praw=True)
            posts = []
            if results.original is not None:
                for e in results:
                    posts.append(e)
                
                if len(posts > 0 and posts[0].score >= 250):
                    posts = quickSort(posts)
                    top_post = posts[0]
                    coms = top_post.comments
                    for e in coms:
                        top_com = e
                        break
                    if e is not None:
                        text = top_com
                        post.reply(text)
                        print("Replied: \n"+text+"\nTo post:\n"+getPostUrl(post))



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
    return "https://www.reddit.com/r/"+post.subreddit+"/comments/"+post.id
