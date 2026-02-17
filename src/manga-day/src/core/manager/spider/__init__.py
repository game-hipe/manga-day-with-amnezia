"""Менеджер пауков, загрузка пауков, начать работу паука/пауков, и т п."""

from ._load import load_spiders
from ._spider import SpiderManager
from ._starter import SpiderStarter
from ._status import SpiderStatus

__all__ = ["load_spiders", "SpiderManager", "SpiderStarter", "SpiderStatus"]
