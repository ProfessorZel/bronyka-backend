import os
import re
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException, Depends, APIRouter
from fastapi.responses import FileResponse

from app.core.user import current_superuser

router = APIRouter()
# Настройки
UPLOAD_DIR = Path("data/uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
FILENAME_PREFIX_LENGTH = 8  # Длина префикса в символах


def clean_filename(filename: str) -> str:
    """Очищает имя файла от опасных символов и нормализует"""
    # Удаляем небезопасные символы
    cleaned = re.sub(r'[^\w\s\-\.]', '', filename)
    # Заменяем пробелы на подчеркивания
    cleaned = cleaned.replace(' ', '_')
    # Убираем множественные подчеркивания
    cleaned = re.sub(r'_{2,}', '_', cleaned)
    return cleaned.strip('_')


def generate_safe_filename(original_filename: str) -> str:
    """Генерирует безопасное имя файла с префиксом"""
    # Очищаем оригинальное имя
    safe_name = clean_filename(original_filename)

    # Извлекаем расширение
    ext = ''
    if '.' in safe_name:
        name_part, ext = safe_name.rsplit('.', 1)
        ext = f".{ext.lower()}"
        safe_name = name_part

    # Генерируем случайный префикс
    prefix = uuid.uuid4().hex[:FILENAME_PREFIX_LENGTH]

    # Формируем итоговое имя
    return f"{prefix}_{safe_name}{ext}"


def is_safe_path(base_path: Path, target_path: Path) -> bool:
    """Проверяет, находится ли целевой путь внутри базового пути"""
    try:
        base = base_path.resolve()
        target = target_path.resolve()
        return base in target.parents or base == target
    except Exception:
        return False


@router.post("/",
             dependencies=[Depends(current_superuser)],
             summary="Загрузка файла для отображения в интерфейсе"
             )
async def upload_file(file: UploadFile):
    try:
        # Проверяем расширение файла
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Генерируем безопасное имя
        safe_filename = generate_safe_filename(file.filename)
        file_path = UPLOAD_DIR / safe_filename

        # Проверяем безопасность пути
        if not is_safe_path(UPLOAD_DIR, file_path):
            raise HTTPException(
                status_code=400,
                detail="Недопустимый путь к файлу"
            )

        # Сохраняем файл
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Возвращаем только сгенерированное имя файла
        return {"filename": safe_filename}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )


@router.get("/{filename}",
            #dependencies=[Depends(current_user)],
            summary="Скачивание файла по имени"
            )
async def download_file(filename: str):
    try:
        # Проверяем расширение файла
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Неподдерживаемый тип файла"
            )

        file_path = UPLOAD_DIR / filename

        # Проверяем безопасность пути
        if not is_safe_path(UPLOAD_DIR, file_path):
            raise HTTPException(
                status_code=400,
                detail="Недопустимый путь к файлу"
            )

        # Проверяем существование файла
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Файл не найден"
            )

        # Возвращаем файл с сохраненным именем
        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при скачивании файла: {str(e)}"
        )