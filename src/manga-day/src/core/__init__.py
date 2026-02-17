"""Ядро системы, хранит абстрактные классы и так-же менеджеры и схемы, модели"""

from ._config import config
from ._cron import SpiderScheduler

__all__ = ["config", "SpiderScheduler"]
