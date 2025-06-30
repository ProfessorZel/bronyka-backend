from fastapi import APIRouter, UploadFile, Depends
from starlette.responses import FileResponse

from app.core.user import current_superuser

router = APIRouter()

@router.post("/",
             dependencies=[Depends(current_superuser)],
             summary="Загрузка файла для отображения в интерфейсе"
             )
def upload_file(file: UploadFile):
  return file

@router.get("/{file_id}")
def download_file():
  return FileResponse(path='data.xlsx', filename='Статистика покупок.xlsx', media_type='multipart/form-data')

