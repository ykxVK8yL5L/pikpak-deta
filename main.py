#!/usr/bin/python
# -*- coding: UTF-8 -*-
from fastapi import FastAPI,Request,Body
from fastapi.responses import StreamingResponse,HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from deta import Deta
from pydantic import BaseModel
from pydantic import Extra
import time
import base64
import io
import re
import requests
import json


deta = Deta()
DETA_USER_DB = deta.Base("pikpak_user")


app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

headers = {
	"User-Agent": ":Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko)Version/5.1 Safari/534.50",
	"content-type": "text/html; charset=utf-8",
}

@app.get("/pikpak", response_class=HTMLResponse)
async def pklji(request: Request):
    return templates.TemplateResponse("pikpak.html",{'request': request})


class User(BaseModel):
    username: str
    password: str 

class PostRequest(BaseModel):
    username: str
    password: str
    access_token:str
    key:str
    class Config:
        extra = Extra.allow





@app.post('/login')
def login(user:User):
    s = requests.session()
    url = "https://user.mypikpak.com/v1/auth/signin"
    username = user.username
    password = user.password
    d = json.dumps({
    "captcha_token": "",
    "client_id": "YNxT9w7GMdWvEOKa",
    "client_secret": "dbw2OtmVEeuUvIptb1Coyg",
    "username": username,
    "password": password
    })
    r = s.post(url, verify=False, data=d)
    result = json.loads(r.text)
    if 'access_token' not in result:
        return 'error'
    else:
        user = {}
        user['username'] = username
        user['password'] = password
        user['access_token'] = result['access_token']
        user['key'] = username
        DETA_USER_DB.put(user)
        userstring = json.dumps(user)
        return userstring
    return 'error'


@app.post('/relogin')
def relogin(user:User):
    s = requests.session()
    url = "https://user.mypikpak.com/v1/auth/signin"
    username = user.username
    password = DETA_USER_DB.get(username)['password']
    d = json.dumps({
    "captcha_token": "",
    "client_id": "YNxT9w7GMdWvEOKa",
    "client_secret": "dbw2OtmVEeuUvIptb1Coyg",
    "username": username,
    "password": password
    })
    r = s.post(url, verify=False, data=d)
    result = json.loads(r.text)
    if 'access_token' not in result:
        return 'error'
    else:
        user = {}
        user['username'] = username
        user['password'] = password
        user['access_token'] = result['access_token']
        user['key'] = username
        DETA_USER_DB.update(user)
        userstring = json.dumps(user)
        return userstring
    return 'error'


@app.get('/getUsers')
def getUsers():
    res = DETA_USER_DB.fetch()
    all_users = res.items
    while res.last:
        res = db.fetch(last=res.last)
        all_users += res.items
    return all_users




@app.post('/getEvents')
def getEvents(item: PostRequest):
    ucookies = item.access_token
    url = 'https://api-drive.mypikpak.com/drive/v1/events?filters=&thumbnail_size=SIZE_LARGE&limit=100&page_token='+item.pagetoken
    headers['referer'] = "https://api-drive.mypikpak.com/drive/v1/files"
    headers['Authorization']='Bearer '+ucookies
    try:
        r = requests.get(url, verify=False,headers=headers, timeout=100)
    except:
        return 'error'
    else:
        return r.text
        result = json.loads(r.text)
        if r.status_code != 200:
            return 'error'
        return json.dumps(result)

@app.post('/getVip')
def getVip(item: PostRequest):
    ucookies = item.access_token
    url = 'https://api-drive.mypikpak.com/drive/v1/privilege/vip'
    headers['referer'] = "https://api-drive.mypikpak.com/drive/v1/files"
    headers['Authorization']='Bearer '+ucookies
    try:
        r = requests.get(url, verify=False,headers=headers, timeout=100)
    except:
        return 'error'
    else:
        return r.text
        result = json.loads(r.text)
        if r.status_code != 200:
            return 'error'
        return json.dumps(result)




@app.get("/")
async def root():    
    return "Hello World!"

