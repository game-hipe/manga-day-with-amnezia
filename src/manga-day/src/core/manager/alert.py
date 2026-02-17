import asyncio

from loguru import logger

from ..abstract.alert import BaseAlert, LEVEL


class AlertManager:
    def __init__(self, *alert: BaseAlert):
        self._alerts: list[BaseAlert] = []
        self._alerts.extend(alert)

    def add_alert(self, alert: BaseAlert) -> None:
        """Добавить уведомление."""
        if not isinstance(alert, BaseAlert):
            logger.warning(
                "Не удалось добавить обработчик так-как он не наследуется от BaseAlert"
            )
            raise TypeError("Обработчик уведомлений должен быть наследником BaseAlert")

        if alert not in self._alerts:
            self._alerts.append(alert)
            logger.debug(
                f"Добавлен новый обработчик уведомлений: {alert.__class__.__name__}"
            )
        else:
            logger.debug(
                f"Обработчик уведомлений {alert.__class__.__name__} уже существует"
            )

    async def alert(self, message: str, level: LEVEL):
        """Уведомить всех о событии."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            logger.info("Невозможно отправить Alert, even-loop закрыт")
            return

        async def _send(message: str, alert_engine: BaseAlert) -> None:
            try:
                result = await alert_engine.alert(message, level)
                if not result:
                    self._alerts.remove(alert_engine)
                    logger.debug(
                        f"Система уведомлений {type(alert_engine).__name__} было удалено"
                    )

            except Exception as e:
                self._alerts.remove(alert_engine)
                logger.error(
                    f"Ошибка при отправке уведомления {alert_engine.__class__.__name__}: {e}"
                )

        await asyncio.gather(*[_send(message, alert) for alert in self._alerts])

    def remove_alert(self, alert: BaseAlert) -> None:
        """Удалить уведомление."""
        if alert in self._alerts:
            self._alerts.remove(alert)
            logger.debug(
                f"Обработчик уведомлений {alert.__class__.__name__} был удален"
            )
        else:
            logger.warning(
                f"Обработчик уведомлений {alert.__class__.__name__} не найден"
            )

    @property
    def alerts(self):
        """Список уведомлений."""
        return self._alerts.copy()
