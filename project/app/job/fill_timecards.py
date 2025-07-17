import asyncio
import logging
from datetime import datetime, timedelta

from fastapi_utilities import repeat_at
from sqlalchemy import Sequence

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.crud.reservation import reservation_crud
from app.crud.timesheet_settings import timesheet_setting_crud
from app.crud.user import user_crud
from app.models import TimesheetSetting, User
from app.timecard.header_parser import UserHeader
from app.timecard.worksheet_filler import WorkScheduleFiller
from app.timecard.google_spreadsheet import configured_get_google_sheets_editor


@repeat_at(cron="15 * * * *")
def run_fill_timecards():
    if not settings.cron_timesheet_enabled:
        logging.info("Cron to fill timecards is DISABLED")
        return

    editor = configured_get_google_sheets_editor()
    session = AsyncSessionLocal()
    try:
        logging.info("Starting cron to fill timecards")
        configured_timesheets: list[TimesheetSetting] = asyncio.run(timesheet_setting_crud.get_multi(session))

        today_start = datetime.now().date()
        today_end = today_start + timedelta(days=1)
        date_str = today_start.strftime("%d.%m.%y")

        for configured_timesheet in configured_timesheets:
            if editor.get_service_account_email() != configured_timesheet.with_service_account:
                logging.warn(f"Skipping {configured_timesheet} as service account email is {configured_timesheet.service_account_email} doesn't match current active")
                continue
            try:
                spreadsheet = editor.get_editable_spreadsheet(configured_timesheet.spreadsheet_url)
                worksheet = spreadsheet.worksheet(configured_timesheet.worksheet)
                filler = WorkScheduleFiller(worksheet)

                # Поиск строки с датой
                date_row = filler.find_date_row(date_str)
                users: dict[UserHeader, int] = filler.users()
                seen_logins: set[str] = set()
                for user_header, user_col in users.items():
                    user = None
                    if user_header.login is None:
                        db_users: Sequence[User] = asyncio.run(user_crud.get_user_by_fio(
                                user_header.fio,
                                session))
                        logging.info(f"Found {len(db_users)} candidate users for {user_header}")
                        for candidate_user in db_users:
                            if candidate_user.email not in seen_logins:
                                user = candidate_user
                                break
                    else:
                        user = asyncio.run(user_crud.get_user_by_email(user_header.login))

                    if user is None:
                        logging.warn(
                            f"Skipping {user_header.fio} ({user_header.login}) as user not found in database, but present in spreadsheet")
                        continue

                    seen_logins.add(user.email)

                    if user_header.login is None:
                        logging.info(f"Processing user {user.fio} at col {user_col}, setting user login to {user.email}")
                        filler.update_header(user_col, user.fio, user.email)

                    logging.info(f"Processing user {user.fio}")
                    try:
                        interval: tuple[
                            datetime | None, datetime | None] = asyncio.run(reservation_crud.get_reservations_interval_for_user_today(
                            user_id=user.id,
                            from_time=today_start,
                            to_time=today_end,
                            session=session))
                        if interval[0] is None:
                            filler.fill_schedule(user_col,
                                                 date_row,
                                                 "-", "-")
                        else:
                            from_time_str = interval[0].strftime("%H:%M")
                            to_time_str = interval[1].strftime("%H:%M")
                            logging.info(f"for user {user.fio} at {from_time_str} to {to_time_str}")
                            filler.fill_schedule(user_col,
                                                 date_row,
                                                 from_time_str, to_time_str)
                    except Exception as e:
                        logging.error(f"error in cron {e} for user {user.fio}")
            except Exception as e:
                logging.error(f"error in cron {e} for configured_timesheet {configured_timesheet.id}")
        logging.info("Finished cron to fill timecards")
    except Exception as e:
        logging.error(f"error in cron {e}")
    finally:
        asyncio.run(session.close())
