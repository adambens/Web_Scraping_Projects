## Import Statements
import json
import pandas as pd #for Reddit Visualization
import plotly #for Reddit Visualization
import plotly.plotly as py
import plotly.graph_objs as go 
import numpy as np #Visualization
import matplotlib.pyplot as plt #Visualization
import urllib.request, urllib.parse, urllib.error
import requests
import hiddeninfo
import sys
import datetime
import re 
import sqlite3

#Reddit python wrapper
import praw 

# Adam Benson
# Reddit API --- scraping subreddits to gain insights into subreddit activity over time



######## PRINTING FUNCTION FOR CODEC ISSUES #########################################
def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file) 
#####################################################################################


######## SET UP CACHING #####################
#############################################
REDDIT_CACHE = "redditAPIResearch_cache.json"
#############################################


try:
    reddit_cache_file = open(REDDIT_CACHE, 'r') # Try to read the data from the file
    reddit_cache_contents = reddit_cache_file.read()  # If it's there, get it into a string
    reddit_cache_file.close() # Close the file, we're good, we got the data in a string.
    REDDIT_CACHE_DICTION = json.loads(reddit_cache_contents) # And then load it into a dictionary
except:
    REDDIT_CACHE_DICTION = {}


## This portion requires that a USER has a Reddit account
## User must generate client information via Reddit account
## Enter user information when prompted to
## This function will retrieve up to 100 of the top, non-stickied, submissions of the specified subreddit
## NOTE: I was interested in 'bigdata', but wrote this function to match any existing subreddit

print("Welcome to the Reddit Analysis Portion of the project")
name = input('Enter Reddit Username: ')

##Set Up Reddit Instance with user information
if name == 'BobCruddles':  #Using personal information for my account
    reddit = praw.Reddit(client_id = hiddeninfo.reddit_id,
                         client_secret = hiddeninfo.reddit_secret,
                         user_agent = 'APIResearch by /u/BobCruddles',
                         username = hiddeninfo.reddit_username,
                         password = hiddeninfo.reddit_password)
else:
    outside_id = input('Enter Reddit client_id: ')
    outside_secret = input('Enter Reddit client_secret: ')
    outside_agent = input('Enter Reddit user_agent: ')
    outside_name = name
    outside_password = input('Enter Reddit password: ')
    reddit = praw.Reddit(client_id = outside_id,
                         client_secret = outside_secret,
                         user_agent = outside_agent,
                         username = outside_name,
                         password = outside_password)


print('Accessing User: ', reddit.user.me()) #make sure you are accessing correct account

def get_subreddit_submissions(subred): #retrieve submissions for subreddit
    if subred in REDDIT_CACHE_DICTION:
        print("Data Was Cached")
        return REDDIT_CACHE_DICTION[subred]
        
    else:
        print("Making New Request")
        response = reddit.subreddit(subred)
        x = response.top(limit=100) 
        REDDIT_CACHE_DICTION[subred] = x
        reddit_cache_file = open(REDDIT_CACHE, 'w')
        reddit_cache_file.write(str(REDDIT_CACHE_DICTION))
        reddit_cache_file.close()
        return REDDIT_CACHE_DICTION[subred]

redditinput = input("Enter subreddit 'ex) bigdata' : ")
subreddit = get_subreddit_submissions(redditinput) #big data subreddit
#print("subreddit title: ", subreddit.title)
#print(type(subreddit)) #type = praw_object
count = 0

###################################################################################
#CREATING REDDIT DB

conn = sqlite3.connect('Reddit_APIandDB.sqlite')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS Submissions')
cur.execute('CREATE TABLE Submissions (subid TEXT PRIMARY KEY, title TEXT, score INTEGER, comments INTEGER, creation_date DATETIME, author TEXT, author_karma INTEGER)')

###################################################################################

for sub in subreddit: #for submission in top 100 submissions in specified subreddit
    if not sub.stickied: #for submissions that are not "stickied"
        count += 1
        subid = sub.id #type str
        subtitle = sub.title #type str
        submission_score = sub.score #type int
        total_comments = sub.num_comments #type int
        sdate = sub.created_utc
        submission_date = datetime.datetime.utcfromtimestamp(sdate) #type datetime
        submission_author = str(sub.author) #from praw.models.reddit
        uprint('submission_title: ', subtitle)
        print('sub_id :', subid)
        print('total comments: ', total_comments)
        print('submission created at: ', submission_date)
        print('submission score: ', submission_score) #score = likes - dislikes
        print('submission author: ', submission_author) #author = username
        aredditor = reddit.redditor(submission_author)
        try:
            authorkarma = aredditor.link_karma
            uprint('link karma: ', authorkarma)
            print('\n')
        except:
            authorkarma = 0
            print("No Karma\n")
        sub_info = [subid, subtitle, sub.score, sub.num_comments, submission_date, submission_author, authorkarma]
        cur.execute('INSERT or IGNORE INTO Submissions VALUES (?,?,?,?,?,?,?)', sub_info)
print(count)
conn.commit()


###################################################################################
## REDDIT VISUALIZATION COMPONENT USING PANDAS AND PLOTLY #########################
###################################################################################
cur.execute('SELECT score, creation_date from Submissions')
p = cur.fetchall()
df = pd.DataFrame([[x for x in y] for y in p])
df.rename(columns={0: 'Score', 1: 'CreationDate'}, inplace = True)


trace1 = go.Scatter(
    x=df['CreationDate'],
    y = df['Score'],
    mode = 'markers')

layout = go.Layout(
    title = 'Reddit Submissions Score vs Date',
    xaxis = go.XAxis(title = 'Creation Date'),
    yaxis = go.YAxis(title = 'Submission Score'))

data = [trace1]
fig = dict(data= data, layout=layout)
py.iplot(fig, filename='Reddit Submissions')
cur.close()
conn.close()

print('Reddit Visualization Success')