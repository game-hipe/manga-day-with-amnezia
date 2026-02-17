# Dockerfile for amneziawg-go and amneziawg-tools with Tinyproxy

# ---- Builder Stage ----
FROM golang:1.24.4-alpine AS builder
RUN apk add --no-cache git build-base
WORKDIR /src
RUN git clone https://github.com/amnezia-vpn/amneziawg-go.git .
RUN CGO_ENABLED=1 go build -ldflags '-linkmode external -extldflags "-fno-PIC -static"' -v -o amneziawg-go

# ---- Runtime Stage ----
FROM alpine:3.19
ARG AWGTOOLS_RELEASE="1.0.20250903"

# Устанавливаем зависимости + tinyproxy
RUN apk --no-cache add iproute2 iptables bash wget unzip openresolv tinyproxy

# Устанавливаем amneziawg-tools
RUN cd /usr/bin/ && \
    wget https://github.com/amnezia-vpn/amneziawg-tools/releases/download/v${AWGTOOLS_RELEASE}/alpine-3.19-amneziawg-tools.zip && \
    unzip -j alpine-3.19-amneziawg-tools.zip && \
    rm alpine-3.19-amneziawg-tools.zip && \
    chmod +x /usr/bin/awg /usr/bin/awg-quick && \
    ln -s /usr/bin/awg /usr/bin/wg && \
    ln -s /usr/bin/awg-quick /usr/bin/wg-quick && \
    sed -i 's|\[\[ $proto == -4 \]\] && cmd sysctl -q net\.ipv4\.conf\.all\.src_valid_mark=1|[[ $proto == -4 ]] \&\& [[ $(sysctl -n net.ipv4.conf.all.src_valid_mark) != 1 ]] \&\& cmd sysctl -q net.ipv4.conf.all.src_valid_mark=1|' /usr/bin/awg-quick

# Копируем собранный amneziawg-go
COPY --from=builder /src/amneziawg-go /usr/bin/

# Конфигурация Tinyproxy
COPY tinyproxy.conf /etc/tinyproxy/tinyproxy.conf

# Копируем entrypoint
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Создаём папку для WireGuard
RUN mkdir -p /etc/wireguard

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD awg show || exit 1