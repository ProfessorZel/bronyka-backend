# app/api/endpoints/googlesheets.py

import gspread
from fastapi import APIRouter, Depends, HTTPException

from app.core.user import current_superuser
from app.schemas.googlesheets import SpreadsheetInfo, ValidateSpreadsheet, AccessRequestMeta
from app.timecard.filltimecard import WorkScheduleFiller
from app.timecard.google_spreadsheet import get_google_editor, GoogleSheetsEditor, \
    GoogleSheetsAccessError

router = APIRouter()


@router.get(
    "/meta",
    response_model=AccessRequestMeta,
    dependencies=[Depends(current_superuser)],
    summary="Информация с инструкцией по получению доступа",
)
async def get_meta(
    editor: GoogleSheetsEditor = Depends(get_google_editor)
):
    return AccessRequestMeta(
        service_account_email=editor.get_service_account_email(),
    )

@router.post(
    "/validate",
    response_model=SpreadsheetInfo,
    dependencies=[Depends(current_superuser)],
    summary="Запрос на проверку доступа к файлу",
    response_description="Успешная проверка доступа и данные об файле",
)
async def validate_access_by_url(
    req: ValidateSpreadsheet,
    editor: GoogleSheetsEditor = Depends(get_google_editor)
):
    try:
        editor.get_editable_spreadsheet(req.url)
    except GoogleSheetsAccessError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Доступ к таблице не получен",
                "message": str(e),
                "service_account": editor.get_service_account_email()
            }
        )


@router.post(
    "/config",
    response_model=SpreadsheetInfo,
    dependencies=[Depends(current_superuser)],
    summary="Запрос на добавление новой таблицы в работу",
    response_description="Успешная проверка доступа и добавление таблицы",
)
async def add_sheet_config(
    editor: GoogleSheetsEditor = Depends(get_google_editor),
):
    try:
        spreadsheet = editor.get_editable_spreadsheet("https://docs.google.com/spreadsheets/d/1ZcwFEJkBQPV9XLxn-VRu6lx4fwu6gITxJVOVta3vXHw/edit?gid=1035045900#gid=1035045900")
        worksheet = spreadsheet.worksheet(spreadsheet.worksheets()[0].title)
        filler = WorkScheduleFiller(worksheet)

        filler.fill_schedule("Измайлова Диана Дмитриевна", "21.07.25", "01:00", "12:00")

        return None
    except GoogleSheetsAccessError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Доступ к таблице не получен",
                "message": str(e),
                "service_account": editor.get_service_account_email()
            }
        )
