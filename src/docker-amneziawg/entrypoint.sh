#!/bin/bash
set -e

# Default interface name
INTERFACE="wg0"
if [ -n "$1" ]; then
    INTERFACE=$1
fi

CONFIG_FILE="/etc/wireguard/${INTERFACE}.conf"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Функция для graceful shutdown
shutdown() {
    echo "Shutting down WireGuard interface: $INTERFACE"
    awg-quick down "$CONFIG_FILE"
    # Останавливаем tinyproxy, если он ещё работает
    pkill tinyproxy || true
    exit 0
}
trap shutdown SIGTERM SIGINT

# Поднимаем интерфейс
echo "Bringing up WireGuard interface: $INTERFACE"
awg-quick up "$CONFIG_FILE"

# Запускаем Tinyproxy в фоне
echo "Starting Tinyproxy on port 8888..."
tinyproxy -d &   # -d = foreground, но мы пускаем в фон через &

# Ждём сигналов, сохраняя контейнер активным
echo "WireGuard interface is up. Proxy is running. Container will remain running."
while true; do
    sleep 86400 &
    wait $!
done