from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from image_processer.app import image_process
from middlewares import AuthMiddleware, UploadLimitMiddleware
import db
from input import images_path, image_out_path


class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = 'user'


class UserLogin(BaseModel):
    username: str
    password: str


app = FastAPI()
app.mount("/image_process", image_process)
app.add_middleware(AuthMiddleware)
app.add_middleware(UploadLimitMiddleware)


@app.on_event("startup")
async def startup_event():
    db.init_db()
    # start periodic cleanup task in background
    asyncio.create_task(db.periodic_cleanup(images_path, image_out_path, interval_seconds=60))


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post('/users/register')
async def register_user(user: UserCreate):
    try:
        token = db.create_user(user.username, user.password, user.role or 'user')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"token": token}


@app.post('/users/login')
async def login(user: UserLogin):
    token = db.authenticate_user(user.username, user.password)
    if not token:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    return {"token": token}


