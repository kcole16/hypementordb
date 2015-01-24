#python core
import os 
import sys
import datetime
from datetime import timedelta

#dependencies
import pymongo
import requests
from bs4 import BeautifulSoup
from bson.objectid import ObjectId

# from bson import json_util

def getenv(key):
    val = os.environ.get(key)
    if val:
        return val
    elif os.path.isfile('.env'):
        f = open('.env')
        s = f.read()
        f.close()
        for line in s.strip().split('\n'):
            k, v = line.split('=')
            if k == key:
                return v
    return None

def connect_db(url, app_name):
    client = pymongo.MongoClient(getenv(url))
    db = client[getenv(app_name)]
    return db

def check_user_exists(linkedin_id, client_short_name):
    db = connect_db('MONGOLAB_URI', 'APP_NAME')
    user_exists = False
    check_user = eval("db.%s.find_one({'linkedin_id':linkedin_id})" % client_short_name)
    if check_user != None:
        user_exists = True
    return user_exists

def authenticate_linkedin(code, client_code):
    url = 'https://www.linkedin.com/uas/oauth2/accessToken'
    client_id = getenv('LINKEDIN_CLIENT_ID')
    client_secret = getenv('LINKEDIN_CLIENT_SECRET')
    data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': '%s/oauth/%s/' % (str(getenv('PATH_URL')),client_code),
    'code': code,
    'grant_type': 'authorization_code'
    }
    r = requests.post(url, data=data)
    access_token = r.json()['access_token']
    return access_token

def parse_profile(profile):
    xml = BeautifulSoup(profile)
    linkedin_id = xml.find('id').string
    first_name = xml.find('first-name').string
    last_name = xml.find('last-name').string
    email = xml.find('email-address').string
    education = [school.string for school in xml.find_all('school-name')]
    location = xml.find('location').find('name').string
    headline = xml.find('headline').string
    picture_url = xml.find('picture-url').string
    position_list = xml.find_all('position')
    positions = [{'title':position.find('title').string.strip(), 
        'company':position.find('company').find('name').string.strip()} for position in position_list]
    industry = xml.find('industry').string
    user_details = {'linkedin_id':linkedin_id, 
        'first_name':first_name, 'education':education,
        'last_name':last_name, 'email':email, 'location':location, 
        'headline':headline, 'positions':positions, 'industry':industry, 'picture_url':picture_url}
    return user_details

def save_linkedin_profile(access_token, client_code):
    user_status = False
    db = connect_db('MONGOLAB_URI', 'APP_NAME')
    client_short_name = db.clients.find_one({'client_code':client_code})['short_name']
    url = 'https://api.linkedin.com/v1/people/~:(id,headline,first-name,last-name,email-address,educations,location:(name),industry,positions,picture-url)'
    headers = {
        'Host':'api.linkedin.com',
        'Connection':'Keep-Alive',
        'Authorization': 'Bearer %s' % access_token
    }
    r = requests.get(url, headers=headers)
    print r.text
    if r.ok:
        user_details = parse_profile(r.text)
        if check_user_exists(user_details['linkedin_id'], client_short_name) == False:
            db_insert = "db.%s.insert(user_details)" % client_short_name
            eval(db_insert)
        else:
            user_status = True
    else:
        user_status = "Error"
    return user_status
    
