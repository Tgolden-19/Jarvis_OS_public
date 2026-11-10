FROM --platform=linux/arm64 python:3.10-slim

ENV TZ=America/New_York

WORKDIR /JARVIS_BMOS


RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libsndfile1 \
    libffi-dev \
    ffmpeg \
    git \
    pipx \
    curl \
    python-lgpio \
    build-essential \
    libatlas-base-dev \
    sqlite3 \
    portaudio19-dev \
    python3-pyaudio \
    libportaudio2 \
    libportaudiocpp0 \
    libasound-dev \
    libsndfile1-dev \
    && apt-get clean

RUN pipx ensurepath \
    && pipx install poetry

RUN poetry run pip install faster-whisper pyaudio vosk

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .

CMD ["python", "main.py"]