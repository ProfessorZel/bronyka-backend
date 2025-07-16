# app/api/endpoints/googlesheets.py

from fastapi import APIRouter, Depends, HTTPException
from gspread import WorksheetNotFound
from starlette.responses import Response

from app.core.user import current_superuser
from app.schemas.googlesheets import SpreadsheetInfo, ValidateSpreadsheet, AccessRequestMeta, ConfigSpreadsheet
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
    response_model=None,
    dependencies=[Depends(current_superuser)],
    summary="Запрос на добавление новой таблицы в работу",
    response_description="Успешная проверка доступа и добавление таблицы",
)
async def add_sheet_config(
    req: ConfigSpreadsheet,
    editor: GoogleSheetsEditor = Depends(get_google_editor),
):
    try:
        spreadsheet = editor.get_editable_spreadsheet(req.url)
        worksheet = spreadsheet.worksheet(req.sheet)
        return Response(content="Создано успешно")
    except WorksheetNotFound as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Не существует такого листа",
                "message": str(e),
            }
        )
    except GoogleSheetsAccessError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Доступ к таблице не получен",
                "message": str(e),
                "service_account": editor.get_service_account_email()
            }
        )
