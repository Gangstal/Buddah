import praw

reddit = praw.Reddit(user_agent='Comment Extraction (by /u/)'+name,
                     client_id=id, client_secret=secret,
                     username=name, password=pwd)
