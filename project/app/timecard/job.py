import asyncio
import logging
from datetime import datetime, timedelta

from fastapi_utilities import repeat_at

from app.core.db import AsyncSessionLocal
from app.crud.reservation import reservation_crud
from app.crud.user import user_crud
from app.timecard.filltimecard import WorkScheduleFiller
from app.timecard.google_spreadsheet import configured_get_google_sheets_editor


@repeat_at(cron="0 * * * *")
def run_fill_timecards():
    editor = configured_get_google_sheets_editor()
    session = AsyncSessionLocal()
    try:
        logging.warn("Starting cron to fill timecards")


        spreadsheet = editor.get_editable_spreadsheet()
        worksheet = spreadsheet.worksheet()

        filler = WorkScheduleFiller(worksheet)
        users = asyncio.run(user_crud.get_multi(session))

        for user in users:
            logging.warn(f"Processing user {user.fio}")
            today_start = datetime.now().date()
            today_end = today_start + timedelta(days=1)
            date_str = today_start.strftime("%d.%m.%y")

            try:
                interval: tuple[
                    datetime | None, datetime | None] = asyncio.run(reservation_crud.get_reservations_interval_for_user_today(
                    user_id=user.id,
                    from_time=today_start,
                    to_time=today_end,
                    session=session))
                if interval[0] is None:
                    filler.fill_schedule(user.fio,
                                         date_str,
                                         "-", "-")
                else:
                    from_time_str = interval[0].strftime("%H:%M")
                    to_time_str = interval[1].strftime("%H:%M")
                    logging.warn(f"for user {user.fio} at {from_time_str} to {to_time_str}")
                    filler.fill_schedule(user.fio,
                                         date_str,
                                         from_time_str, to_time_str)
            except Exception as e:
                logging.error(f"error in cron {e} for user {user.fio}")
        logging.warn("Finished cron to fill timecards")
    except Exception as e:
        logging.error(f"error in cron {e}")
    finally:
        session.close()
