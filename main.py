#!/usr/bin/python
# -*- coding: UTF-8 -*-
from fastapi import FastAPI,Request,Body,Response
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
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'}

@app.get("/", response_class=HTMLResponse)
async def pikpak(request: Request):
    return templates.TemplateResponse("pikpak.html",{'request': request})


@app.get("/pikpak/{userindex}/{folderid}", response_class=HTMLResponse)
async def pikpak_folder(userindex: int,folderid: str,request: Request):
    return templates.TemplateResponse("pikpak_folder.html",{'request': request,'userindex':userindex,'folderid':folderid})


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
        # user['key'] = username
        DETA_USER_DB.update(user,username)
        userstring = json.dumps(user)
        return userstring
    return 'error'


# @app.post('/relogin')
# def relogin(user:User):
#     username = user.username
#     DETA_USER_DB.update(user,username)
#     return 'ok'

@app.get('/getUsers')
def getUsers():
    res = DETA_USER_DB.fetch()
    index = 0
    all_users = res.items
    while res.last:
        res = db.fetch(last=res.last)
        all_users += res.items
    users = []
    for user in all_users:
        user['index']=index
        users.append(user)
        index+=1
    return users

@app.post('/delUser')
def delUser(user:User):
    username = user.username
    DETA_USER_DB.delete(username)
    return 'ok'

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
        return Response(content=r.text, media_type="application/json")
        return r.text
        result = json.loads(r.text)
        if r.status_code != 200 or 'error' in result:
            return 'error'
        return json.dumps(result)



@app.post('/getFiles')
def getFiles(item: PostRequest):
    ucookies = item.access_token
    rdata = {'parent_id': item.path,'page_token': item.pagetoken}
    url = 'https://api-drive.mypikpak.com/drive/v1/files?thumbnail_size=SIZE_LARGE&with_audit=true&parent_id='+item.path+'&page_token='+item.pagetoken+'&filters=%7B%22phase%22:%7B%22eq%22:%22PHASE_TYPE_COMPLETE%22%7D,%22trashed%22:%7B%22eq%22:false%7D%7D'
    headers['referer'] = "https://api-drive.mypikpak.com/drive/v1/files"
    headers['Authorization']='Bearer '+ucookies
    try:
        r = requests.get(url, verify=False,headers=headers, timeout=100)
    except:
        return 'error'
    else:
        return Response(content=r.text, media_type="application/json")
        return r.text
        result = json.loads(r.text)
        if r.status_code != 200 or 'error' in result:
            return 'error'
        return json.dumps(result)


@app.post('/delFile')
def delFile(item: PostRequest):
    ucookies = item.access_token
    trashurl = 'https://api-drive.mypikpak.com/drive/v1/files:batchTrash'
    deleteurl = 'https://api-drive.mypikpak.com/drive/v1/files:batchDelete' 
    headers['referer'] = "https://api-drive.mypikpak.com/drive/v1/files"
    headers['Authorization']='Bearer '+ucookies
    ids = json.loads(item.ids);
    payload = json.dumps({
        "ids": ids
    })
    try:
        r = requests.post(deleteurl, verify=False,data=payload, headers=headers, timeout=100)
    except:
        return 'error'
    else:
        dresult = json.loads(r.text)
        if r.status_code != 200:
            return 'error'
        return json.dumps(dresult)


@app.post('/getDownload')
def getDownload(item: PostRequest):
    ucookies = item.access_token
    headers['referer'] = "https://api-drive.mypikpak.com/drive/v1/files"
    headers['Authorization']='Bearer '+ucookies

    url = '' 
    if item.id == '/':
        url = 'https://api-drive.mypikpak.com/drive/v1/files'
    else:
        url = 'https://api-drive.mypikpak.com/drive/v1/files/'+item.id
   
    try:
        r = requests.get(url, verify=False,headers=headers, timeout=100)
    except:
        return 'error'
    else:
        return Response(content=r.text, media_type="application/json")
        result = json.loads(r.text)
        if r.status_code != 200:
            return 'error'
        return json.dumps(result)


@app.post('/offline')
def offline(item: PostRequest):
    ucookies = item.access_token
    url = 'https://api-drive.mypikpak.com/drive/v1/files'
    keyword = item.textLink
    headers['referer'] = "https://api-drive.mypikpak.com/drive/v1/files"
    headers['Authorization']='Bearer '+ucookies

    postData = {
            "kind": "drive#file",
            "name": "",
            "parent_id": '',
            "upload_type": "UPLOAD_TYPE_URL",
            "url": {
              "url": keyword
            },
            "params": {"from":"file"},
            "folder_type": "DOWNLOAD"
          }
    r = requests.post(url, verify=False, data=json.dumps(postData), headers=headers,timeout=100)
    result = json.loads(r.text)
    if r.status_code != 200 or result['upload_type'] is None:
        return 'error'
    return json.dumps(r.text)


@app.route('/delFile', methods=['POST'])
def delFile():
    data = request.get_json(silent=True)
    if 'access_token' not in data.keys():
        return 'error'
    ucookies = data['access_token'] 
    trashurl = 'https://api-drive.mypikpak.com/drive/v1/files:batchTrash'
    deleteurl = 'https://api-drive.mypikpak.com/drive/v1/files:batchDelete' 

    headers['referer'] = "https://api-drive.mypikpak.com/drive/v1/files"
    headers['Authorization']='Bearer '+ucookies
    ids = json.loads(data['ids']);
    payload = json.dumps({
        "ids": ids
    })
    try:
        r = requests.post(deleteurl, verify=False,data=payload, headers=headers, timeout=100)
    except:
        return 'error'
    else:
            dresult = json.loads(r.text)
            if r.status_code != 200:
                return 'error'
            return json.dumps(dresult)



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
        return Response(content=r.text, media_type="application/json")
        return r.text
        result = json.loads(r.text)
        if r.status_code != 200 or 'error' in result:
            return 'error'
        return json.dumps(result)
