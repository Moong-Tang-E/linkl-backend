import motor.motor_asyncio
import datetime
import redis.asyncio as redis
import string
import random
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status
from starlette.responses import JSONResponse
from models.link import CrateLink

create_route = APIRouter()


@create_route.post("/create")
async def create_link(request: Request, link: CrateLink):
    original_link = link.link
    if link.redirect_link is None:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "redirect_link is required"})
    if (
        not link.redirect_link.startswith("http://")
        and not link.redirect_link.startswith("https://")
        and not link.redirect_link.startswith("ftp://")
        and not link.redirect_link.startswith("ftps://")
        and not link.redirect_link.startswith("sftp://")
        and not link.redirect_link.startswith("smb://")
        and not link.redirect_link.startswith("smb://")
        and not link.redirect_link.startswith("chrome://")
        and not link.redirect_link.startswith("magnet://")
        and not link.redirect_link.startswith("mailto://")
        and not link.redirect_link.startswith("tel://")
        and not link.redirect_link.startswith("telnet://")
        and not link.redirect_link.startswith("webdav://")
        and not link.redirect_link.startswith("webdavs://")
        and not link.redirect_link.startswith("ws://")
        and not link.redirect_link.startswith("wss://")
        and not link.redirect_link.startswith("file://")
    ):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Bad Redirect link"})
    special_characters = "!@#$%^&*()-+?_=,<>/"
    if any(c in special_characters for c in original_link):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Bad link name"})
    try:
        r = await redis.Redis(host='localhost', port=6379, db=1)
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://172.30.1.26:27017")
    except Exception:
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    db = mongo_client["linkl"]
    collection = db["link"]
    if original_link == "null":
        while True:
            original_link = "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(9))
            if await collection.find_one({"link": original_link}) is None:
                break
    elif await collection.find_one({"link": original_link}) is not None:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Link already exists","link": original_link})
    mongo_payload = {
        "link": original_link,
        "redirect_link": link.redirect_link,
        "created_at": datetime.datetime.now(),
        "using": 0
    }
    try:
        await collection.insert_one(mongo_payload)
        await r.set(original_link, link.redirect_link)
    except Exception:
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    return JSONResponse(status_code=201, content={"link": original_link,
                                                  "redirect_link": link.redirect_link,
                                                  "created_at": str(datetime.datetime.now())
                                                  })
