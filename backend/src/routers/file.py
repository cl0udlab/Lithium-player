from fastapi import APIRouter, UploadFile

file_router = APIRouter()

@file_router.post("/upload")
async def upload_file(file: UploadFile):
    ...


@file_router.get("/files")
async def get_files():
    ...
