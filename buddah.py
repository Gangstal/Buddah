import praw

file = open("buddah/conf/userdata.txt")
data = file.read().split("\n")

name   = data[0]
pwd    = data[1]
cid    = data[2]
secret = data[3]

secret

reddit = praw.Reddit(user_agent='Comment Extraction (by /u/)'+name,
                     client_id=cid, client_secret=secret,
                     username=name, password=pwd)
