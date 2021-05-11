# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-slim-buster
RUN apt-get update && apt-get install -y libjpeg-turbo-progs libjpeg62-turbo-dev liblcms2-dev libwebp-dev zlib1g-dev wget

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "bot.py"]

HEALTHCHECK  --interval=150s --timeout=3s --start-period=15s \
    CMD wget --no-verbose --tries=1 --spider  http://0.0.0.0:8080/ || exit 1
