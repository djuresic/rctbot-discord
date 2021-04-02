FROM python:3.9-slim-buster

RUN apt-get update && apt-get install -y libjpeg-turbo-progs libjpeg62-turbo-dev liblcms2-dev libwebp-dev zlib1g-dev wget

COPY requirements.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd --create-home rctbot
WORKDIR /home/rctbot
USER rctbot

COPY . .

CMD ["python", "./bot.py"]

HEALTHCHECK  --interval=150s --timeout=3s --start-period=15s \
    CMD wget --no-verbose --tries=1 --spider  http://0.0.0.0:8080/ || exit 1
