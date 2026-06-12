from fastapi import FastAPI, File, UploadFile
from image_processer.app import image_process
from middlewares import AuthMiddleware, UploadLimitMiddleware

app = FastAPI()
app.mount("/image_process", image_process)
app.add_middleware(AuthMiddleware)
app.add_middleware(UploadLimitMiddleware)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
