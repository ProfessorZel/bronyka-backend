# app/api/endpoints/googlesheets.py

import gspread
from fastapi import APIRouter, Depends

from app.core.user import current_superuser
from app.schemas.googlesheets import SpreadsheetInfo
from timecard.google_spreadsheet import get_editable_spreadsheet

router = APIRouter()


@router.post(
    "/",
    response_model=SpreadsheetInfo,
    dependencies=[Depends(current_superuser)],
    summary="Запрос на добавление новой таблицы в работу",
    response_description="Успешная проверка доступа и добавление таблицы",
)
async def add_sheet(
    url: str,
    spreadsheet: gspread.Spreadsheet = Depends(get_editable_spreadsheet),
):
    return SpreadsheetInfo(
        url=url,
        title=spreadsheet.title,
        sheets= [ws.title for ws in spreadsheet.worksheets()]
    )