from fastapi import FastAPI, UploadFile, BackgroundTasks, Request, Response
from fastapi.responses import FileResponse
from pathlib import Path

from input import (
    images_path,
    COLORS_CHARTS,
    image_out_path,
    max_out_anonymous_size,
    max_out_authenticated_size,
    max_out_premium_size,
    ANONYMOUS_USER,
    USER,
    PREMIUM_USER
)
from .color_chart import ColorChart
from .image_processor import ImageProcessor

image_process = FastAPI()


@image_process.post("/upload_image/")
async def upload_image(file: UploadFile):
    content = await file.read()
    file_path = Path(images_path) / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content)
    }


@image_process.get("/replace_color/{file_name}/{chart}")
async def replace_color(
        request: Request,
        file_name: str,
        chart: str,
        background_tasks: BackgroundTasks,
        max_color: int = -1,
        max_pixel: int = -1
        ):
    max_pixel_authorized = {
        ANONYMOUS_USER: max_out_anonymous_size,
        USER: max_out_authenticated_size,
        PREMIUM_USER: max_out_premium_size
    }[getattr(request.state, 'authorisations', ANONYMOUS_USER)]
    if max_pixel > max_pixel_authorized:
        if max_pixel > max_out_premium_size:
            return Response(
                status_code=403,
                content=f"The required output size is not allowed")
        if max_pixel > max_out_authenticated_size:
            return Response(
                status_code=402,
                content=f"The required output size is only allowed for premium user"
            )
        if max_pixel > max_out_anonymous_size:
            return Response(
                status_code=401,
                content=f"The required output size is only allowed for authenticated user,"
                        f" please create an account before continue"
            )
    if max_pixel == -1:
        max_pixel = max_pixel_authorized
    process = ImageProcessor(file_name, chart, max_color, max_pixel)
    process.load()
    background_tasks.add_task(process.replace_color)
    return {
        "process": "started",
        "out_file_name": process.image_out_name
    }


@image_process.get("/get_out_image/{filename}")
async def get_out_image(filename: str):
    path = Path(image_out_path) / filename
    if not path.exists():
        return {
            "status": "image does not exists yet, try again later"
        }
    return FileResponse(path)


@image_process.get("/chart_keys/")
async def get_color_chart_keys():
    keys = COLORS_CHARTS.keys()

    return {
        "chart_keys": list(keys)
    }


@image_process.get("/chart_item_details/{key}")
async def get_chart_item_detail(key: str):
    item = COLORS_CHARTS[key]
    return item


@image_process.get("/get_chart/{key}")
async def get_chart(key: str):
    chart = ColorChart(key)
    chart.load_chart()
    return chart.chart
