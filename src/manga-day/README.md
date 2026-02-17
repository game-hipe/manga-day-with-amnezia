![logo](https://raw.githubusercontent.com/game-hipe/manga-day/refs/heads/main/src/frontend/user/static/images/logo.png)

# Manga-Day Новая манга в 2 клика!
В чём суть проекта? У меня есть много сайтов, где манга выходит не каждый день, но следит за ними нужно, поэтому я подумал почему-бы не просто создать пауков, и ТГ админку? Вот на этом и решили!

## На будущее!
Стоит улучшить API, для полноценности проекта, так-же улучшить Бота на стороне пользователя!

## Как запустить проект?
```bash
git clone https://github.com/game-hipe/manga-day.git
cd manga-day

cp env.example .env
cp config-example.yaml config.yaml

nano config.yaml # Если имеются прокси вставтье данные, при отсутствии таковых, удалите поле proxy.
nano .env

docker-compose build --no-cache
docker-compose up -d
```

## 2 Способ через прямой python (python3.14.X+)
```bash
git clone https://github.com/game-hipe/manga-day.git
cd manga-day
cp config-example.yaml config.yaml

nano config.yaml # Если имеются прокси вставтье данные, при отсутствии таковых, удалите поле proxy.
nano .env
pip install -r requirements.txt
python main.py
```

> [!WARNING]
> Донор данных hitomi, была добавлена защита Cloudflare, поэтому на данный момента паук "hitomi" не доступен.

> [!WARNING]
> Проект является просто демонстрацие своих сил в BackEnd, и в ТГ ботах, поэтому не бейте тапком
