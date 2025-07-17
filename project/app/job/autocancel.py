import asyncio
import logging
from datetime import timedelta, datetime
from typing import Sequence

from fastapi_utilities import repeat_at

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.crud.activity import activity_crud
from app.crud.audit import audit_crud
from app.crud.reservation import reservation_crud
from app.models import Reservation
from app.schemas.audit import AuditCreate
from app.schemas.reservation import ReservationRoomDBUpdateInternal


@repeat_at(cron="*/3 * * * *")
def run_autocancel():
    if not settings.cron_autocancel_enabled:
        logging.info("Cron to cancel unused reservations is DISABLED")
        return

    session = AsyncSessionLocal()
    try:
        logging.info("Starting cron to cancel unused reservations")
        current_reservations: Sequence[Reservation] = asyncio.run(reservation_crud.get_reservations_current(session=session))
        for current_reservation in current_reservations:
            try:
                if current_reservation.confirmed_activity:
                    logging.info(f"Reservation {current_reservation.id} has confirmed activity, skipping...")
                    continue
                if current_reservation.to_reserve < datetime.now():
                    logging.info(f"Skipping processing reservation {current_reservation.id} is already finished")
                    continue
                if current_reservation.from_reserve > datetime.now() - timedelta(seconds=settings.autocancel_after_no_activity_after_start_seconds):
                    logging.info(f"Skipping processing reservation {current_reservation.id} as time from start is not enough to trigger autocancel")
                    continue

                is_active = asyncio.run(activity_crud.confirm_activty(user_id=current_reservation.user_id,
                                                                      meetingroom_id=current_reservation.meetingroom_id,
                                                                      lookback_interval=timedelta(days=1),
                                                                      session=session))
                if not is_active:
                    logging.info(f"Reservation {current_reservation} has no activity detected, cancelling...")
                    reservation = asyncio.run(reservation_crud.remove(db_obj=current_reservation, session=session))
                    event = AuditCreate(
                        description="Отмена резервирования по основаниям autocancel: {0}".format(
                            reservation
                        ),
                        user_id=None,
                    )
                    asyncio.run(audit_crud.create(event, session))
                else:
                    reservation = reservation_crud.update(db_obj=current_reservation, obj_in=ReservationRoomDBUpdateInternal(
                        confirmed_activity = True
                    ), session=session)
                    event = AuditCreate(
                        description="Обновлено резервирование, активность подтверждена: {0}".format(
                            reservation
                        ),
                        user_id=None,
                    )
                    asyncio.run(audit_crud.create(event, session))
                    logging.info(f"Reservation {current_reservation} has activity detected, skipping...")
            except Exception as e:
                logging.error(f"error in reservation {current_reservation} canceling {e}")
        logging.info("Finished cron to cancel unused reservations")
    except Exception as e:
        logging.error(f"error in cron {e}")
    finally:
        asyncio.run(session.close())
