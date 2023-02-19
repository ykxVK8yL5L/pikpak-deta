from fastapi import FastAPI,Request
from fastapi.responses import StreamingResponse,HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from deta import Deta
from pydantic import BaseModel
import time
import base64
import io
import re
import requests
import json


deta = Deta()
DETA_DB = deta.Base("pikpak")




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


@app.post('/login')
def login(user:User):
    s = requests.session()
    url = "https://user.mypikpak.com/v1/auth/signin"
    username = user.username
    password = user.password
    #pwd = hashlib.md5(password.encode("utf-8")).hexdigest()
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
        DETA_DB.put(user)
        return userstring
    return 'error'





@app.get("/")
async def root():    
    return "Hello World!"

