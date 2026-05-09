set -a && source .env && set +a && uv run uvicorn main:app --port 8003 --reload
