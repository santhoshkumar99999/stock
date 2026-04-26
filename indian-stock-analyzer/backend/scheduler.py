from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler


def start_scheduler(refresh_callback) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_callback, "interval", minutes=1, id="refresh_all_data")
    scheduler.start()
    return scheduler
