## Import statements
import json
import numpy as np #Visualization
import matplotlib.pyplot as plt #Visualization
from wordcloud import WordCloud #World Cloud Visualization
import urllib.request, urllib.parse, urllib.error
import requests
import sys
import datetime
import time #for NYT rate-limit
import re 
import sqlite3



######## PRINTING FUNCTION FOR CODEC ISSUES #########################################
def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file) 
#####################################################################################
######## SET UP CACHING ################
########################################
try:
    nyt_cache_file = open(NYT_CACHE, 'r') # Try to read the data from the file
    nyt_cache_contents = nyt_cache_file.read()  # If it's there, get it into a string
    nyt_cache_file.close() # Close the file, we're good, we got the data in a string.
    NYT_CACHE_DICTION = json.loads(nyt_cache_contents) # And then load it into a dictionary
except:
    NYT_CACHE_DICTION = {}

###################################################################################
###################################################################################
# New York Times
# Matches articles based on a user entered query
# NYT requires USER generates an access key via NYTS
# Enter article search query when prompted
# Process returns useful meta-data about articles

print("Welcome to the New York Times Analysis Portion of the project")


nytbase_url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
params = {}
nyt_key = None
if nyt_key is None: #get token from nyt user in order to run this script
    nyt_key = input("\nCopy and paste API Key from https://developer.nytimes.com/\n>  ")


#Question = where to implement range(10) in order to get 100 results
def get_nyt_articles(subject): #creating an API request for NYT articles on a certain subject
    y=0
    if subject in NYT_CACHE_DICTION:
       print("Data in Cache")
       return NYT_CACHE_DICTION[subject]
    else:
        print("Making new request")
        data = list()
        t = 0
        for x in range(0,10): #10 results per page. 10 pages = 100 results
            params = {'page':  str(x), 'api-key': nyt_key, 'q': subject,
                   'fq' : "headline(\"" + str(subject) + "\")",
                   'fl': 'headline, keywords, pub_date, news_desk'}
                   #'offset': x}
        #while x <= 3:
           
            nyt_api =  requests.get(nytbase_url, params = params)
            print(type(json.loads(nyt_api.text)))
            #uprint(json.loads(nyt_api.text))
            #try:
            data.append(json.loads(nyt_api.text))
            #except: 
                #print('didnt work')
                #continue

            #x = x + 1
            time.sleep(1) #avoid making too many requests during pagnation

            NYT_CACHE_DICTION[subject] = data
            dumped_json_cache = json.dumps(NYT_CACHE_DICTION)
            nyt_cache_file = open(NYT_CACHE_DICTION, 'w')
            nyt_cache_file.write(dumped_json_cache)
            nyt_cache_file.close()
            t +=1
            print(t)

        return NYT_CACHE_DICTION[subject]
        
subj = input("Enter Search Query: ")
articles = (get_nyt_articles(subj))
#uprint(articles)  #type(articles) = LIST
#uprint(articles)
#print(len(articles[2]['docs']))
#s = json.dumps(articles, indent = 4)
#print(s)

###################################################################################
conn = sqlite3.connect('NYT_APIandDB.sqlite')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS Articles')
cur.execute('DROP TABLE IF EXISTS Keywords')
cur.execute('DROP TABLE IF EXISTS Sections')
cur.execute('CREATE TABLE Articles (date_published DATETIME, headline TEXT, query TEXT, section TEXT)')
cur.execute('CREATE TABLE Keywords (keyword TEXT, value INTEGER)')
cur.execute('CREATE TABLE Sections (section TEXT, value INTEGER)')
###################################################################################

keywords_dict = {}
sections_dict = {}

for t in articles:
    if t['status'] == 'OK':
        stories = t["response"]["docs"]
        for item in stories:
            headline = item["headline"]["main"]
            #print(headline)
            publication_date = item.get("pub_date", "Date Unavaliable")
            #print(publication_date)
            news_section = item.get("new_desk", "Section Unavaliable")
            #print(news_section)
            if news_section != 'Section Unavaliable':
                sections_dict[news_section] = sections_dict.get(news_section, 0) + 1
            keywords_list = item["keywords"]
            if len(keywords_list) != 0:
                for piece in keywords_list:
                    words = piece['value']
                    keywords_dict[words] = keywords_dict.get(words, 0) + 1
            stories_info = (publication_date, headline, subj, news_section, )
            cur.execute('INSERT or IGNORE INTO Articles VALUES (?,?,?,?)', stories_info)
    else:
        continue
#stories = articles[0]["response"]['docs']
#print(type(stories), type(articles))
#print(len(stories))
#s = str(stories)
#ss = re.findall('headline', s)
#print(len(ss))


sorted_keywords = [(a, keywords_dict[a]) for a in sorted(keywords_dict,
                    key = keywords_dict.get, reverse = True)]

for k, v in sorted_keywords:
    #print(k, v)
    g = (k,v)
    cur.execute('INSERT or IGNORE INTO Keywords VALUES (?,?)', g)

sorted_sections = [(a, sections_dict[a]) for a in sorted(sections_dict,
                    key = sections_dict.get, reverse = True)]
print('\n')

print('Sorted News Sections: ')
for c, d in sorted_sections:
    print(c, d)
    b = (c,d)
    cur.execute('INSERT or IGNORE INTO Sections VALUES (?,?)', b)
#printing sections based on value
conn.commit()

keyword_wordcloud = WordCloud(background_color="black", max_font_size=60, min_font_size = 12, max_words = 100, width = 800, height =800).generate_from_frequencies(keywords_dict)
#plt.figure.Figure()
plt.imshow(keyword_wordcloud, interpolation="bilinear")
plt.axis("off")
plt.show()
cur.close()
conn.close()

print('NYTimes Visualization Success')