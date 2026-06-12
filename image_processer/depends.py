from functools import wraps
from fastapi import UploadFile, HTTPException

from input import max_anonymous_image_size, max_authenticated_image_size, allowed_images_type


def validate_image(file: UploadFile):
    if not validate_image_type(file):
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed"
                   f"allowed types are {allowed_images_type}")


def validate_image_type(file: UploadFile) -> bool:
    return file.content_type in allowed_images_type
