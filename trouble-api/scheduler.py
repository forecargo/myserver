import os

from apscheduler.schedulers.background import BackgroundScheduler

_scheduler = BackgroundScheduler()


def start_scheduler(collect_fn):
    interval = int(os.getenv("SYNC_INTERVAL_MINUTES", "15"))
    _scheduler.add_job(
        collect_fn,
        trigger="interval",
        minutes=interval,
        id="email_sync",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
