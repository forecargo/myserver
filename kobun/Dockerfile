# 古文単語 API（kobun-api）。uv で依存を解決し uvicorn で起動する。
FROM python:3.12-slim

# uv（公式配布バイナリ）を取得。
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# 依存だけ先に解決してレイヤキャッシュを効かせる。
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project --no-dev

# アプリ本体（assets はデプロイ時に bind mount でも可）。
COPY . .
RUN uv sync --no-dev

EXPOSE 8006

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
