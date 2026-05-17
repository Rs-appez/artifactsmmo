FROM python:3.14-alpine

ENV TZ="Europe/Brussels"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --no-group cli --no-install-project

COPY . /app

CMD ["uv", "run", "--no-sync", "main.py"]
