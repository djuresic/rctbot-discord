FROM python:3.9-slim-buster

COPY requirements.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd --create-home rctbot
WORKDIR /home/rctbot
USER rctbot

COPY . .

CMD [ "python", "./bot.py" ]