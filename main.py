from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from image_processer.app import image_process
from middlewares import AuthMiddleware, UploadLimitMiddleware
import db
from input import images_path, image_out_path
from models import UserCreate, UserLogin


app = FastAPI()

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Local development (Vite default)
        "http://localhost:3000",    # Alternative frontend port
        "http://localhost:5173/",   # With trailing slash
    ],
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)

app.mount("/image_process", image_process)
app.add_middleware(AuthMiddleware)
app.add_middleware(UploadLimitMiddleware)


@app.on_event("startup")
async def startup_event():
    db.init_db()
    # ensure images directories exist with safe permissions
    from pathlib import Path
    p_in = Path(images_path)
    p_out = Path(image_out_path)
    p_in.mkdir(parents=True, exist_ok=True, mode=0o750)
    p_out.mkdir(parents=True, exist_ok=True, mode=0o750)
    # enforce permissions (mkdir respects umask), use chmod to ensure desired mode
    import os
    try:
        os.chmod(p_in, 0o750)
    except Exception:
        pass
    try:
        os.chmod(p_out, 0o750)
    except Exception:
        pass

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


