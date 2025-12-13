FROM python:3.12

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

RUN python3 -m venv .venv

# ENV PATH=/app/.venv/bin:$PATH

RUN apt-get update && \
    apt-get install -y \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 && \
    pip install "uv==0.9.5" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY backend pyproject.toml uv.lock requirements.txt pytest.ini ./

RUN uv pip install -r requirements.txt --system

RUN uv pip list
