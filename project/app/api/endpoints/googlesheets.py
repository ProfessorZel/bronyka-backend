# app/api/endpoints/googlesheets.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from gspread import WorksheetNotFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.validators import check_timesheet_setting_exists
from app.core.db import get_async_session
from app.core.user import current_superuser
from app.crud.timesheet_settings import timesheet_setting_crud
from app.models import TimesheetSetting
from app.schemas.googlesheets import ValidateSpreadsheetResult, ValidateSpreadsheet, AccessRequestMeta, ConfigSpreadsheet, \
    ConfigSpreadsheetDB
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
        instructions="Необходимо предоставить доступ к этому сервис аккаунту к книге, с уровнем доступа редактор."
    )

@router.post(
    "/validate",
    response_model=ValidateSpreadsheetResult,
    dependencies=[Depends(current_superuser)],
    summary="Запрос на проверку доступа к файлу",
    response_description="Успешная проверка доступа и данные об файле",
)
async def validate_access_by_url(
    req: ValidateSpreadsheet,
    editor: GoogleSheetsEditor = Depends(get_google_editor)
):
    try:
        spreadsheet = editor.get_editable_spreadsheet(req.url)
        return ValidateSpreadsheetResult(
            url=req.url,
            title=spreadsheet.title,
            sheets=[sheet.title for sheet in spreadsheet.worksheets()]
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


@router.post(
    "/",
    response_model=ConfigSpreadsheetDB,
    dependencies=[Depends(current_superuser)],
    summary="Запрос на добавление новой таблицы в работу",
    response_description="Успешная проверка доступа и добавление таблицы",
)
async def add_sheet_config(
    req: ConfigSpreadsheet,
    editor: GoogleSheetsEditor = Depends(get_google_editor),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        spreadsheet = editor.get_editable_spreadsheet(req.url)
        worksheet = spreadsheet.worksheet(req.sheet)
        try:
            result = await timesheet_setting_crud.create(
                TimesheetSetting(
                    spreadsheet_url=spreadsheet.url,
                    worksheet=worksheet.title,
                    with_service_account=editor.get_service_account_email()
                ),
                session=session,
            )
            return ConfigSpreadsheetDB(
                id=result.id,
                spreadsheet_url=result.spreadsheet_url,
                worksheet=result.worksheet,
                service_account_email=result.with_service_account,
            )
        except IntegrityError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Такая пара книги и листа уже существует",
                    "message": "Такая пара книги и листа уже существует " + str(e),
                }
            )
    except WorksheetNotFound as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Не существует такого листа",
                "message": "Не существует такого листа " + str(e),
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

@router.get(
"/",
    response_model=List[ConfigSpreadsheetDB],
    dependencies=[Depends(current_superuser)],
    summary="Список сконфигурированных листов",
)
async def get_list(
    session: AsyncSession = Depends(get_async_session)
):
    configs = await timesheet_setting_crud.get_multi(session=session)
    con = []
    for config in configs:
        con.append(ConfigSpreadsheetDB(
            id=config.id,
            spreadsheet_url=config.spreadsheet_url,
            worksheet=config.worksheet,
            service_account_email=config.with_service_account,
        ))
    return con


@router.delete(
"/{config_id}",
    response_model=ConfigSpreadsheetDB,
    dependencies=[Depends(current_superuser)],
    summary="Удаляет конфиг",
)
async def get_list(
    config_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    config = await check_timesheet_setting_exists(timesheet_settings_id=config_id, session=session)
    config = await timesheet_setting_crud.remove(db_obj=config, session=session)
    return ConfigSpreadsheetDB(
        id=config.id,
        spreadsheet_url=config.spreadsheet_url,
        worksheet=config.worksheet,
        service_account_email=config.with_service_account,
    )