FROM debian:bookworm-slim

WORKDIR /app

RUN apt update && apt install -y \
    ffmpeg \
    curl \
    ca-certificates \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --frozen
ENV PATH="/app/.venv/bin:$PATH"

#only necessary in a prod environment
#COPY . /app

EXPOSE 8000
CMD ["python", "src/main.py"]