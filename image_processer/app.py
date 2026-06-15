from fastapi import FastAPI, UploadFile, BackgroundTasks, Request, Response
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime, timedelta, timezone
import uuid

from input import (
    images_path,
    COLORS_CHARTS,
    image_out_path,
    max_out_anonymous_size,
    max_out_authenticated_size,
    max_out_premium_size,
    ANONYMOUS_USER,
    USER,
    PREMIUM_USER,
    allowed_images_type
)
from db import get_file_record, add_file_record_with_token, touch_file_record, delete_file_and_record
from typing import Optional
from .file_utils import safe_write_file


def can_delete_file(rec: dict, request: Request, access_token: Optional[str] = None) -> bool:
    """Check if user has permission to delete file."""
    # anonymous files: only if access_token matches
    if rec.get('is_anonymous'):
        return access_token and rec.get('access_token') == access_token
    # owned files: only if owner matches current user
    owner_id = rec.get('owner_id')
    user = getattr(request.state, 'user', None)
    if owner_id is None:
        # public file (shouldn't happen but allow owner)
        return user is not None
    return user and user.get('id') == owner_id
from typing import Optional
from .color_chart import ColorChart
from .image_processor import ImageProcessor

image_process = FastAPI()

# TTL for anonymous files (seconds)
ANONYMOUS_TTL_SECONDS = 60 * 60  # 1 hour


@image_process.post("/upload_image/")
async def upload_image(request: Request, file: UploadFile, background_tasks: BackgroundTasks):
    # Validate content type
    if file.content_type not in allowed_images_type:
        return Response(status_code=415, content=f"Unsupported media type: {file.content_type}")

    content = await file.read()
    # ensure unique filename and sanitize input filename
    target = Path(images_path)
    target.mkdir(parents=True, exist_ok=True)
    # avoid path traversal by taking only the name
    original_name = Path(file.filename).name
    stem = Path(original_name).stem
    suffix = Path(original_name).suffix
    filename = original_name
    dest = target / filename
    i = 1
    # avoid overwriting existing files
    while dest.exists():
        filename = f"{stem}_{i}{suffix}"
        dest = target / filename
        i += 1

    # write atomically: write to a temp file then rename
    try:
        safe_write_file(dest, content)
    except Exception:
        # fallback to direct write
        with open(dest, "wb") as f:
            f.write(content)
        try:
            import os
            os.chmod(dest, 0o640)
        except Exception:
            pass

    # record file in DB
    user = getattr(request.state, 'user', None)
    if user:
        owner_id = user.get('id')
        is_anonymous = False
        expires_at = None
        access_token = None
        try:
            add_file_record_with_token(filename, owner_id, is_anonymous, expires_at, access_token)
        except Exception:
            pass
        return {
            "filename": filename,
            "content_type": file.content_type,
            "size": len(content),
            "anonymous": is_anonymous,
            "expires_at": None
        }

    # anonymous user: generate an access token and an expiry
    owner_id = None
    is_anonymous = True
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=ANONYMOUS_TTL_SECONDS)
    access_token = uuid.uuid4().hex
    try:
        add_file_record_with_token(filename, owner_id, is_anonymous, expires_at, access_token)
    except Exception:
        pass

    return {
        "filename": filename,
        "content_type": file.content_type,
        "size": len(content),
        "anonymous": is_anonymous,
        "expires_at": expires_at.isoformat(),
        "access_token": access_token
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
async def get_out_image(request: Request, filename: str, access_token: Optional[str] = None):
    # Check DB to ensure access control
    rec = get_file_record(filename)
    if not rec:
        path = Path(image_out_path) / filename
        if not path.exists():
            return {"status": "image does not exists yet, try again later"}
        # if no db record assume public
        return FileResponse(path)

    # if anonymous, do not allow retrieval from others - only owner (none) -> so deny
    if rec.get('is_anonymous'):
        # allow retrieval only if access_token matches
        if access_token and rec.get('access_token') == access_token:
            # reset expiry
            try:
                touch_file_record(filename, ANONYMOUS_TTL_SECONDS)
            except Exception:
                pass
            path = Path(image_out_path) / filename
            if not path.exists():
                return {"status": "image does not exists yet, try again later"}
            return FileResponse(path)
        return Response(status_code=404, content="Not found")

    # if file has owner, allow
    owner_id = rec.get('owner_id')
    user = getattr(request.state, 'user', None)
    if owner_id is None:
        # public file
        path = Path(image_out_path) / filename
        if not path.exists():
            return {"status": "image does not exists yet, try again later"}
        return FileResponse(path)

    if user and user.get('id') == owner_id:
        path = Path(image_out_path) / filename
        if not path.exists():
            return {"status": "image does not exists yet, try again later"}
        return FileResponse(path)

    return Response(status_code=403, content="Forbidden")


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


@image_process.delete("/delete_file/{filename}")
async def delete_file(request: Request, filename: str, access_token: Optional[str] = None):
    """Delete uploaded file (anonymous or owned)."""
    rec = get_file_record(filename)
    if not rec:
        return Response(status_code=404, content="File not found")

    # check permissions
    if not can_delete_file(rec, request, access_token):
        return Response(status_code=403, content="Permission denied")

    # delete file and record
    try:
        delete_file_and_record(filename, images_path, image_out_path)
    except Exception as e:
        return Response(status_code=500, content=f"Error deleting file: {str(e)}")

    return {"success": True, "message": f"File {filename} deleted", "filename": filename}


@image_process.get("/get_chart/{key}")
async def get_chart(key: str):
    chart = ColorChart(key)
    chart.load_chart()
    return chart.chart
