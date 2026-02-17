import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from loguru import logger

from src.core.manager.alert import AlertManager
from src.core.abstract.alert import BaseAlert, LEVEL


class MockAlert(BaseAlert):
    """Мок-класс для тестирования уведомлений."""

    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed
        self.last_message: str | None = None
        self.last_level: LEVEL | None = None

    async def alert(self, message: str, level: LEVEL) -> bool:
        self.last_message = message
        self.last_level = level
        return self.should_succeed


class TestAlertManager:
    @pytest.fixture
    def alert_manager(self):
        """Создание экземпляра AlertManager."""
        return AlertManager()

    @pytest.fixture
    def successful_alert(self):
        """Мок успешного уведомления."""
        return MockAlert(should_succeed=True)

    @pytest.fixture
    def failing_alert(self):
        """Мок неудачного уведомления."""
        return MockAlert(should_succeed=False)

    def test_add_alert_valid(self, alert_manager, successful_alert):
        """Тест добавления валидного обработчика уведомлений."""
        alert_manager.add_alert(successful_alert)
        assert successful_alert in alert_manager.alerts
        assert len(alert_manager.alerts) == 1

    def test_add_alert_invalid_type(self, alert_manager):
        """Тест добавления невалидного обработчика (не наследника BaseAlert)."""
        with pytest.raises(TypeError):
            alert_manager.add_alert("not_an_alert")  # type: ignore

    def test_add_duplicate_alert(self, alert_manager, successful_alert, caplog):
        """Тест повторного добавления того же обработчика."""
        alert_manager.add_alert(successful_alert)
        with caplog.at_level(logger.level("DEBUG").name):
            alert_manager.add_alert(successful_alert)

        assert alert_manager.alerts.count(successful_alert) == 1

    def test_remove_alert_existing(self, alert_manager, successful_alert, caplog):
        """Тест удаления существующего обработчика."""
        alert_manager.add_alert(successful_alert)
        with caplog.at_level(logger.level("DEBUG").name):
            alert_manager.remove_alert(successful_alert)

        assert successful_alert not in alert_manager.alerts

    def test_remove_alert_nonexistent(self, alert_manager, failing_alert, caplog):
        """Тест удаления несуществующего обработчика."""
        with caplog.at_level(logger.level("WARNING").name):
            alert_manager.remove_alert(failing_alert)

    @pytest.mark.asyncio
    async def test_alert_sends_to_all_handlers(self, alert_manager, successful_alert):
        """Тест отправки уведомления всем подключённым обработчикам."""
        alert_manager.add_alert(successful_alert)
        await alert_manager.alert("Test message", "info")

        assert successful_alert.last_message == "Test message"
        assert successful_alert.last_level == "info"

    @pytest.mark.asyncio
    async def test_failing_alert_is_removed(self, alert_manager, failing_alert, caplog):
        """Тест, что провалившийся обработчик удаляется из менеджера."""
        alert_manager.add_alert(failing_alert)
        with caplog.at_level(logger.level("DEBUG").name):
            await alert_manager.alert("Failing message", "error")

        assert failing_alert not in alert_manager.alerts

    @pytest.mark.asyncio
    async def test_exception_in_alert_removes_handler(self, alert_manager, caplog):
        """Тест, что исключение в обработчике приводит к его удалению."""

        class ExceptionAlert(BaseAlert):
            async def alert(self, message: str, level: LEVEL) -> bool:
                raise RuntimeError("Simulated failure")

        exception_alert = ExceptionAlert()
        alert_manager.add_alert(exception_alert)

        with caplog.at_level(logger.level("ERROR").name):
            await alert_manager.alert("Exception message", "critical")

        assert exception_alert not in alert_manager.alerts

    @pytest.mark.asyncio
    async def test_alert_with_multiple_handlers(
        self, alert_manager, successful_alert, failing_alert
    ):
        """Тест отправки уведомления нескольким обработчикам (один из которых падает)."""
        alert_manager.add_alert(successful_alert)
        alert_manager.add_alert(failing_alert)

        await alert_manager.alert("Mixed message", "warning")

        assert successful_alert.last_message == "Mixed message"
        assert failing_alert not in alert_manager.alerts
        assert len(alert_manager.alerts) == 1

    @pytest.mark.asyncio
    async def test_alert_empty_handlers(self, alert_manager, caplog):
        """Тест отправки уведомления при отсутствии обработчиков."""
        with caplog.at_level(logger.level("DEBUG").name):
            await alert_manager.alert("No handlers", "info")

        # Никаких ошибок, просто ничего не происходит
        assert "Ошибка при отправке" not in caplog.text

    def test_alert_property_returns_copy(self, alert_manager, successful_alert):
        """Тест, что свойство alerts возвращает копию списка."""
        alert_manager.add_alert(successful_alert)
        alerts_ref = alert_manager.alerts
        assert alerts_ref == alert_manager.alerts
        assert alerts_ref is not alert_manager._alerts  # Это должна быть копия
