import asyncio
from datetime import datetime

import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .manager.spider import SpiderManager
from . import config


class SpiderScheduler:
    def __init__(
        self,
        manager: SpiderManager,
        start_time: str | None = None,
        zone: str | None = None,
    ):
        self.start_time = start_time or config.update.start_time
        self.zone = zone or config.update.zone
        self.manager = manager

        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(self.zone))

    async def start(self):
        hour, minute, day = self.get_time()
        self.scheduler.add_job(
            self.manager.start_full_parsing,
            CronTrigger(
                hour=hour, minute=minute, day=day, timezone=pytz.timezone(self.zone)
            ),
        )

        self.scheduler.start()

        try:
            await asyncio.Event().wait()

        except (KeyboardInterrupt, SystemExit, asyncio.exceptions.CancelledError):
            self.scheduler.shutdown()

    def get_time(self):
        dt = datetime.strptime(self.start_time, "%I:%M %p EVERY %d DAYS")
        return dt.hour, dt.minute, dt.day
