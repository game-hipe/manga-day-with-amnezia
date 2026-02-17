FROM python:3.14.2-slim-bookworm

WORKDIR /app

RUN mkdir /app/var

RUN mkdir /app/var/pdf

VOLUME [ "/app/var" ]

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD [ "python", "main.py" ]